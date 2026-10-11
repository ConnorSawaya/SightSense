import AVFoundation
import Foundation

/// A message from the GX10. Guidance has `state`; a place lookup has `lookup`; the cane's talk button has `listen` (contracts/MESSAGES.md).
struct GX10Message: Decodable, Equatable {
    var seq: Int?
    var state: String?
    var earcon: String?
    var speech: String?
    var lookup: String?
    var listen: Bool?

    static func parse(_ text: String) -> GX10Message? {
        guard let m = try? JSONDecoder().decode(GX10Message.self, from: Data(text.utf8)),
              m.state != nil || m.lookup != nil || m.listen != nil else { return nil }
        return m
    }
}

/// Plays earcons and speaks guidance. Guidance can arrive every frame, so repeats are held back.
@MainActor
final class Speaker {
    static let earconRepeat: TimeInterval = 1.0  // the same earcon at most once a second
    static let speechRepeat: TimeInterval = 2.0  // the GX10 sends a sentence once; this only stops a flickering stop repeating itself

    private let synth = AVSpeechSynthesizer()
    private var players: [String: AVAudioPlayer] = [:]
    private var lastEarcon: (name: String, time: Date)?
    private var lastSpeech: (text: String, time: Date)?

    /// Set while the user is talking to the phone. Speech under way is cut off and nothing new is spoken,
    /// so the phone neither talks over the user nor hears itself. Tones still play, the stop tone among them.
    var quiet = false {
        didSet { if quiet && !oldValue { synth.stopSpeaking(at: .immediate) } }
    }

    init() {
        let session = AVAudioSession.sharedInstance()
        try? session.setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker, .allowBluetoothHFP, .duckOthers])
        try? session.setActive(true)
        for (name, tones) in Self.earcons {
            if let p = try? AVAudioPlayer(data: Self.wav(tones)) {
                p.pan = name == "left" ? -1 : (name == "right" ? 1 : 0)  // in that ear, on headphones
                p.prepareToPlay()
                players[name] = p
            }
        }
    }

    func handle(_ m: GX10Message) {
        let now = Date()
        if let e = m.earcon {
            if lastEarcon?.name != e || now.timeIntervalSince(lastEarcon!.time) >= Self.earconRepeat {
                play(e)
                lastEarcon = (e, now)
            }
        }
        if let s = m.speech, !s.isEmpty, !quiet {  // a sentence dropped while the user talks does not count as said
            if lastSpeech?.text != s || now.timeIntervalSince(lastSpeech!.time) >= Self.speechRepeat {
                say(s, interrupt: m.state == "STOP")
                lastSpeech = (s, now)
            }
        }
    }

    func play(_ earcon: String) {
        guard let p = players[earcon] ?? players["other"] else { return }
        p.currentTime = 0
        p.play()
    }

    func say(_ text: String, interrupt: Bool = false) {
        guard !quiet else { return }  // a spoken stop would go into the open microphone and into the user's command
        if interrupt { synth.stopSpeaking(at: .immediate) }
        let u = AVSpeechUtterance(string: text)
        u.rate = 0.55
        synth.speak(u)
    }

    // MARK: - Tones

    /// (frequency Hz, seconds); frequency 0 is silence.
    static let earcons: [String: [(Double, Double)]] = [
        "stop": [(880, 0.12), (0, 0.05), (880, 0.12)],
        "caution": [(660, 0.10)],
        // direction cues from the GX10 (gx10/planner/cue.py): low for left, high for right, so they differ on the phone's own speaker too
        "left": [(440, 0.10)],
        "right": [(740, 0.10)],
        "unknown": [(220, 0.22)],
        "other": [(520, 0.08)],
    ]

    static func wav(_ tones: [(Double, Double)], rate: Int = 22050) -> Data {
        var samples: [Int16] = []
        for (freq, secs) in tones {
            let n = Int(secs * Double(rate))
            for i in 0..<n {
                let fade = min(1, Double(min(i, n - i)) / (0.005 * Double(rate)))  // 5 ms ramps, no clicks
                let v = freq == 0 ? 0 : sin(2 * .pi * freq * Double(i) / Double(rate)) * fade * 0.6
                samples.append(Int16(v * Double(Int16.max)))
            }
        }
        var d = Data()
        func put<T>(_ v: T) { withUnsafeBytes(of: v) { d.append(contentsOf: $0) } }
        let bytes = samples.count * 2
        d.append(contentsOf: Array("RIFF".utf8)); put(UInt32(36 + bytes).littleEndian)
        d.append(contentsOf: Array("WAVEfmt ".utf8)); put(UInt32(16).littleEndian)
        put(UInt16(1).littleEndian); put(UInt16(1).littleEndian)          // PCM, mono
        put(UInt32(rate).littleEndian); put(UInt32(rate * 2).littleEndian)
        put(UInt16(2).littleEndian); put(UInt16(16).littleEndian)
        d.append(contentsOf: Array("data".utf8)); put(UInt32(bytes).littleEndian)
        samples.forEach { put($0.littleEndian) }
        return d
    }
}
