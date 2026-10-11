import ARKit
import SwiftUI

/// Owns the ARKit session and the link to the GX10, and publishes their state for the screen.
@MainActor
final class Capture: ObservableObject {
    let session = ARSession()
    let depthPreview = DepthPreview()

    @Published private(set) var isRunning = false
    @Published private(set) var link = GX10Link.State.idle.rawValue
    @Published private(set) var linkState = GX10Link.State.idle
    @Published private(set) var linkDetail: String?
    @Published private(set) var cameraFormat: String?
    @Published private(set) var stats = FrameSender.Stats()
    @Published private(set) var sendRate = 0.0
    @Published private(set) var lastMessage: String?
    @Published private(set) var guidance: GX10Message?
    @Published var problem: String?

    /// The cane's talk button, passed on by the GX10: true when it goes down, false when it is let go after a hold.
    var onListen: ((Bool) -> Void)?

    private let gx10 = GX10Link()
    private let sender: FrameSender
    private let speaker = Speaker()
    private let location = Location()
    private let places = Places()
    private var wasOpen = false
    private let delegateQueue = DispatchQueue(label: "arkit.frames", qos: .userInitiated)
    private var timer: Timer?
    private var demoTimer: Timer?  // Simulator only
    private var lastTick = (sent: 0, time: CACurrentMediaTime())

    static let framePort = 8765

    init() {
        sender = FrameSender(link: gx10)
        session.delegate = sender
        session.delegateQueue = delegateQueue
        gx10.onState = { [weak self] state, why in
            Task { @MainActor in self?.linkChanged(state, why) }
        }
        gx10.onText = { [weak self] text in
            Task { @MainActor in self?.received(text) }
        }
        location.onUpdate = { [weak sender] extras in sender?.setExtras(extras) }
        sender.onFrame = { [depthPreview] frame in depthPreview.update(frame) }
    }

    /// Sends a spoken or typed command: {"text": "guide me to the apple"}.
    func send(command: String) {
        guard let data = try? JSONSerialization.data(withJSONObject: ["text": command]),
              let json = String(data: data, encoding: .utf8) else { return }
        gx10.sendText(json)
    }

    private func linkChanged(_ state: GX10Link.State, _ why: String?) {
        link = why.map { "\(state.rawValue): \($0)" } ?? state.rawValue
        linkState = state
        linkDetail = why
        guard isRunning else { return }
        if state == .open, !wasOpen {
            wasOpen = true
            speaker.say("Connected")
        } else if state == .retrying, wasOpen {
            wasOpen = false
            guidance = nil
            lastMessage = nil
            speaker.play("stop")
            speaker.say("Connection lost", interrupt: true)
        }
    }

    private func received(_ text: String) {
        lastMessage = text
        guard let m = GX10Message.parse(text) else { return }
        if m.state != nil {
            guidance = m
            speaker.handle(m)
        }
        if let query = m.lookup {
            // "take me to Safeway": find it with Apple Maps and send the walking route back
            places.route(to: query, from: location.coordinate) { [weak self] route in
                self?.gx10.sendText(route)
            }
        }
        if let listen = m.listen {
            if listen { speaker.play("other") }  // the hand is on the cane, not the phone: a tone says the press was taken
            onListen?(listen)
        }
    }

    /// Plays each tone and speaks its name, so the phone's sound can be checked with no GX10.
    func soundCheck() {
        let steps = [("left", "Left"), ("right", "Right"), ("unknown", "Can't see ahead"), ("stop", "Stop. Sound check done.")]
        for (i, step) in steps.enumerated() {
            DispatchQueue.main.asyncAfter(deadline: .now() + Double(i) * 1.8) { [weak self] in
                self?.speaker.play(step.0)
                self?.speaker.say(step.1)
            }
        }
    }

    /// Called when the phone starts or stops listening for a command, from its own talk button or the cane's.
    func talking(_ on: Bool) {
        speaker.quiet = on
    }

    var hasLiDAR: Bool {
        ARWorldTrackingConfiguration.supportsFrameSemantics(.sceneDepth)
    }

    func start(host: String) {
        problem = nil
        #if targetEnvironment(simulator)
        // No camera or LiDAR here: connect without ARKit so the link, guidance and voice can be tried.
        let simulated = true
        #else
        let simulated = false
        guard hasLiDAR else {
            problem = "This device has no LiDAR depth. Use an iPhone Pro."
            return
        }
        #endif
        guard let url = Self.frameURL(host) else {
            problem = "Enter the GX10 address, for example 192.168.8.10"
            return
        }
        if simulated {
            #if targetEnvironment(simulator)
            let start = CACurrentMediaTime()
            demoTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [depthPreview] _ in
                depthPreview.showSynthetic(time: CACurrentMediaTime() - start)
            }
            #endif
        } else {
            let config = ARWorldTrackingConfiguration()
            config.frameSemantics = .sceneDepth
            if let format = Self.coolestVideoFormat() { config.videoFormat = format }
            let f = config.videoFormat
            cameraFormat = "\(Int(f.imageResolution.width)) × \(Int(f.imageResolution.height)) at \(f.framesPerSecond) fps"
            session.run(config, options: [.resetTracking, .removeExistingAnchors])
        }
        sender.reset()
        lastTick = (0, CACurrentMediaTime())
        gx10.connect(to: url)
        #if !targetEnvironment(simulator)
        location.start()  // the Simulator has no GPS; skipping it also keeps its prompt out of screenshots
        #endif
        wasOpen = false
        UIApplication.shared.isIdleTimerDisabled = true
        isRunning = true
        timer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { [weak self] _ in
            Task { @MainActor in self?.tick() }
        }
    }

    func stop() {
        timer?.invalidate()
        timer = nil
        demoTimer?.invalidate()
        demoTimer = nil
        gx10.disconnect()
        location.stop()
        session.pause()
        guidance = nil
        depthPreview.clear()
        UIApplication.shared.isIdleTimerDisabled = false
        isRunning = false
        sendRate = 0
    }

    /// ARKit defaults to 60 frames a second, but only 15 are sent. A 30 a second format
    /// halves the camera, LiDAR and tracking work. Keep 4:3 so the picture lines up with the 4:3 depth.
    static func coolestVideoFormat() -> ARConfiguration.VideoFormat? {
        ARWorldTrackingConfiguration.supportedVideoFormats
            .filter { abs($0.imageResolution.width / $0.imageResolution.height - 4.0 / 3.0) < 0.01 }
            .filter { $0.framesPerSecond >= 30 }
            .min { ($0.framesPerSecond, $0.imageResolution.width) < ($1.framesPerSecond, $1.imageResolution.width) }
    }

    /// "192.168.8.10" → ws://192.168.8.10:8765. "host:port" keeps its port (handy for the fake GX10 on a laptop).
    static func frameURL(_ host: String) -> URL? {
        let h = host.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !h.isEmpty, !h.contains("/") else { return nil }
        let withPort = h.contains(":") ? h : "\(h):\(framePort)"
        return URL(string: "ws://\(withPort)")
    }

    private func tick() {
        let s = sender.snapshot()
        let now = CACurrentMediaTime()
        sendRate = Double(s.sent - lastTick.sent) / max(now - lastTick.time, 0.001)
        lastTick = (s.sent, now)
        stats = s
    }
}
