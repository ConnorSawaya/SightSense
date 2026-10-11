import SwiftUI

// Pieces of the main screen. Glass is iOS 26 Liquid Glass.
// Animations run only when something changes (state, listening, connecting), never every frame,
// because the phone is already warm from the LiDAR.

/// Dark background with a soft glow in the guidance colour. Static: a live full-screen blur
/// of the depth picture cost GPU time on a phone that is already hot from the LiDAR.
struct Backdrop: View {
    let state: String?

    var body: some View {
        let glow = state == nil ? Theme.accent.opacity(0.14) : Theme.color(forState: state).opacity(0.26)
        Theme.backdrop
            .overlay {
                RadialGradient(colors: [glow, .clear], center: .top, startRadius: 10, endRadius: 560)
            }
            .animation(.easeInOut(duration: 0.4), value: state)
            .ignoresSafeArea()
            .accessibilityHidden(true)
    }
}

// MARK: - Guidance

/// The guidance from the GX10: an icon and the state, the spoken sentence, and a
/// parking-sensor bar for the distance at the centre of the LiDAR picture.
struct GuidanceCard: View {
    let message: GX10Message?
    let running: Bool
    let linkState: GX10Link.State
    @ObservedObject var depth: DepthPreview

    private var state: String? { message?.state ?? (running && linkState == .open ? "NO_DATA" : nil) }

    var body: some View {
        let color = Theme.color(forState: state)
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 14) {
                Image(systemName: Theme.symbol(forState: state))
                    .font(.system(size: 22, weight: .bold))
                    .foregroundStyle(state == nil ? .secondary : color)
                    .contentTransition(.symbolEffect(.replace))
                    .symbolEffect(.bounce, value: state)
                    .frame(width: 48, height: 48)
                    .background(color.opacity(state == nil ? 0.08 : 0.18), in: .circle)
                    .overlay(Circle().strokeBorder(color.opacity(state == nil ? 0.15 : 0.5), lineWidth: 1))

                VStack(alignment: .leading, spacing: 3) {
                    Text(Theme.title(forState: state))
                        .font(.system(size: 22, weight: .bold))
                        .fontWidth(.expanded)
                        .foregroundStyle(state == nil ? .secondary : color)
                        .contentTransition(.interpolate)
                    Text(subtitle)
                        .font(.subheadline.weight(.medium))
                        .foregroundStyle(message?.speech?.isEmpty == false ? .primary : .secondary)
                        .lineLimit(2)
                        .contentTransition(.opacity)
                }
                Spacer(minLength: 0)
            }
            if running { ProximityBar(metres: depth.centreMetres) }
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .glassEffect(.regular.tint(color.opacity(state == nil ? 0 : 0.16)), in: .rect(cornerRadius: 28))
        .animation(.snappy, value: state)
        .animation(.snappy, value: message?.speech)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("Guidance: \(Theme.title(forState: state)). \(message?.speech ?? "")")
    }

    private var subtitle: String {
        if let speech = message?.speech, !speech.isEmpty { return speech }
        switch state {
        case nil: return "Connect to the GX10 to start"
        case "NO_DATA": return "Waiting for guidance from the GX10"
        case "CLEAR": return "The way ahead is open"
        case "CAUTION": return "Something is near the path"
        case "STOP": return "Obstacle close ahead"
        default: return "Not sure about the way ahead"
        }
    }
}

/// Distance at the centre of the LiDAR picture on a 0 to 5 m bar, like a car's parking sensor.
/// The zones mark the GX10's distances (stop 1.2 m, caution 2.5 m); the GX10 judges a corridor,
/// not just the centre, so this is a guide for people watching, not the decision.
struct ProximityBar: View {
    let metres: Float?
    static let range: ClosedRange<Float> = 0...5
    static let zones: [(upTo: Float, state: String)] = [(1.2, "STOP"), (2.5, "CAUTION"), (5, "CLEAR")]

