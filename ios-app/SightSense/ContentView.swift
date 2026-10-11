import SwiftUI

struct ContentView: View {
    @StateObject private var capture = Capture()
    @StateObject private var voice = Voice()
    @AppStorage("gx10Host") private var host = Hosts.presets[0].address
    @AppStorage("recentHosts") private var recentRaw = ""
    @State private var showSettings = false
    @State private var resumeOnActive = false
    @Environment(\.scenePhase) private var scenePhase

    private var isStop: Bool { capture.guidance?.state == "STOP" }
    private var linkOpen: Bool { capture.isRunning && capture.linkState == .open }

    var body: some View {
        ZStack {
            Backdrop(state: capture.guidance?.state)

            VStack(spacing: 12) {
                topBar
                GuidanceCard(message: capture.guidance, running: capture.isRunning,
                             linkState: capture.linkState, depth: capture.depthPreview)
                if let problem = capture.problem ?? voice.problem {
                    Label(problem, systemImage: "exclamationmark.triangle.fill")
                        .font(.footnote.weight(.semibold))
                        .padding(.horizontal, 14).padding(.vertical, 8)
                        .glassEffect(.regular.tint(.red.opacity(0.3)), in: .capsule)
                        .transition(.move(edge: .top).combined(with: .opacity))
                }
                DepthStage(depth: capture.depthPreview, running: capture.isRunning,
                           linkState: capture.linkState, host: host, stats: capture.stats) { idleCard }
                dock
            }
            .padding(.horizontal, 16)
            .padding(.bottom, 4)
            .animation(.snappy, value: capture.problem ?? voice.problem)

            if isStop { StopGlow().transition(.opacity) }
        }
        .animation(.easeInOut(duration: 0.25), value: isStop)
        .preferredColorScheme(.dark)
        .tint(Theme.accent)
        .sensoryFeedback(trigger: capture.guidance?.state) { _, new in
            new == "STOP" ? .warning : nil
        }
        .sheet(isPresented: $showSettings) {
            SettingsSheet(capture: capture, host: $host, recentRaw: $recentRaw, connect: connect)
                .presentationDetents([.medium, .large])
                .presentationDragIndicator(.visible)
        }
        .onAppear {
            // For testing: launch with `-autoconnect host[:port]` to connect straight away.
            let args = ProcessInfo.processInfo.arguments
            if let i = args.firstIndex(of: "-autoconnect"), i + 1 < args.count, !capture.isRunning {
                connect(args[i + 1])
            }
            if args.contains("-settings") { showSettings = true }
            // The talk button on the cane: a press starts listening, as the button on the screen does.
            // Letting go after a hold stops it; after a click it stops by itself, or on a second click.
            let talker = voice, link = capture
            link.onListen = { [weak talker, weak link] on in
                guard let talker, let link else { return }
                if on, !talker.isListening {
                    talker.start(stopsItself: true) { [weak link] text in link?.send(command: text) }
                } else {
                    talker.stop()
                }
            }
        }
        .onChange(of: voice.isListening) { _, on in
            capture.talking(on)  // no speech over the user while they talk
        }
        .onChange(of: scenePhase) { _, phase in
            // Streaming stops in the background (iOS stops the camera anyway) and picks up again on return.
            if phase == .background, capture.isRunning {
                resumeOnActive = true
                capture.stop()
            } else if phase == .active, resumeOnActive {
                resumeOnActive = false
                connect(host)
            }
        }
    }

    // MARK: - Pieces

    private var topBar: some View {
        HStack {
            Button { showSettings = true } label: {
                Image(systemName: "gearshape.fill")
                    .font(.system(size: 18, weight: .semibold))
                    .frame(width: 44, height: 44)
            }
            .buttonStyle(.glass)
            .buttonBorderShape(.circle)
            .accessibilityLabel("Connection settings")

            Spacer()

            HStack(spacing: 8) {
            LogoMark()
                .frame(width: 28, height: 28)
                .clipShape(.rect(cornerRadius: 7))
            VStack(alignment: .leading, spacing: 1) {
                Text("SIGHTSENSE")
                    .font(.system(size: 13, weight: .heavy))
                    .fontWidth(.expanded)
                    .kerning(1.5)
                Text("LiDAR GUIDE")
                    .font(.system(size: 9, weight: .semibold))
                    .fontWidth(.expanded)
                    .kerning(1.5)
                    .foregroundStyle(Theme.accent)
            }
            }
            .lineLimit(1)
            .minimumScaleFactor(0.7)
            .accessibilityHidden(true)

            Spacer()

            Button { showSettings = true } label: {
                LinkCapsule(state: capture.linkState, rate: capture.sendRate, running: capture.isRunning)
                    .fixedSize()
            }
            .buttonStyle(.plain)
            .accessibilityHint("Opens connection settings")
        }
    }

