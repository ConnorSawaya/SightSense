// Draws the 1024 px app icon from LogoMark.swift, on the Mac.
// From ios-app/:
//   swiftc -parse-as-library tools/render_icon.swift SightSense/LogoMark.swift -o /tmp/render_icon \
//     && /tmp/render_icon SightSense/Assets.xcassets/AppIcon.appiconset/AppIcon.png
import AppKit
import SwiftUI

@main
struct RenderIcon {
    @MainActor static func main() {
        let out = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "AppIcon.png"
        let renderer = ImageRenderer(content: LogoMark().frame(width: 1024, height: 1024))
        renderer.scale = 1
        guard let cg = renderer.cgImage else { fatalError("could not draw the icon") }
        // The App Store icon must have no transparency: draw onto an opaque context.
        let ctx = CGContext(data: nil, width: 1024, height: 1024, bitsPerComponent: 8, bytesPerRow: 0,
                            space: CGColorSpace(name: CGColorSpace.sRGB)!,
                            bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
        ctx.draw(cg, in: CGRect(x: 0, y: 0, width: 1024, height: 1024))
        let rep = NSBitmapImageRep(cgImage: ctx.makeImage()!)
        try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: out))
        print("wrote", out)
    }
}
