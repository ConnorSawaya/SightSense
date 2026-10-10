import AVFoundation
import Speech

/// Push-to-talk speech recognition, on the phone only.
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

    func requestPermission() {
        SFSpeechRecognizer.requestAuthorization { _ in }
        AVAudioApplication.requestRecordPermission { _ in }
    }

    /// Starts listening. `done` gets the final text when `stop()` is called (not called if nothing was heard).
    func start(done: @escaping (String) -> Void) {
        guard !isListening else { return }
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
        task = recognizer.recognitionTask(with: request) { [weak self] result, _ in
            guard let text = result?.bestTranscription.formattedString else { return }
            Task { @MainActor in self?.heard = text }
        }
    }

    func stop() {
        guard isListening else { return }
        isListening = false
        engine.stop()
        engine.inputNode.removeTap(onBus: 0)
        request?.endAudio()
        let done = finished
        finished = nil
        // Give the recognizer a moment to finish the last words.
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) { [weak self] in
            guard let self else { return }
            self.task?.cancel()
            self.task = nil
            self.request = nil
            let text = self.heard.trimmingCharacters(in: .whitespacesAndNewlines)
            if !text.isEmpty { done?(text) }
        }
    }
}
