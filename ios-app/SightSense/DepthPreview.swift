import ARKit
import UIKit

/// Turns LiDAR depth into a colour picture for the screen: near red, far blue, low confidence dark.
/// Only for people looking at the phone; the GX10 gets the raw depth.
final class DepthPreview: ObservableObject {
    @MainActor @Published private(set) var image: UIImage?
    @MainActor @Published private(set) var centreMetres: Float?

    static let maxMetres: Float = 5
    /// Pictures a second on screen: 5 normally, 2 when the phone is hot. Only for people looking at the phone.
    static func interval(for thermal: ProcessInfo.ThermalState) -> TimeInterval {
        thermal.rawValue >= ProcessInfo.ThermalState.serious.rawValue ? 0.5 : 0.2
    }

    private let lock = NSLock()
    private var last: TimeInterval = 0
    private var busy = false
    private let queue = DispatchQueue(label: "depth.preview", qos: .utility)

    /// Called on the ARKit delegate queue for every frame; draws at most 10 a second, never queues.
    func update(_ frame: ARFrame) {
        guard let depth = frame.sceneDepth else { return }
        let go: Bool = lock.withLock {
            guard !busy, frame.timestamp - last >= Self.interval(for: ProcessInfo.processInfo.thermalState) else { return false }
            busy = true
            last = frame.timestamp
            return true
        }
        guard go else { return }
        let depthMap = depth.depthMap, confidence = depth.confidenceMap
        queue.async {
            let result = Self.render(depthMap, confidence)
            self.lock.withLock { self.busy = false }
            Task { @MainActor in
                self.image = result?.image
                self.centreMetres = result?.centre
            }
        }
    }

    #if targetEnvironment(simulator)
    /// Simulator only: a made-up room (floor, a wall, a box drifting side to side) so the screen can be designed.
    func showSynthetic(time t: Double) {
        let w = 256, h = 192
        var buf: CVPixelBuffer?
        CVPixelBufferCreate(nil, w, h, kCVPixelFormatType_DepthFloat32, nil, &buf)
        guard let buf else { return }
        CVPixelBufferLockBaseAddress(buf, [])
        let row = CVPixelBufferGetBytesPerRow(buf)
        let boxX = 0.5 + 0.25 * sin(t * 0.7)  // across the picture's width (up/down once turned upright)
        for y in 0..<h {
            let d = CVPixelBufferGetBaseAddress(buf)!.advanced(by: y * row).assumingMemoryBound(to: Float32.self)
            for x in 0..<w {
                let u = Double(x) / Double(w), v = Double(y) / Double(h)
                var z = 0.6 + 4.2 * u  // floor running away from the camera
                if abs(u - boxX) < 0.12 && abs(v - 0.5) < 0.18 { z = 1.1 + 0.2 * sin(t) }  // box
                if u > 0.92 { z = .nan }  // missing readings at the far edge
                d[x] = Float32(z)
            }
        }
        CVPixelBufferUnlockBaseAddress(buf, [])
        let result = Self.render(buf, nil)
        Task { @MainActor in
            self.image = result?.image
            self.centreMetres = result?.centre
        }
    }
    #endif

    @MainActor func clear() {
        image = nil
        centreMetres = nil
    }

    private static func render(_ depth: CVPixelBuffer, _ confidence: CVPixelBuffer?) -> (image: UIImage, centre: Float?)? {
        guard CVPixelBufferGetPixelFormatType(depth) == kCVPixelFormatType_DepthFloat32 else { return nil }
        CVPixelBufferLockBaseAddress(depth, .readOnly)
        defer { CVPixelBufferUnlockBaseAddress(depth, .readOnly) }
        if let confidence { CVPixelBufferLockBaseAddress(confidence, .readOnly) }
        defer { if let confidence { CVPixelBufferUnlockBaseAddress(confidence, .readOnly) } }
        guard let dBase = CVPixelBufferGetBaseAddress(depth) else { return nil }
        let w = CVPixelBufferGetWidth(depth), h = CVPixelBufferGetHeight(depth)
        let dRow = CVPixelBufferGetBytesPerRow(depth)
        let cBase = confidence.flatMap(CVPixelBufferGetBaseAddress)
        let cRow = confidence.map(CVPixelBufferGetBytesPerRow) ?? 0

        var rgba = [UInt8](repeating: 0, count: w * h * 4)
        for y in 0..<h {
            let d = dBase.advanced(by: y * dRow).assumingMemoryBound(to: Float32.self)
            let c = cBase?.advanced(by: y * cRow).assumingMemoryBound(to: UInt8.self)
            for x in 0..<w {
                let z = d[x]
                let i = (y * w + x) * 4
                rgba[i + 3] = 255
                guard z.isFinite, z > 0 else { continue }  // missing: black
                let (r, g, b) = colour(min(z / maxMetres, 1))
                let dim: Float = (c?[x] ?? 2) == 0 ? 0.3 : 1  // low confidence: dark
                rgba[i] = UInt8(r * dim * 255)
                rgba[i + 1] = UInt8(g * dim * 255)
                rgba[i + 2] = UInt8(b * dim * 255)
            }
        }

        // Median of the middle 8 x 8 pixels.
        var mid: [Float] = []
        for y in (h / 2 - 4)..<(h / 2 + 4) {
            let d = dBase.advanced(by: y * dRow).assumingMemoryBound(to: Float32.self)
            for x in (w / 2 - 4)..<(w / 2 + 4) where d[x].isFinite && d[x] > 0 { mid.append(d[x]) }
        }
        let centre = mid.isEmpty ? nil : mid.sorted()[mid.count / 2]

        guard let provider = CGDataProvider(data: Data(rgba) as CFData),
              let cg = CGImage(width: w, height: h, bitsPerComponent: 8, bitsPerPixel: 32, bytesPerRow: w * 4,
                               space: CGColorSpaceCreateDeviceRGB(),
                               bitmapInfo: CGBitmapInfo(rawValue: CGImageAlphaInfo.noneSkipLast.rawValue),
                               provider: provider, decode: nil, shouldInterpolate: true, intent: .defaultIntent)
        else { return nil }
        // Depth is in the sensor's landscape direction; turn it upright for a phone held in portrait.
        return (UIImage(cgImage: cg, scale: 1, orientation: .right), centre)
    }

    /// 0 near → red, through yellow and green, → 1 far blue.
    private static func colour(_ t: Float) -> (Float, Float, Float) {
        let stops: [(Float, Float, Float)] = [(1, 0.1, 0.1), (1, 0.85, 0.1), (0.2, 0.85, 0.3), (0.1, 0.4, 1)]
        let s = t * Float(stops.count - 1)
        let i = min(Int(s), stops.count - 2)
        let f = s - Float(i)
        let a = stops[i], b = stops[i + 1]
        return (a.0 + (b.0 - a.0) * f, a.1 + (b.1 - a.1) * f, a.2 + (b.2 - a.2) * f)
    }
}
