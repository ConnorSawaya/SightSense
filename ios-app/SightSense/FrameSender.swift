import ARKit

/// Takes ARKit frames and sends about 15 a second to the GX10.
/// Never queues: if the previous frame is still being encoded or sent, the new one is skipped.
final class FrameSender: NSObject, ARSessionDelegate {
    struct Stats {
        var sent = 0
        var skipped = 0
        var failed = 0
        var bytes = 0
        var lastEncodeMs = 0.0
        var lastSendMs = 0.0
        var depthSize: String?
        var tracking = "—"
        var lastError: String?
    }

    static let framesPerSecond = 15.0

    private let link: GX10Link
    private let encoder = FrameEncoder()
    private let encodeQueue = DispatchQueue(label: "frame.encode", qos: .userInitiated)
    private let lock = NSLock()
    private var inFlight = false
    private var lastSent: TimeInterval = 0
    private var seq = 0
    private var stats = Stats()
    private var extras = FrameEncoder.Extras()

    /// Every ARKit frame, on the delegate queue, whether or not the GX10 is connected.
    var onFrame: ((ARFrame) -> Void)?

    init(link: GX10Link) {
        self.link = link
    }

    func reset() {
        lock.withLock {
            stats = Stats()
            lastSent = 0
        }
    }

    func snapshot() -> Stats {
        lock.withLock { stats }
    }

    /// Location and heading for the next frames. Any field may be nil.
    func setExtras(_ value: FrameEncoder.Extras) {
        lock.withLock { extras = value }
    }

    // MARK: - ARSessionDelegate (on the session's delegate queue)

    func session(_ session: ARSession, didUpdate frame: ARFrame) {
        onFrame?(frame)
        let interval = 1 / Self.framesPerSecond
        let tracking = Self.describe(frame.camera.trackingState)
        lock.lock()
        stats.tracking = tracking
        let due = frame.timestamp - lastSent >= interval * 0.9
        guard due, link.isOpen else {
            lock.unlock()
            return
        }
        guard !inFlight else {
            stats.skipped += 1
            lastSent = frame.timestamp  // count one skip per due slot, not per ARKit frame
            lock.unlock()
            return
        }
        inFlight = true
        lastSent = frame.timestamp
        seq += 1
        let seq = self.seq
        let extras = self.extras
        lock.unlock()

        // Holding one ARFrame while it is encoded is fine; holding many stalls ARKit.
        encodeQueue.async { [weak self] in
            guard let self else { return }
            let t0 = CACurrentMediaTime()
            let encoded: FrameEncoder.Encoded
            do {
                encoded = try self.encoder.encode(frame, seq: seq, extras: extras)
            } catch {
                self.finish { $0.failed += 1; $0.lastError = "\(error)" }
                return
            }
            let t1 = CACurrentMediaTime()
            self.link.send(encoded.data) { ok in
                let t2 = CACurrentMediaTime()
                self.finish { s in
                    s.lastEncodeMs = (t1 - t0) * 1000
                    s.depthSize = "\(encoded.depthWidth) × \(encoded.depthHeight)"
                    if ok {
                        s.sent += 1
                        s.bytes += encoded.data.count
                        s.lastSendMs = (t2 - t1) * 1000
                    } else {
                        s.failed += 1
                        s.lastError = "send failed"
                    }
                }
            }
        }
    }

    private func finish(_ update: (inout Stats) -> Void) {
        lock.withLock {
            update(&stats)
            inFlight = false
        }
    }

    static func describe(_ state: ARCamera.TrackingState) -> String {
        switch state {
        case .normal: return "Normal"
        case .notAvailable: return "Not available"
        case .limited(let reason):
            switch reason {
            case .initializing: return "Limited: starting up"
            case .excessiveMotion: return "Limited: moving too fast"
            case .insufficientFeatures: return "Limited: too little detail"
            case .relocalizing: return "Limited: relocalizing"
            @unknown default: return "Limited"
            }
        }
    }
}
