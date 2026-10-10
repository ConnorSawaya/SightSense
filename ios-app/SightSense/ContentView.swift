import ARKit
import SwiftUI

struct ContentView: View {
    @StateObject private var capture = Capture()
    @StateObject private var voice = Voice()
    @AppStorage("gx10Host") private var host = "192.168.8.10"
    @State private var typed = ""
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        ScrollView {
            VStack(spacing: 12) {
                connectRow
                if let problem = capture.problem ?? voice.problem {
                    Text(problem)
                        .foregroundStyle(.red)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                GuidanceBanner(message: capture.guidance, running: capture.isRunning)
                LiDARView(depth: capture.depthPreview, running: capture.isRunning)
                status
                commandRow
                talkButton
            }
            .padding()
        }
        .scrollDismissesKeyboard(.interactively)
        .onAppear {
            voice.requestPermission()
            // For testing: launch with `-autoconnect host[:port]` to connect straight away.
            let args = ProcessInfo.processInfo.arguments
            if let i = args.firstIndex(of: "-autoconnect"), i + 1 < args.count, !capture.isRunning {
                host = args[i + 1]
                capture.start(host: host)
            }
        }
        .onChange(of: scenePhase) { _, phase in
            if phase == .background, capture.isRunning { capture.stop() }
        }
    }

    private var connectRow: some View {
        HStack {
            TextField("GX10 address", text: $host)
                .textFieldStyle(.roundedBorder)
                .keyboardType(.numbersAndPunctuation)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .disabled(capture.isRunning)
            Button(capture.isRunning ? "Disconnect" : "Connect") {
                if capture.isRunning { capture.stop() } else { capture.start(host: host) }
            }
            .buttonStyle(.borderedProminent)
        }
    }

    private var status: some View {
        Grid(alignment: .leading, horizontalSpacing: 16, verticalSpacing: 6) {
            row("Link", capture.link)
            row("Tracking", capture.isRunning ? capture.stats.tracking : "—")
            row("Depth", capture.stats.depthSize ?? "—")
            row("Sending", capture.isRunning ? String(format: "%.1f frames/s", capture.sendRate) : "—")
            row("Sent / skipped", "\(capture.stats.sent) / \(capture.stats.skipped)")
            row("Encode / send", String(format: "%.0f ms / %.0f ms", capture.stats.lastEncodeMs, capture.stats.lastSendMs))
            if capture.stats.failed > 0 {
                row("Failed", "\(capture.stats.failed) (\(capture.stats.lastError ?? ""))")
            }
            row("From GX10", capture.lastMessage ?? "—")
        }
        .font(.callout.monospacedDigit())
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private var commandRow: some View {
        HStack {
            TextField("Type a command", text: $typed)
                .textFieldStyle(.roundedBorder)
                .submitLabel(.send)
                .onSubmit(sendTyped)
            Button("Send", action: sendTyped)
                .disabled(typed.trimmingCharacters(in: .whitespaces).isEmpty || !capture.isRunning)
        }
    }

    private var talkButton: some View {
        Text(voice.isListening ? (voice.heard.isEmpty ? "Listening…" : voice.heard) : "Hold to talk")
            .font(.title3.weight(.semibold))
            .multilineTextAlignment(.center)
            .frame(maxWidth: .infinity, minHeight: 88)
            .padding(.horizontal)
            .background(voice.isListening ? Color.red : Color.accentColor, in: RoundedRectangle(cornerRadius: 16))
            .foregroundStyle(.white)
            .opacity(capture.isRunning ? 1 : 0.4)
            .gesture(
                DragGesture(minimumDistance: 0)
                    .onChanged { _ in
                        guard capture.isRunning, !voice.isListening else { return }
                        voice.start { capture.send(command: $0) }
                    }
                    .onEnded { _ in voice.stop() }
            )
            .accessibilityLabel("Talk")
            .accessibilityHint("Hold and say a command, then let go")
            .accessibilityAddTraits(.isButton)
    }

    private func sendTyped() {
        let text = typed.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, capture.isRunning else { return }
        capture.send(command: text)
        typed = ""
    }

    private func row(_ label: String, _ value: String) -> some View {
        GridRow {
            Text(label).foregroundStyle(.secondary)
            Text(value).lineLimit(2)
        }
    }
}

/// The latest guidance state from the GX10, large enough for a sighted observer to read at a glance.
struct GuidanceBanner: View {
    let message: GX10Message?
    let running: Bool

    var body: some View {
        let state = message?.state ?? (running ? "NO_DATA" : "OFF")
        VStack(spacing: 4) {
            Text(state.replacingOccurrences(of: "_", with: " "))
                .font(.largeTitle.weight(.bold))
            if let speech = message?.speech {
                Text(speech).font(.headline)
            }
        }
        .frame(maxWidth: .infinity, minHeight: 80)
        .padding(.vertical, 8)
        .background(Self.color(state), in: RoundedRectangle(cornerRadius: 16))
        .foregroundStyle(.white)
        .accessibilityElement(children: .combine)
    }

    static func color(_ state: String) -> Color {
        switch state {
        case "CLEAR": return .green
        case "CAUTION": return .orange
        case "STOP": return .red
        case "UNCERTAIN": return .purple
        default: return .gray
        }
    }
}

/// LiDAR depth in colour (near red, far blue, no reading black) with the distance at the centre.
/// The camera picture is still sent to the GX10 for the vision-language model; it is just not shown.
struct LiDARView: View {
    @ObservedObject var depth: DepthPreview
    let running: Bool

    var body: some View {
        ZStack(alignment: .bottomLeading) {
            Color.black
            if let image = depth.image {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFill()
            }
            Rectangle()  // the patch the centre distance is measured over
                .stroke(.white, lineWidth: 2)
                .frame(width: 24, height: 24)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            Text(depth.centreMetres.map { String(format: "Centre %.2f m", $0) } ?? (running ? "No depth yet" : "Connect to start"))
                .font(.headline.monospacedDigit())
                .padding(.horizontal, 8).padding(.vertical, 4)
                .background(.black.opacity(0.6), in: Capsule())
                .foregroundStyle(.white)
                .padding(8)
        }
        .aspectRatio(3 / 4, contentMode: .fit)
        .frame(maxHeight: 400)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .accessibilityHidden(true)
    }
}
