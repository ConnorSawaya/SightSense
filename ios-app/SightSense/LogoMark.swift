import SwiftUI

/// The SightSense logo: a cane whose tip sends out depth rings, coloured like the LiDAR view
/// (orange near, cyan, violet far). Drawn in code so the app icon and the screen match;
/// `tools/render_icon.swift` draws the 1024 px app icon from this same view.
/// Plain SwiftUI only, so it also builds on the Mac for the icon script.
struct LogoMark: View {
    /// Draw the dark rounded tile behind the mark (the app icon); off for the mark alone.
    var tile = true

    static let navyTop = Color(red: 0.05, green: 0.13, blue: 0.22)
    static let navyBottom = Color(red: 0.01, green: 0.03, blue: 0.07)
    static let rings: [Color] = [
        Color(red: 1.0, green: 0.55, blue: 0.15),  // near: orange
        Color(red: 0.35, green: 0.85, blue: 1.0),  // the app's cyan
        Color(red: 0.45, green: 0.38, blue: 1.0),  // far: violet
    ]

    var body: some View {
        GeometryReader { geo in
            let s = min(geo.size.width, geo.size.height)
            ZStack {
                if tile {
                    LinearGradient(colors: [Self.navyTop, Self.navyBottom], startPoint: .top, endPoint: .bottom)
                    RadialGradient(colors: [Self.rings[1].opacity(0.22), .clear],
                                   center: UnitPoint(x: 0.42, y: 0.66), startRadius: 0, endRadius: s * 0.62)
                }
                // Rings fanning forward from the cane tip.
                ForEach(0..<3) { i in
                    Ring(radius: [0.2, 0.34, 0.48][i])
                        .stroke(Self.rings[i], style: StrokeStyle(lineWidth: s * [0.052, 0.044, 0.036][i], lineCap: .round))
                        .shadow(color: Self.rings[i].opacity(0.55), radius: s * 0.02)
                }
                // The cane, from the handle down to the tip.
                Cane()
                    .stroke(.white, style: StrokeStyle(lineWidth: s * 0.05, lineCap: .round, lineJoin: .round))
                    .shadow(color: .black.opacity(0.35), radius: s * 0.015, y: s * 0.008)
                // The wheel at the tip.
                Circle()
                    .fill(.white)
                    .frame(width: s * 0.1, height: s * 0.1)
                    .position(x: s * Self.tip.x, y: s * Self.tip.y)
            }
            .frame(width: s, height: s)
        }
        .aspectRatio(1, contentMode: .fit)
        .accessibilityHidden(true)
    }

    static let tip = CGPoint(x: 0.3, y: 0.76)

    /// An arc ahead of the tip: the depth reading spreading forward along the way.
    struct Ring: Shape {
        let radius: CGFloat
        func path(in r: CGRect) -> Path {
            let s = min(r.width, r.height)
            var p = Path()
            p.addArc(center: CGPoint(x: s * LogoMark.tip.x, y: s * LogoMark.tip.y), radius: s * radius,
                     startAngle: .degrees(-62), endAngle: .degrees(14), clockwise: false)
            return p
        }
    }

    /// A straight shaft with a crook at the top, curling back over the user's side.
    struct Cane: Shape {
        func path(in r: CGRect) -> Path {
            let s = min(r.width, r.height)
            var p = Path()
            p.move(to: CGPoint(x: s * LogoMark.tip.x, y: s * LogoMark.tip.y))
            p.addLine(to: CGPoint(x: s * 0.4, y: s * 0.24))
            p.addQuadCurve(to: CGPoint(x: s * 0.24, y: s * 0.25), control: CGPoint(x: s * 0.34, y: s * 0.1))
            return p
        }
    }
}
