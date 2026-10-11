import ARKit
import UIKit

/// Turns LiDAR depth into a colour picture for the screen: Turbo colours, near orange, far deep purple.
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
        let depthMap = depth.depthMap
        queue.async {
            let result = Self.render(depthMap)
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
        let result = Self.render(buf)
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

    private static func render(_ depth: CVPixelBuffer) -> (image: UIImage, centre: Float?)? {
        guard CVPixelBufferGetPixelFormatType(depth) == kCVPixelFormatType_DepthFloat32 else { return nil }
        CVPixelBufferLockBaseAddress(depth, .readOnly)
        defer { CVPixelBufferUnlockBaseAddress(depth, .readOnly) }
        guard let dBase = CVPixelBufferGetBaseAddress(depth) else { return nil }
        let w = CVPixelBufferGetWidth(depth), h = CVPixelBufferGetHeight(depth)
        let dRow = CVPixelBufferGetBytesPerRow(depth)

        var rgba = [UInt8](repeating: 0, count: w * h * 4)
        for y in 0..<h {
            let d = dBase.advanced(by: y * dRow).assumingMemoryBound(to: Float32.self)
            for x in 0..<w {
                let z = d[x]
                let i = (y * w + x) * 4
                // Missing readings take the far colour, so the picture has no black holes
                let k = z.isFinite && z > 0 ? Self.lutIndex(z) : 0
                rgba[i] = Self.lut[k * 3]
                rgba[i + 1] = Self.lut[k * 3 + 1]
                rgba[i + 2] = Self.lut[k * 3 + 2]
                rgba[i + 3] = 255
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

    // Colour scale: Turbo, the usual LiDAR depth look. Near is orange, then yellow, green,
    // cyan and blue, and far (or no reading) is deep purple. The nearest end stops short of
    // Turbo's dark red so close things read as bright orange.
    static let nearMetres: Float = 0.3
    static let nearestTurbo: Float = 0.82

    /// 256 entries, RGB: index 0 far, 255 near.
    static let lut: [UInt8] = (0..<256).flatMap { i -> [UInt8] in
        let (r, g, b) = turbo(Float(i) / 255 * nearestTurbo)
        return [UInt8(r * 255), UInt8(g * 255), UInt8(b * 255)]
    }

    static func lutIndex(_ metres: Float) -> Int {
        let t = 1 - (min(max(metres, nearMetres), maxMetres) - nearMetres) / (maxMetres - nearMetres)
        return Int((t * 255).rounded())
    }

    /// Google's polynomial fit of the Turbo colour map, t in 0...1.
    static func turbo(_ t: Float) -> (Float, Float, Float) {
        let r = 0.13572138 + t * (4.61539260 + t * (-42.66032258 + t * (132.13108234 + t * (-152.94239396 + t * 59.28637943))))
        let g = 0.09140261 + t * (2.19418839 + t * (4.84296658 + t * (-14.18503333 + t * (4.27729857 + t * 2.82956604))))
        let b = 0.10667330 + t * (12.64194608 + t * (-60.58204836 + t * (110.36276771 + t * (-89.90310912 + t * 27.34824973))))
        return (min(max(r, 0), 1), min(max(g, 0), 1), min(max(b, 0), 1))
    }
}
