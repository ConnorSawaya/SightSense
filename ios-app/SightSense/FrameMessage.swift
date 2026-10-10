import CoreVideo
import Foundation

/// The frame message from contracts/MESSAGES.md, without ARKit, so it can be tested on a Mac:
/// 4-byte little-endian header length, JSON header, JPEG, depth (UInt16 mm, LE), confidence (UInt8).
enum FrameMessage {
    static func pack(header: [String: Any], jpeg: Data, depth: Data, confidence: Data) throws -> Data {
        var header = header
        header["jpeg_len"] = jpeg.count
        header["depth_len"] = depth.count
        header["conf_len"] = confidence.count
        let json = try JSONSerialization.data(withJSONObject: header)
        var out = Data(capacity: 4 + json.count + jpeg.count + depth.count + confidence.count)
        var len = UInt32(json.count).littleEndian
        withUnsafeBytes(of: &len) { out.append(contentsOf: $0) }
        out.append(json)
        out.append(jpeg)
        out.append(depth)
        out.append(confidence)
        return out
    }

    /// Float32 metres → UInt16 millimetres, little-endian, row by row. Missing or bad readings become 0.
    static func depthMillimetres(_ buffer: CVPixelBuffer) -> (data: Data, width: Int, height: Int)? {
        guard CVPixelBufferGetPixelFormatType(buffer) == kCVPixelFormatType_DepthFloat32 else { return nil }
        CVPixelBufferLockBaseAddress(buffer, .readOnly)
        defer { CVPixelBufferUnlockBaseAddress(buffer, .readOnly) }
        guard let base = CVPixelBufferGetBaseAddress(buffer) else { return nil }
        let w = CVPixelBufferGetWidth(buffer), h = CVPixelBufferGetHeight(buffer)
        let rowBytes = CVPixelBufferGetBytesPerRow(buffer)
        var out = Data(count: w * h * 2)
        out.withUnsafeMutableBytes { raw in
            let dst = raw.bindMemory(to: UInt16.self)
            for y in 0..<h {
                let row = base.advanced(by: y * rowBytes).assumingMemoryBound(to: Float32.self)
                for x in 0..<w {
                    dst[y * w + x] = millimetres(row[x]).littleEndian
                }
            }
        }
        return (out, w, h)
    }

    static func millimetres(_ metres: Float32) -> UInt16 {
        guard metres.isFinite, metres > 0 else { return 0 }
        return UInt16(min(metres * 1000, 65535).rounded())
    }

    /// ARConfidenceLevel per pixel: 0 low, 1 medium, 2 high.
    static func confidenceBytes(_ buffer: CVPixelBuffer) -> Data? {
        guard CVPixelBufferGetPixelFormatType(buffer) == kCVPixelFormatType_OneComponent8 else { return nil }
        CVPixelBufferLockBaseAddress(buffer, .readOnly)
        defer { CVPixelBufferUnlockBaseAddress(buffer, .readOnly) }
        guard let base = CVPixelBufferGetBaseAddress(buffer) else { return nil }
        let w = CVPixelBufferGetWidth(buffer), h = CVPixelBufferGetHeight(buffer)
        let rowBytes = CVPixelBufferGetBytesPerRow(buffer)
        var out = Data(capacity: w * h)
        for y in 0..<h {
            out.append(base.advanced(by: y * rowBytes).assumingMemoryBound(to: UInt8.self), count: w)
        }
        return out
    }

    /// Camera-to-world transform, 16 numbers, column by column.
    static func pose(columns: [SIMD4<Float>]) -> [Double] {
        columns.flatMap { [$0.x, $0.y, $0.z, $0.w] }.map(Double.init)
    }

    /// Intrinsics for the full camera picture, scaled to the depth picture's size.
    static func scaledIntrinsics(fx: Float, fy: Float, cx: Float, cy: Float,
                                 from image: CGSize, toWidth w: Int, height h: Int) -> (fx: Double, fy: Double, cx: Double, cy: Double) {
        let sx = Double(w) / Double(image.width), sy = Double(h) / Double(image.height)
        return (Double(fx) * sx, Double(fy) * sy, Double(cx) * sx, Double(cy) * sy)
    }

    static func thermalName(_ state: ProcessInfo.ThermalState) -> String {
        switch state {
        case .nominal: return "nominal"
        case .fair: return "fair"
        case .serious: return "serious"
        case .critical: return "critical"
        @unknown default: return "unknown"
        }
    }
}