    var body: some View {
        VStack(spacing: 6) {
            GeometryReader { geo in
                let w = geo.size.width
                ZStack(alignment: .leading) {
                    HStack(spacing: 3) {
                        ForEach(Array(Self.zones.enumerated()), id: \.offset) { i, zone in
                            let from = i == 0 ? Self.range.lowerBound : Self.zones[i - 1].upTo
                            let lit = metres.map { $0 < zone.upTo } ?? false
                            Capsule()
                                .fill(Theme.color(forState: zone.state).opacity(lit && active(zone.state) ? 0.95 : 0.22))
                                .frame(width: max(0, CGFloat((zone.upTo - from) / Self.range.upperBound) * w - 3))
                        }
                    }
                    if let m = metres {
                        Capsule()
                            .fill(.white)
                            .frame(width: 4, height: 16)
                            .shadow(color: .black.opacity(0.5), radius: 3)
                            .offset(x: CGFloat(min(max(m, 0), Self.range.upperBound) / Self.range.upperBound) * (w - 4))
                    }
                }
                .frame(height: 16)
            }
            .frame(height: 16)
            .animation(.smooth(duration: 0.25), value: metres)

            HStack {
                Text("0").frame(maxWidth: .infinity, alignment: .leading)
                Text("1.2").frame(maxWidth: .infinity)
                Text("2.5").frame(maxWidth: .infinity)
                Text("5 m").frame(maxWidth: .infinity, alignment: .trailing)
            }
            .font(.caption2.monospacedDigit())
            .foregroundStyle(.tertiary)
        }
        .accessibilityHidden(true)
    }

    /// Light only the zone the distance is in, so the bar reads at a glance.
    private func active(_ state: String) -> Bool {
        guard let m = metres else { return false }
        let zone = Self.zones.first { m < $0.upTo }?.state ?? "CLEAR"
        return zone == state
    }
}

// MARK: - LiDAR

/// The LiDAR picture with a reticle, the centre distance, a colour key and small readouts in the corners.
struct DepthStage<Idle: View>: View {
    @ObservedObject var depth: DepthPreview
    let running: Bool
    let linkState: GX10Link.State
    let host: String
    let stats: FrameSender.Stats
    @ViewBuilder let idle: () -> Idle

    private var hot: Bool { stats.thermal.rawValue >= ProcessInfo.ThermalState.serious.rawValue }

