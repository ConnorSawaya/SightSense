import SwiftUI

// Pieces of the main screen. Glass is iOS 26 Liquid Glass.

/// The depth picture blurred to fill the screen, so colour glows behind the glass.
struct DepthBackdrop: View {
    @ObservedObject var depth: DepthPreview

    var body: some View {
        // The image sits in an overlay so its fill size never widens the screen's layout.
        Theme.backdrop
            .overlay {
                if let image = depth.image {
                    Image(uiImage: image)
                        .resizable()
                        .scaledToFill()
                        .blur(radius: 50)
                        .opacity(0.55)
                        .animation(.easeOut(duration: 0.3), value: image)
                }
            }
            .overlay {
                LinearGradient(colors: [.black.opacity(0.5), .clear, .black.opacity(0.6)],
                               startPoint: .top, endPoint: .bottom)
            }
            .clipped()
            .ignoresSafeArea()
        .accessibilityHidden(true)
    }
}

/// The sharp LiDAR picture with a reticle and the distance at the centre.
struct DepthStage<Idle: View>: View {
    @ObservedObject var depth: DepthPreview
    let running: Bool
    let linkState: GX10Link.State
    let host: String
    @ViewBuilder let idle: () -> Idle

    var body: some View {
        ZStack {
            if let image = depth.image, running {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFit()
                    .clipShape(RoundedRectangle(cornerRadius: 28))
                    .overlay(RoundedRectangle(cornerRadius: 28).strokeBorder(.white.opacity(0.18), lineWidth: 1))
                    .overlay { Reticle() }
                    .overlay(alignment: .bottom) { distance.padding(14) }
                    .overlay(alignment: .top) { if linkState != .open { linkNotice.padding(14) } }
                    .accessibilityElement()
                    .accessibilityLabel(depth.centreMetres.map { String(format: "Distance ahead %.1f metres", $0) } ?? "No distance")
            } else if running {
                VStack(spacing: 12) {
                    ProgressView().tint(Theme.accent)
                    Theme.label("Starting LiDAR")
                }
            } else {
                idle()
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var distance: some View {
        HStack(alignment: .firstTextBaseline, spacing: 4) {
            Text(depth.centreMetres.map { String(format: "%.2f", $0) } ?? "—")
                .font(.system(size: 44, weight: .semibold).monospacedDigit())
                .fontWidth(.expanded)
                .contentTransition(.numericText())
            Text("m").font(.title3.weight(.medium)).foregroundStyle(.secondary)
        }
        .padding(.horizontal, 20).padding(.vertical, 8)
        .glassEffect(.regular, in: .capsule)
    }

    private var linkNotice: some View {
        HStack(spacing: 8) {
            ProgressView().controlSize(.small).tint(Theme.color(forLink: linkState))
            Text(linkState == .retrying ? "Reconnecting to \(host)" : "Connecting to \(host)")
                .font(.footnote.weight(.semibold))
        }
        .padding(.horizontal, 14).padding(.vertical, 8)
        .glassEffect(.regular.tint(Theme.color(forLink: linkState).opacity(0.25)), in: .capsule)
    }
}

/// Corner brackets and a centre square: the patch the distance is measured over.
struct Reticle: View {
    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 4)
                .strokeBorder(.white, lineWidth: 2)
                .frame(width: 26, height: 26)
                .shadow(color: Theme.accent.opacity(0.8), radius: 6)
            Brackets()
                .stroke(.white.opacity(0.6), style: StrokeStyle(lineWidth: 2, lineCap: .round))
                .frame(width: 120, height: 120)
        }
        .allowsHitTesting(false)
    }

    struct Brackets: Shape {
        func path(in r: CGRect) -> Path {
            let l: CGFloat = 18
            var p = Path()
            for (x, y, dx, dy) in [(r.minX, r.minY, 1.0, 1.0), (r.maxX, r.minY, -1.0, 1.0),
                                   (r.minX, r.maxY, 1.0, -1.0), (r.maxX, r.maxY, -1.0, -1.0)] {
                p.move(to: CGPoint(x: x + dx * l, y: y))
                p.addLine(to: CGPoint(x: x, y: y))
                p.addLine(to: CGPoint(x: x, y: y + dy * l))
            }
            return p
        }
    }
}

