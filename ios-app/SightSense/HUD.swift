import SwiftUI

// Pieces of the main screen. Glass is iOS 26 Liquid Glass.

/// The LiDAR depth picture, edge to edge. Near red, far blue, no reading black.
struct LiDARFeed: View {
    @ObservedObject var depth: DepthPreview
    let running: Bool

    var body: some View {
        // The image sits in an overlay so its fill size never widens the screen's layout.
        Theme.backdrop
            .overlay {
                if running, let image = depth.image {
                    Image(uiImage: image)
                        .resizable()
                        .scaledToFill()
                }
            }
            .clipped()
            .ignoresSafeArea()
            .accessibilityElement()
            .accessibilityLabel(running ? "LiDAR view" : "")
            .accessibilityValue(depth.centreMetres.map { String(format: "%.1f metres ahead", $0) } ?? "")
    }
}

/// A glow around the screen edge in the guidance colour: pulsing red on STOP, a steady
/// amber or purple for CAUTION and UNCERTAIN, a faint green for CLEAR, nothing when idle.
struct StateEdge: View {
    let state: String?

    var body: some View {
        if let state {
            let edge = RoundedRectangle(cornerRadius: 56)
                .strokeBorder(Theme.color(forState: state), lineWidth: state == "CLEAR" ? 4 : 8)
                .blur(radius: 12)
                .ignoresSafeArea()
                .allowsHitTesting(false)
                .accessibilityHidden(true)
            if state == "STOP" {
                edge.phaseAnimator([0.35, 1.0]) { glow, phase in
                    glow.opacity(phase)
                } animation: { _ in .easeInOut(duration: 0.45) }
            } else {
                edge.opacity(state == "CLEAR" ? 0.45 : 0.8)
                    .animation(.easeInOut(duration: 0.3), value: state)
            }
        }
    }
}

/// Link to the GX10: green connected, pulsing amber connecting, grey off.
struct StatusDot: View {
    let state: GX10Link.State

    var body: some View {
        let color = Theme.color(forLink: state)
        Circle()
            .fill(color)
            .frame(width: 12, height: 12)
            .shadow(color: color, radius: 5)
            .phaseAnimator([1.0, 0.35]) { dot, phase in
                dot.opacity(state == .open || state == .idle ? 1 : phase)
            } animation: { _ in .easeInOut(duration: 0.7) }
    }
}

/// Large hold-to-talk button.
struct TalkButton: View {
    @ObservedObject var voice: Voice
    let enabled: Bool
    let onText: (String) -> Void

    var body: some View {
        Image(systemName: voice.isListening ? "waveform" : "mic.fill")
            .font(.system(size: 30, weight: .semibold))
            .symbolEffect(.variableColor.iterative, isActive: voice.isListening)
            .frame(width: 88, height: 88)
            .foregroundStyle(voice.isListening ? .white : (enabled ? Theme.accent : .secondary))
            .glassEffect(.regular.tint(voice.isListening ? Color.red.opacity(0.55) : Theme.accent.opacity(0.12)).interactive(),
                         in: .circle)
            .scaleEffect(voice.isListening ? 1.12 : 1)
            .animation(.spring(response: 0.3, dampingFraction: 0.6), value: voice.isListening)
            .opacity(enabled ? 1 : 0.5)
            .gesture(
                DragGesture(minimumDistance: 0)
                    .onChanged { _ in
                        guard enabled, !voice.isListening else { return }
                        voice.start(done: onText)
                    }
                    .onEnded { _ in voice.stop() }
            )
            .sensoryFeedback(.impact(weight: .medium), trigger: voice.isListening)
            .accessibilityLabel("Talk")
            .accessibilityHint("Hold and say a command, then let go")
            .accessibilityAddTraits(.isButton)
    }
}