    var body: some View {
        ZStack {
            if let image = depth.image, running {
                Image(uiImage: image)
                    .resizable()
                    .interpolation(.high)  // smooth, like a regular depth view; the depth is only 256 x 192
                    .scaledToFit()
                    .clipShape(RoundedRectangle(cornerRadius: 30))
                    .overlay(RoundedRectangle(cornerRadius: 30).strokeBorder(.white.opacity(0.16), lineWidth: 1))
                    .overlay { Reticle() }
                    .overlay(alignment: .top) { topReadouts.padding(12) }
                    .overlay(alignment: .bottom) { bottom.padding(12) }
                    .accessibilityElement()
                    .accessibilityLabel(depth.centreMetres.map { String(format: "Distance ahead %.1f metres", $0) } ?? "No distance")
                    .transition(.opacity.combined(with: .scale(scale: 0.97)))
            } else if running {
                VStack(spacing: 14) {
                    ProgressView().controlSize(.large).tint(Theme.accent)
                    Theme.label("Starting LiDAR")
                }
                .transition(.opacity)
            } else {
                idle().transition(.blurReplace)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .animation(.smooth(duration: 0.35), value: depth.image == nil)
        .animation(.smooth(duration: 0.35), value: running)
    }

    @ViewBuilder private var topReadouts: some View {
        VStack(spacing: 8) {
            HStack {
                HUDTag(symbol: "camera.metering.matrix",
                       text: stats.depthSize?.replacingOccurrences(of: " ", with: "") ?? "LiDAR")
                Spacer()
                HUDTag(symbol: "location.viewfinder", text: shortTracking,
                       tint: stats.tracking == "Normal" || stats.tracking == "—" ? nil : Theme.color(forState: "CAUTION"))
            }
            if linkState != .open {
                HStack(spacing: 8) {
                    ProgressView().controlSize(.small).tint(Theme.color(forLink: linkState))
                    Text(linkState == .retrying ? "Reconnecting to \(host)" : "Connecting to \(host)")
                        .font(.footnote.weight(.semibold))
                        .lineLimit(1)
                }
                .padding(.horizontal, 14).padding(.vertical, 8)
                .glassEffect(.regular.tint(Theme.color(forLink: linkState).opacity(0.25)), in: .capsule)
                .transition(.move(edge: .top).combined(with: .opacity))
            }
            if hot {
                Label(String(format: "Phone is hot: %.0f frames a second", stats.targetRate), systemImage: "thermometer.high")
                    .font(.footnote.weight(.semibold))
                    .foregroundStyle(Theme.color(forState: "CAUTION"))
                    .padding(.horizontal, 14).padding(.vertical, 8)
                    .glassEffect(.regular.tint(Theme.color(forState: "CAUTION").opacity(0.2)), in: .capsule)
                    .transition(.move(edge: .top).combined(with: .opacity))
            }
        }
        .animation(.snappy, value: linkState)
        .animation(.snappy, value: hot)
    }

    private var bottom: some View {
        VStack(spacing: 10) {
            HStack(alignment: .firstTextBaseline, spacing: 4) {
                Text(depth.centreMetres.map { String(format: "%.2f", $0) } ?? "—")
                    .font(.system(size: 46, weight: .semibold).monospacedDigit())
                    .fontWidth(.expanded)
                    .contentTransition(.numericText(value: Double(depth.centreMetres ?? 0)))
                Text("m").font(.title3.weight(.medium)).foregroundStyle(.secondary)
            }
            .padding(.horizontal, 22).padding(.vertical, 6)
            .glassEffect(.regular, in: .capsule)
            .animation(.snappy, value: depth.centreMetres)

            HStack(spacing: 8) {
                DepthKey()
                HUDTag(symbol: "arrow.up.arrow.down",
                       text: linkState == .open ? String(format: "%.0f ms", stats.lastSendMs) : "—")
            }
        }
    }

    private var shortTracking: String {
        let t = stats.tracking
        return t.hasPrefix("Limited") ? "Limited" : (t == "—" ? "Tracking" : t)
    }
}

/// Small glass readout used in the corners of the LiDAR picture.
struct HUDTag: View {
    let symbol: String
    let text: String
    var tint: Color? = nil

    var body: some View {
        HStack(spacing: 5) {
            Image(systemName: symbol).font(.caption2.weight(.bold))
            Text(text).font(.caption.weight(.semibold).monospacedDigit()).lineLimit(1)
        }
        .foregroundStyle(tint ?? .primary)
        .padding(.horizontal, 10).padding(.vertical, 6)
        .glassEffect(.regular, in: .capsule)
        .contentTransition(.numericText())
    }
}

/// The colour key for the LiDAR picture: the same Turbo colours, near on the left.
struct DepthKey: View {
    static let gradient: Gradient = {
        let steps = 12
        return Gradient(colors: (0...steps).map { i in
            let t = Float(i) / Float(steps)
            let (r, g, b) = DepthPreview.turbo(DepthPreview.nearestTurbo * (1 - t))
            return Color(red: Double(r), green: Double(g), blue: Double(b))
        })
    }()

    var body: some View {
        HStack(spacing: 8) {
            Text(String(format: "%.1f", DepthPreview.nearMetres))
            Capsule()
                .fill(LinearGradient(gradient: Self.gradient, startPoint: .leading, endPoint: .trailing))
                .frame(height: 6)
            Text(String(format: "%.0f m", DepthPreview.maxMetres))
        }
        .font(.caption2.weight(.semibold).monospacedDigit())
        .foregroundStyle(.secondary)
        .padding(.horizontal, 12).padding(.vertical, 8)
        .glassEffect(.regular, in: .capsule)
        .accessibilityHidden(true)
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
            Circle().fill(.white).frame(width: 3, height: 3)
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

/// Rings spreading out from an antenna, for the screen before connecting.
struct RadarPulse: View {
    var body: some View {
        ZStack {
            ForEach(0..<3) { i in
                Circle()
                    .stroke(Theme.accent.opacity(0.5), lineWidth: 1.5)
                    .phaseAnimator([false, true]) { ring, out in
                        ring.scaleEffect(out ? 1 : 0.35).opacity(out ? 0 : 0.9)
                    } animation: { out in
                        out ? .easeOut(duration: 2.4).delay(Double(i) * 0.8) : .linear(duration: 0)
                    }
            }
            Image(systemName: "dot.radiowaves.left.and.right")
                .font(.system(size: 30, weight: .medium))
                .foregroundStyle(Theme.accent)
                .frame(width: 64, height: 64)
                .glassEffect(.regular.tint(Theme.accent.opacity(0.15)), in: .circle)
        }
        .frame(width: 150, height: 150)
        .accessibilityHidden(true)
    }
}

// MARK: - Top bar

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
                    .contentTransition(.numericText(value: rate))
            } else {
                Text(state == .idle ? "Offline" : state.rawValue.capitalized)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.horizontal, 14)
        .frame(height: 44)
        .glassEffect(.regular.interactive(), in: .capsule)
        .animation(.snappy, value: state)
        .accessibilityElement(children: .combine)
    }
}

// MARK: - Dock

/// Large hold-to-talk button. Rings spread out while listening.
struct TalkButton: View {
    @ObservedObject var voice: Voice
    let enabled: Bool
    let onText: (String) -> Void