    private var idleCard: some View {
        VStack(spacing: 20) {
            RadarPulse()
            VStack(spacing: 6) {
                Text("Ready to connect").font(.title2.weight(.semibold)).fontWidth(.expanded)
                Text("Streams LiDAR depth to the GX10 for guidance")
                    .font(.subheadline).foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }
            HStack(spacing: 12) {
                Image(systemName: Hosts.presets.first { $0.address == host }?.symbol ?? "server.rack")
                    .font(.body.weight(.semibold))
                    .foregroundStyle(Theme.accent)
                    .frame(width: 36, height: 36)
                    .background(Theme.accent.opacity(0.14), in: .circle)
                VStack(alignment: .leading, spacing: 2) {
                    Text(Hosts.name(for: host) ?? "GX10").font(.subheadline.weight(.semibold))
                    Text(host).font(.caption.monospaced()).foregroundStyle(.secondary)
                }
                Spacer(minLength: 0)
                Button { showSettings = true } label: {
                    Text("Change").font(.footnote.weight(.semibold))
                }
                .buttonStyle(.glass)
            }
            .padding(12)
            .glassEffect(.regular, in: .rect(cornerRadius: 20))

            Button { connect(host) } label: {
                Label("Connect", systemImage: "bolt.fill")
                    .font(.headline)
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.glassProminent)
            .controlSize(.extraLarge)
        }
        .padding(24)
        .frame(maxWidth: 420)
        .glassEffect(.regular, in: .rect(cornerRadius: 34))
    }

    /// Describe, talk and read, like the controls under a camera's shutter. What was heard floats above it while talking.
    private var dock: some View {
        VStack(spacing: 10) {
            if voice.isListening || !voice.heard.isEmpty {
                HStack(spacing: 8) {
                    Image(systemName: voice.isListening ? "waveform" : "quote.opening")
                        .symbolEffect(.variableColor.iterative, isActive: voice.isListening)
                        .foregroundStyle(voice.isListening ? .red : Theme.accent)
                    Text(voice.isListening && voice.heard.isEmpty ? "Listening…" : voice.heard)
                        .font(.callout.weight(.medium))
                        .lineLimit(2)
                        .contentTransition(.interpolate)
                }
                .padding(.horizontal, 16).padding(.vertical, 10)
                .glassEffect(.regular, in: .capsule)
                .transition(.move(edge: .bottom).combined(with: .blurReplace))
            }
            GlassEffectContainer(spacing: 20) {
            HStack(spacing: 0) {
                QuickAction(title: "Describe", symbol: "text.viewfinder", enabled: linkOpen) {
                    capture.send(command: "what's in front of me")
                }
                .frame(maxWidth: .infinity)
                TalkButton(voice: voice, enabled: linkOpen) { capture.send(command: $0) }
                    .offset(y: -6)
                QuickAction(title: "Read", symbol: "doc.text.viewfinder", enabled: linkOpen) {
                    capture.send(command: "read the sign")
                }
                .frame(maxWidth: .infinity)
            }
            }
        }
        .animation(.snappy, value: voice.isListening)
        .animation(.snappy, value: voice.heard.isEmpty)
    }

    private func connect(_ address: String) {
        let a = address.trimmingCharacters(in: .whitespacesAndNewlines)
        if capture.isRunning { capture.stop() }
        host = a
        recentRaw = Hosts.remember(a, in: recentRaw)
        capture.start(host: a)
    }
}

/// Saved GX10 addresses.
enum Hosts {
    struct Preset: Identifiable {
        let name: String
        let detail: String
        let address: String
        let symbol: String
        var id: String { address }
    }

    static let presets = [
        Preset(name: "GX10 over Tailscale", detail: "Frame service, works from any network", address: "100.108.5.67:8775", symbol: "network"),
        Preset(name: "GX10 on team router", detail: "Fastest, for the demo", address: "192.168.8.10:8775", symbol: "wifi.router"),
    ]

    static func name(for address: String) -> String? {
        presets.first { $0.address == address }?.name
    }

    static func recent(_ raw: String) -> [String] {
        raw.split(separator: "\n").map(String.init).filter { a in !presets.contains { $0.address == a } }
    }

    /// Newest first, at most 5, no duplicates.
    static func remember(_ address: String, in raw: String) -> String {
        guard !address.isEmpty else { return raw }
        let list = [address] + raw.split(separator: "\n").map(String.init).filter { $0 != address }
        return list.prefix(5).joined(separator: "\n")
    }
}
