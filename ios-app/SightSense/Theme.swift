import SwiftUI

/// Colours and type for the HUD. One place, so the screen and the settings sheet match.
enum Theme {
    static let accent = Color(red: 0.35, green: 0.85, blue: 1.0)  // cyan
    static let backdrop = Color(red: 0.02, green: 0.03, blue: 0.06)

    /// Guidance state → colour. Unknown states are grey.
    static func color(forState state: String?) -> Color {
        switch state {
        case "CLEAR": return Color(red: 0.25, green: 0.95, blue: 0.55)
        case "CAUTION": return Color(red: 1.0, green: 0.72, blue: 0.2)
        case "STOP": return Color(red: 1.0, green: 0.25, blue: 0.3)
        case "UNCERTAIN": return Color(red: 0.7, green: 0.5, blue: 1.0)
        default: return .gray
        }
    }

    static func color(forLink state: GX10Link.State) -> Color {
        switch state {
        case .open: return Color(red: 0.25, green: 0.95, blue: 0.55)
        case .connecting, .retrying: return Color(red: 1.0, green: 0.72, blue: 0.2)
        case .idle: return .gray
        }
    }

    /// Small uppercase HUD label.
    static func label(_ text: String) -> some View {
        Text(text.uppercased())
            .font(.system(size: 11, weight: .semibold))
            .fontWidth(.expanded)
            .kerning(1.2)
            .foregroundStyle(.secondary)
    }
}