/// The guidance state from the GX10, tinted by state, with the spoken sentence under it.
struct GuidancePill: View {
    let message: GX10Message?
    let running: Bool
    let linkState: GX10Link.State

    var body: some View {
        let state = message?.state ?? (running && linkState == .open ? "NO_DATA" : nil)
        let color = Theme.color(forState: state)
        VStack(spacing: 2) {
            Text((state ?? "Standby").replacingOccurrences(of: "_", with: " "))
                .font(.system(size: 24, weight: .bold))
                .fontWidth(.expanded)
                .foregroundStyle(state == nil ? .secondary : color)
                .shadow(color: color.opacity(state == nil ? 0 : 0.7), radius: 10)
                .contentTransition(.opacity)
            if let speech = message?.speech, !speech.isEmpty {
                Text(speech).font(.subheadline.weight(.medium)).multilineTextAlignment(.center)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 12).padding(.horizontal, 16)
        .glassEffect(.regular.tint(color.opacity(state == nil ? 0 : 0.22)), in: .rect(cornerRadius: 24))
        .animation(.snappy, value: state)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("Guidance: \(state ?? "standby"). \(message?.speech ?? "")")
    }
}

/// Coloured dot, "GX10", and the frame rate.
struct LinkCapsule: View {
    let state: GX10Link.State
    let rate: Double
    let running: Bool

    var body: some View {
        let color = Theme.color(forLink: state)
        HStack(spacing: 8) {
            Circle()
                .fill(color)
                .frame(width: 8, height: 8)
                .shadow(color: color, radius: 4)
                .phaseAnimator([1.0, 0.35]) { dot, phase in
                    dot.opacity(state == .open ? 1 : phase)
                } animation: { _ in .easeInOut(duration: 0.7) }
            Text("GX10").font(.footnote.weight(.bold)).fontWidth(.expanded)
            if running, state == .open {
                Text(String(format: "%.0f fps", rate))
                    .font(.footnote.monospacedDigit())
                    .foregroundStyle(.secondary)
                    .contentTransition(.numericText())
            } else {
                Text(state == .idle ? "Offline" : state.rawValue)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.horizontal, 14).padding(.vertical, 10)
        .glassEffect(.regular, in: .capsule)
        .accessibilityElement(children: .combine)
    }
}

/// Small figure with a label, for tracking, depth size and delay.
struct StatChip: View {
    let label: String
    let value: String
    var tint: Color? = nil

    var body: some View {
        VStack(spacing: 2) {
            Theme.label(label)
            Text(value)
                .font(.footnote.weight(.semibold).monospacedDigit())
                .foregroundStyle(tint ?? .primary)
                .lineLimit(1)
                .minimumScaleFactor(0.7)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 8)
        .glassEffect(.regular, in: .rect(cornerRadius: 16))
        .accessibilityElement(children: .combine)
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

/// Round glass button with an icon and a caption under it.
struct QuickAction: View {
    let title: String
    let symbol: String
    let enabled: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 6) {
                Image(systemName: symbol).font(.system(size: 20, weight: .semibold))
                Text(title).font(.caption2.weight(.semibold)).fontWidth(.expanded)
            }
            .frame(width: 72, height: 64)
        }
        .buttonStyle(.glass)
        .disabled(!enabled)
    }
}

/// Red glow around the screen edge while the GX10 says STOP.
struct StopGlow: View {
    var body: some View {
        RoundedRectangle(cornerRadius: 56)
            .strokeBorder(Theme.color(forState: "STOP"), lineWidth: 10)
            .blur(radius: 14)
            .ignoresSafeArea()
            .phaseAnimator([0.35, 1.0]) { glow, phase in
                glow.opacity(phase)
            } animation: { _ in .easeInOut(duration: 0.45) }
            .allowsHitTesting(false)
            .accessibilityHidden(true)
    }
}
