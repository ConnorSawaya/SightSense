import AVFoundation
import Speech

/// Push-to-talk speech recognition, on the phone only. Started and stopped by the talk button on the
/// screen, or by the one on the cane (which can also leave it to stop by itself).
@MainActor
final class Voice: ObservableObject {
    @Published private(set) var isListening = false
    @Published private(set) var heard = ""
    @Published private(set) var problem: String?

    private let recognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
    private let engine = AVAudioEngine()
    private var request: SFSpeechAudioBufferRecognitionRequest?
    private var task: SFSpeechRecognitionTask?
    private var finished: ((String) -> Void)?

    /// When asked to stop by itself: this long after the last new word, or this long with nothing heard.
    static let quietAfterWords: TimeInterval = 1.5
    static let quietAtStart: TimeInterval = 8
    static let longest: TimeInterval = 12  // and about this long after it started, even if words keep arriving (other people talking)
    private var stopsItself = false
    private var quietTimer = 0  // counts up; a waiting stop only fires if nothing newer was set
    private var finishing = false  // from stop() until its 0.4 s wait is over: the last command is still being finished
    /// When the phone last ended a command by itself, and how long after that a click still counts as its end.
    private(set) var stoppedItselfAt = Date.distantPast
    static let endClick: TimeInterval = 2
    private var startedAt = Date.distantPast

    func requestPermission() {
        SFSpeechRecognizer.requestAuthorization { _ in }
        AVAudioApplication.requestRecordPermission { _ in }
    }

    /// Starts listening. `done` gets the final text when `stop()` is called (not called if nothing was heard).
    /// With `stopsItself`, it also stops when the speaker has finished; `stop()` still ends it sooner.
    func start(stopsItself: Bool = false, done: @escaping (String) -> Void) {
        guard !isListening, !finishing else { return }  // a new start would be cancelled by the last stop
        problem = nil
        heard = ""
        switch SFSpeechRecognizer.authorizationStatus() {
        case .authorized:
            break
        case .notDetermined:
            requestPermission()  // first use: iOS asks; the next press works
            return
        default:
            problem = "Allow speech recognition in Settings"
            return
        }
        guard let recognizer, recognizer.isAvailable, recognizer.supportsOnDeviceRecognition else {
            problem = "On-device speech recognition is not available"
            return
        }
        let request = SFSpeechAudioBufferRecognitionRequest()
        request.requiresOnDeviceRecognition = true
        request.shouldReportPartialResults = true
        let input = engine.inputNode
        input.removeTap(onBus: 0)
        input.installTap(onBus: 0, bufferSize: 1024, format: input.outputFormat(forBus: 0)) { buffer, _ in
            request.append(buffer)
        }
        engine.prepare()
        do {
            try engine.start()
        } catch {
            input.removeTap(onBus: 0)
            problem = "Microphone failed: \(error.localizedDescription)"
            return
        }
        self.request = request
        finished = done
        isListening = true
        self.stopsItself = stopsItself
        startedAt = Date()
        if stopsItself { stopAfter(Voice.quietAtStart) }
        task = recognizer.recognitionTask(with: request) { [weak self] result, _ in
            guard let text = result?.bestTranscription.formattedString else { return }
            Task { @MainActor in
                guard let self else { return }
                // Each new word puts the stop off again, but not past the longest a command may take.
                if self.isListening, self.stopsItself, text != self.heard,
                   Date().timeIntervalSince(self.startedAt) < Voice.longest { self.stopAfter(Voice.quietAfterWords) }
                self.heard = text
            }
        }
    }

    /// Stops after this long unless a newer wait replaces this one, or `stop()` is called first.
    private func stopAfter(_ seconds: TimeInterval) {
        quietTimer += 1
        let mine = quietTimer
        DispatchQueue.main.asyncAfter(deadline: .now() + seconds) { [weak self] in
            guard let self, self.isListening, self.quietTimer == mine else { return }
            if !self.heard.isEmpty { self.stoppedItselfAt = Date() }  // nothing heard: there is no command for a click to end
            self.stop(wait: self.heard.isEmpty ? 0 : 0.4)  // and nothing to finish, so a click straight after can start again
        }
    }

    func stop(wait: TimeInterval = 0.4) {
        guard isListening else { return }
        isListening = false
        quietTimer += 1
        engine.stop()
        engine.inputNode.removeTap(onBus: 0)
        request?.endAudio()
        let done = finished
        finished = nil
        finishing = true
        // Give the recognizer a moment to finish the last words.
        DispatchQueue.main.asyncAfter(deadline: .now() + wait) { [weak self] in
            guard let self else { return }
            self.finishing = false
            self.task?.cancel()
            self.task = nil
            self.request = nil
            let text = self.heard.trimmingCharacters(in: .whitespacesAndNewlines)
            if !text.isEmpty { done?(text) }
        }
    }
}
