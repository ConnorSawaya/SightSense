import SwiftUI

struct ContentView: View {
    @StateObject private var capture = Capture()
    @StateObject private var voice = Voice()
    @AppStorage("gx10Host") private var host = Hosts.presets[0].address
    @AppStorage("recentHosts") private var recentRaw = ""
    @State private var showSettings = false
    @Environment(\.scenePhase) private var scenePhase

    private var isStop: Bool { capture.guidance?.state == "STOP" }
    private var linkOpen: Bool { capture.isRunning && capture.linkState == .open }

    var body: some View {
        ZStack {
            DepthBackdrop(depth: capture.depthPreview)

            VStack(spacing: 12) {
                topBar
                GuidancePill(message: capture.guidance, running: capture.isRunning, linkState: capture.linkState)
                if let problem = capture.problem ?? voice.problem {
                    Label(problem, systemImage: "exclamationmark.triangle.fill")
                        .font(.footnote.weight(.semibold))
                        .padding(.horizontal, 14).padding(.vertical, 8)
                        .glassEffect(.regular.tint(.red.opacity(0.3)), in: .capsule)
                }
                DepthStage(depth: capture.depthPreview, running: capture.isRunning,
                           linkState: capture.linkState, host: host) { idleCard }
                if capture.isRunning { stats }
                transcript
                dock
            }
            .padding(.horizontal, 16)
            .padding(.bottom, 8)

            if isStop { StopGlow() }
        }
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
        }
        .onChange(of: scenePhase) { _, phase in
            if phase == .background, capture.isRunning { capture.stop() }
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

            VStack(spacing: 0) {
                Text("SIGHTSENSE")
                    .font(.system(size: 13, weight: .heavy))
                    .fontWidth(.expanded)
                    .kerning(3)
                Text("LiDAR").font(.caption2).foregroundStyle(.secondary)
            }
            .accessibilityHidden(true)

            Spacer()

            Button { showSettings = true } label: {
                LinkCapsule(state: capture.linkState, rate: capture.sendRate, running: capture.isRunning)
            }
            .buttonStyle(.plain)
            .accessibilityHint("Opens connection settings")
        }
    }

    private var idleCard: some View {
        VStack(spacing: 18) {
            Image(systemName: "dot.radiowaves.left.and.right")
                .font(.system(size: 40, weight: .light))
                .foregroundStyle(Theme.accent)
                .symbolEffect(.pulse)
            VStack(spacing: 6) {
                Text("Not connected").font(.title3.weight(.semibold)).fontWidth(.expanded)
                Text(Hosts.name(for: host) ?? "GX10")
                    .font(.subheadline).foregroundStyle(.secondary)
                Text(host).font(.footnote.monospaced()).foregroundStyle(.secondary)
            }
            HStack(spacing: 12) {
                Button { connect(host) } label: {
                    Label("Connect", systemImage: "bolt.fill").frame(minWidth: 110)
                }
                .buttonStyle(.glassProminent)
                Button { showSettings = true } label: {
                    Label("Change", systemImage: "slider.horizontal.3")
                }
                .buttonStyle(.glass)
            }
            .controlSize(.large)
        }
        .padding(28)
        .glassEffect(.regular, in: .rect(cornerRadius: 32))
    }

    private var stats: some View {
        GlassEffectContainer(spacing: 8) {
            HStack(spacing: 8) {
                StatChip(label: "Tracking", value: shortTracking,
                         tint: capture.stats.tracking == "Normal" ? nil : Theme.color(forState: "CAUTION"))
                StatChip(label: "Depth", value: capture.stats.depthSize?.replacingOccurrences(of: " ", with: "") ?? "—")
                StatChip(label: "Send", value: linkOpen ? String(format: "%.0f ms", capture.stats.lastSendMs) : "—")
            }
        }
    }

    private var shortTracking: String {
        let t = capture.stats.tracking
        return t.hasPrefix("Limited") ? "Limited" : t
    }

    @ViewBuilder private var transcript: some View {
        if voice.isListening || !voice.heard.isEmpty {
            Text(voice.isListening && voice.heard.isEmpty ? "Listening…" : "“\(voice.heard)”")
                .font(.callout.weight(.medium))
                .multilineTextAlignment(.center)
                .padding(.horizontal, 16).padding(.vertical, 10)
                .glassEffect(.regular, in: .capsule)
                .transition(.blurReplace)
        }
    }

    private var dock: some View {
        GlassEffectContainer(spacing: 24) {
            HStack(spacing: 24) {
                QuickAction(title: "Describe", symbol: "text.viewfinder", enabled: linkOpen) {
                    capture.send(command: "what's in front of me")
                }
                TalkButton(voice: voice, enabled: linkOpen) { capture.send(command: $0) }
                QuickAction(title: "Read", symbol: "doc.text.viewfinder", enabled: linkOpen) {
                    capture.send(command: "read the sign")
                }
            }
        }
        .animation(.snappy, value: voice.isListening)
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
        Preset(name: "GX10 over Tailscale", detail: "Works from any network", address: "100.108.5.67", symbol: "network"),
        Preset(name: "GX10 on team router", detail: "Fastest, for the demo", address: "192.168.8.10", symbol: "wifi.router"),
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
