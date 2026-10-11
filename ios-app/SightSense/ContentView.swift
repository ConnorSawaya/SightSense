import SwiftUI

/// Full-screen LiDAR feed with only a settings gear, a status dot and the talk button on top.
/// Guidance shows as a glowing screen edge, beeps, speech and vibration. Everything else the
/// app used to show (guidance text, distance, stats, Describe/Read) is on the GX10 dashboard.
struct ContentView: View {
    @StateObject private var capture = Capture()
    @StateObject private var voice = Voice()
    @AppStorage("gx10Host") private var host = Hosts.presets[0].address
    @AppStorage("recentHosts") private var recentRaw = ""
    @State private var showSettings = false
    @State private var resumeOnActive = false
    @Environment(\.scenePhase) private var scenePhase

    private var linkOpen: Bool { capture.isRunning && capture.linkState == .open }
    private var isHot: Bool { capture.isRunning && capture.stats.thermal.rawValue >= ProcessInfo.ThermalState.serious.rawValue }

    var body: some View {
        ZStack {
            LiDARFeed(depth: capture.depthPreview, running: capture.isRunning)

            if !capture.isRunning {
                idleCard.padding(.horizontal, 24)
            } else if capture.depthPreview.image == nil {
                ProgressView().tint(Theme.accent).controlSize(.large)
            }

            StateEdge(state: capture.isRunning ? capture.guidance?.state : nil)

            VStack(spacing: 10) {
                topBar
                if let problem = capture.problem ?? voice.problem {
                    Label(problem, systemImage: "exclamationmark.triangle.fill")
                        .font(.footnote.weight(.semibold))
                        .padding(.horizontal, 14).padding(.vertical, 8)
                        .glassEffect(.regular.tint(.red.opacity(0.3)), in: .capsule)
                }
                if capture.isRunning && !linkOpen {
                    Label(capture.linkState == .retrying ? "Reconnecting to the GX10" : "Connecting to the GX10",
                          systemImage: "antenna.radiowaves.left.and.right")
                        .font(.footnote.weight(.semibold))
                        .padding(.horizontal, 14).padding(.vertical, 8)
                        .glassEffect(.regular, in: .capsule)
                }
                Spacer()
                transcript
                if capture.isRunning {
                    TalkButton(voice: voice, enabled: linkOpen) { capture.send(command: $0) }
                }
            }
            .padding(.horizontal, 16)
            .padding(.bottom, 12)
        }
        .preferredColorScheme(.dark)
        .tint(Theme.accent)
        .animation(.snappy, value: voice.isListening)
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

            Button { showSettings = true } label: {
                HStack(spacing: 6) {
                    if isHot {
                        Image(systemName: "thermometer.high")
                            .font(.system(size: 13, weight: .bold))
                            .foregroundStyle(Theme.color(forState: "CAUTION"))
                    }
                    StatusDot(state: capture.linkState)
                }
                .frame(minWidth: 44, minHeight: 44)
                .padding(.horizontal, isHot ? 8 : 0)
                .glassEffect(.regular, in: .capsule)
            }
            .buttonStyle(.plain)
            .accessibilityLabel("GX10 \(capture.linkState.rawValue)" + (isHot ? ", phone is hot" : ""))
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
