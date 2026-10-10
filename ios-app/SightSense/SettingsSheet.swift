import SwiftUI

/// Connection settings: pick or type the GX10 address, connect, and see what the link is doing.
struct SettingsSheet: View {
    @ObservedObject var capture: Capture
    @Binding var host: String
    @Binding var recentRaw: String
    let connect: (String) -> Void

    @State private var draft = ""
    @State private var command = ""
    @FocusState private var addressFocused: Bool
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    addressCard
                    if capture.isRunning || capture.linkState != .idle { linkCard }
                    commandCard
                    if let last = capture.lastMessage { lastMessageCard(last) }
                }
                .padding(16)
            }
            .scrollDismissesKeyboard(.interactively)
            .navigationTitle("Connection")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button(role: .close) { dismiss() }
                }
            }
        }
        .onAppear { draft = host }
    }

    // MARK: - Cards

    private var addressCard: some View {
        Card(title: "GX10 address") {
            HStack(spacing: 10) {
                Image(systemName: "server.rack").foregroundStyle(Theme.accent)
                TextField("100.108.5.67 or host:port", text: $draft)
                    .font(.body.monospaced())
                    .keyboardType(.numbersAndPunctuation)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .focused($addressFocused)
                    .submitLabel(.go)
                    .onSubmit { connectDraft() }
                if !draft.isEmpty {
                    Button { draft = "" } label: { Image(systemName: "xmark.circle.fill") }
                        .foregroundStyle(.secondary)
                        .accessibilityLabel("Clear address")
                }
            }
            .padding(12)
            .background(.white.opacity(0.06), in: RoundedRectangle(cornerRadius: 14))

            VStack(spacing: 8) {
                ForEach(Hosts.presets) { p in
                    HostRow(symbol: p.symbol, title: p.name, address: p.address, detail: p.detail,
                            selected: draft == p.address) { draft = p.address }
                }
                ForEach(Hosts.recent(recentRaw), id: \.self) { a in
                    HostRow(symbol: "clock.arrow.circlepath", title: "Recent", address: a, detail: nil,
                            selected: draft == a) { draft = a }
                }
            }

            if capture.isRunning && draft == host {
                Button(role: .destructive) { capture.stop() } label: {
                    Label("Disconnect", systemImage: "bolt.slash.fill").frame(maxWidth: .infinity)
                }
                .buttonStyle(.glass)
                .controlSize(.large)
            } else {
                Button { connectDraft() } label: {
                    Label(capture.isRunning ? "Switch to this address" : "Connect", systemImage: "bolt.fill")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.glassProminent)
                .controlSize(.large)
                .disabled(draft.trimmingCharacters(in: .whitespaces).isEmpty)
            }
        }
    }

    private var linkCard: some View {
        Card(title: "Link") {
            HStack(spacing: 10) {
                Circle().fill(Theme.color(forLink: capture.linkState)).frame(width: 10, height: 10)
                Text(capture.linkState.rawValue).font(.headline)
                Spacer()
                Text(host).font(.footnote.monospaced()).foregroundStyle(.secondary)
            }
            if let detail = capture.linkDetail {
                Text(detail)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .textSelection(.enabled)
            }
            Divider().opacity(0.3)
            Grid(alignment: .leading, horizontalSpacing: 16, verticalSpacing: 8) {
                row("Sending", String(format: "%.1f frames/s", capture.sendRate))
                row("Sent / skipped", "\(capture.stats.sent) / \(capture.stats.skipped)")
                row("Encode / send", String(format: "%.0f ms / %.0f ms", capture.stats.lastEncodeMs, capture.stats.lastSendMs))
                row("Depth", capture.stats.depthSize ?? "—")
                row("Tracking", capture.stats.tracking)
                if capture.stats.failed > 0 {
                    row("Failed", "\(capture.stats.failed) · \(capture.stats.lastError ?? "")")
                }
            }
            .font(.callout.monospacedDigit())
        }
    }

    private var commandCard: some View {
        Card(title: "Send a command") {
            HStack(spacing: 10) {
                TextField("guide me to the apple", text: $command)
                    .submitLabel(.send)
                    .onSubmit(sendCommand)
                Button(action: sendCommand) { Image(systemName: "arrow.up.circle.fill").font(.title2) }
                    .disabled(command.trimmingCharacters(in: .whitespaces).isEmpty || capture.linkState != .open)
                    .accessibilityLabel("Send command")
            }
            .padding(12)
            .background(.white.opacity(0.06), in: RoundedRectangle(cornerRadius: 14))
            if capture.linkState != .open {
                Text("Connect first. Same as holding the talk button.")
                    .font(.footnote).foregroundStyle(.secondary)
            }
        }
    }

    private func lastMessageCard(_ text: String) -> some View {
        Card(title: "Last message from GX10") {
            Text(text)
                .font(.footnote.monospaced())
                .frame(maxWidth: .infinity, alignment: .leading)
                .textSelection(.enabled)
        }
    }

    // MARK: - Helpers

    private func connectDraft() {
        let a = draft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !a.isEmpty else { return }
        addressFocused = false
        connect(a)
    }

    private func sendCommand() {
        let text = command.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, capture.linkState == .open else { return }
        capture.send(command: text)
        command = ""
    }

    private func row(_ label: String, _ value: String) -> some View {
        GridRow {
            Text(label).foregroundStyle(.secondary)
            Text(value).lineLimit(3)
        }
    }
}

/// A titled section in the sheet.
private struct Card<Content: View>: View {
    let title: String
    @ViewBuilder let content: () -> Content

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Theme.label(title)
            content()
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.white.opacity(0.05), in: RoundedRectangle(cornerRadius: 22))
        .overlay(RoundedRectangle(cornerRadius: 22).strokeBorder(.white.opacity(0.1), lineWidth: 1))
    }
}

/// A full-width, tappable address row.
private struct HostRow: View {
    let symbol: String
    let title: String
    let address: String
    let detail: String?
    let selected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Image(systemName: symbol)
                    .font(.system(size: 16, weight: .semibold))
                    .frame(width: 36, height: 36)
                    .background(Theme.accent.opacity(selected ? 0.25 : 0.1), in: Circle())
                    .foregroundStyle(Theme.accent)
                VStack(alignment: .leading, spacing: 2) {
                    Text(title).font(.subheadline.weight(.semibold)).foregroundStyle(.primary)
                    Text(address).font(.caption.monospaced()).foregroundStyle(Theme.accent.opacity(0.9))
                    if let detail {
                        Text(detail).font(.caption2).foregroundStyle(.secondary)
                    }
                }
                Spacer()
                if selected {
                    Image(systemName: "checkmark.circle.fill").foregroundStyle(Theme.accent)
                }
            }
            .padding(10)
            .background(.white.opacity(selected ? 0.08 : 0.03), in: RoundedRectangle(cornerRadius: 16))
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityAddTraits(selected ? .isSelected : [])
    }
}