    var body: some View {
        ZStack {
            if voice.isListening {
                ForEach(0..<2) { i in
                    Circle()
                        .stroke(Color.red.opacity(0.6), lineWidth: 2)
                        .phaseAnimator([false, true]) { ring, out in
                            ring.scaleEffect(out ? 1.6 : 1).opacity(out ? 0 : 0.8)
                        } animation: { out in
                            out ? .easeOut(duration: 1.2).delay(Double(i) * 0.6) : .linear(duration: 0)
                        }
                }
                .frame(width: 84, height: 84)
                .transition(.opacity)
            }
            Image(systemName: voice.isListening ? "waveform" : "mic.fill")
                .font(.system(size: 30, weight: .semibold))
                .contentTransition(.symbolEffect(.replace))
                .symbolEffect(.variableColor.iterative, isActive: voice.isListening)
                .frame(width: 84, height: 84)
                .foregroundStyle(voice.isListening ? .white : (enabled ? Theme.accent : .secondary))
                .glassEffect(.regular.tint(voice.isListening ? Color.red.opacity(0.6) : Theme.accent.opacity(0.14)).interactive(),
                             in: .circle)
                .scaleEffect(voice.isListening ? 1.1 : 1)
        }
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

/// Glass button with an icon and a caption under it.
struct QuickAction: View {
    let title: String
    let symbol: String
    let enabled: Bool
    let action: () -> Void
    @State private var taps = 0

    var body: some View {
        Button {
            taps += 1
            action()
        } label: {
            VStack(spacing: 6) {
                Image(systemName: symbol)
                    .font(.system(size: 21, weight: .semibold))
                    .symbolEffect(.bounce, value: taps)
                Text(title).font(.caption2.weight(.semibold)).fontWidth(.expanded)
            }
            .frame(width: 76, height: 62)
        }
        .buttonStyle(.glass)
        .buttonBorderShape(.roundedRectangle(radius: 22))
        .disabled(!enabled)
        .sensoryFeedback(.selection, trigger: taps)
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
