import ARKit
import CoreImage
import ImageIO

/// Turns an ARKit frame into the frame message (see FrameMessage).
/// Picture and depth are sent in the sensor's landscape direction, exactly as ARKit gives them.
final class FrameEncoder {
    static let rgbWidth = 640
    var jpegQuality: CGFloat = 0.6

    private let ciContext = CIContext(options: [.cacheIntermediates: false])
    private let sRGB = CGColorSpace(name: CGColorSpace.sRGB)!

    struct Extras {
        var lat: Double?
        var lon: Double?
        var gpsAccuracy: Double?
        var heading: Double?
    }

    struct Encoded {
        let data: Data
        let depthWidth: Int
        let depthHeight: Int
    }

    enum Failure: Error, CustomStringConvertible {
        case noDepth, badDepthFormat, jpeg
        var description: String {
            switch self {
            case .noDepth: return "no LiDAR depth in frame"
            case .badDepthFormat: return "unexpected depth format"
            case .jpeg: return "JPEG encoding failed"
            }
        }
    }

    func encode(_ frame: ARFrame, seq: Int, extras: Extras) throws -> Encoded {
        guard let depth = frame.sceneDepth else { throw Failure.noDepth }
        guard let d = FrameMessage.depthMillimetres(depth.depthMap) else { throw Failure.badDepthFormat }
        let conf = depth.confidenceMap.flatMap(FrameMessage.confidenceBytes)
            ?? Data(count: d.width * d.height)  // missing confidence = all low, so the GX10 ignores it
        let (jpeg, rgbW, rgbH) = try jpeg(frame.capturedImage)

        let K = frame.camera.intrinsics  // column-major, for the full camera picture
        let k = FrameMessage.scaledIntrinsics(fx: K[0][0], fy: K[1][1], cx: K[2][0], cy: K[2][1],
                                              from: frame.camera.imageResolution, toWidth: d.width, height: d.height)
        let t = frame.camera.transform

        let header: [String: Any] = [
            "seq": seq,
            "t_capture": frame.timestamp,
            "rgb_w": rgbW,
            "rgb_h": rgbH,
            "depth_w": d.width,
            "depth_h": d.height,
            "fx": k.fx,
            "fy": k.fy,
            "cx": k.cx,
            "cy": k.cy,
            "pose": FrameMessage.pose(columns: [t.columns.0, t.columns.1, t.columns.2, t.columns.3]),
            "tracking": Self.trackingName(frame.camera.trackingState),
            "lat": extras.lat ?? NSNull(),
            "lon": extras.lon ?? NSNull(),
            "gps_acc_m": extras.gpsAccuracy ?? NSNull(),
            "heading_deg": extras.heading ?? NSNull(),
            "thermal": FrameMessage.thermalName(ProcessInfo.processInfo.thermalState),
        ]
        let data = try FrameMessage.pack(header: header, jpeg: jpeg, depth: d.data, confidence: conf)
        return Encoded(data: data, depthWidth: d.width, depthHeight: d.height)
    }

    private func jpeg(_ buffer: CVPixelBuffer) throws -> (Data, Int, Int) {
        let image = CIImage(cvPixelBuffer: buffer)
        let w = CVPixelBufferGetWidth(buffer), h = CVPixelBufferGetHeight(buffer)
        let outW = Self.rgbWidth
        let outH = Int((Double(h) * Double(outW) / Double(w)).rounded())
        let scaled = image
            .transformed(by: CGAffineTransform(scaleX: CGFloat(outW) / CGFloat(w), y: CGFloat(outH) / CGFloat(h)))
            .cropped(to: CGRect(x: 0, y: 0, width: outW, height: outH))
        let quality = CIImageRepresentationOption(rawValue: kCGImageDestinationLossyCompressionQuality as String)
        guard let data = ciContext.jpegRepresentation(of: scaled, colorSpace: sRGB, options: [quality: jpegQuality]) else {
            throw Failure.jpeg
        }
        return (data, outW, outH)
    }

    static func trackingName(_ state: ARCamera.TrackingState) -> String {
        // The words gx10/navigator checks: "notAvailable" or "relocalizing" drops a stored target.
        switch state {
        case .normal: return "normal"
        case .notAvailable: return "notAvailable"
        case .limited(.relocalizing): return "relocalizing"
        case .limited: return "limited"
        }
    }
}
