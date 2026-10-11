import Foundation

/// WebSocket to the GX10 on port 8765. Reconnects by itself until `disconnect()`.
/// Frames go out as binary messages; guidance comes back as text.
final class GX10Link: NSObject, URLSessionWebSocketDelegate {
    enum State: String {
        case idle = "Not connected"
        case connecting = "Connecting"
        case open = "Connected"
        case retrying = "Retrying"
    }

    /// Called on a background queue.
    var onState: ((State, String?) -> Void)?
    /// Called on a background queue with each text message from the GX10.
    var onText: ((String) -> Void)?

    static let connectTimeout: TimeInterval = 3
    static let retryDelay: TimeInterval = 1

    // Everything below is touched only on `queue`.
    private let queue = DispatchQueue(label: "gx10.link")
    private lazy var session: URLSession = {
        let ops = OperationQueue()
        ops.underlyingQueue = queue
        ops.maxConcurrentOperationCount = 1
        return URLSession(configuration: .ephemeral, delegate: self, delegateQueue: ops)
    }()
    private var task: URLSessionWebSocketTask?
    private var url: URL?
    private var wanted = false
    private var isOpenLocked = false
    private let openLock = NSLock()

    var isOpen: Bool { openLock.withLock { isOpenLocked } }

    func connect(to url: URL) {
        queue.async {
            self.wanted = true
            self.url = url
            self.task?.cancel(with: .goingAway, reason: nil)
            self.task = nil
            self.open()
        }
    }

    func disconnect() {
        queue.async {
            self.wanted = false
            self.task?.cancel(with: .goingAway, reason: nil)
            self.task = nil
            self.setOpen(false)
            self.onState?(.idle, nil)
        }
    }

    /// Sends one binary message. `done(true)` once it has been handed to the network.
    func send(_ data: Data, done: @escaping (Bool) -> Void) {
        queue.async {
            guard let task = self.task, self.isOpen else { return done(false) }
            task.send(.data(data)) { error in done(error == nil) }
        }
    }

    func sendText(_ text: String) {
        queue.async {
            guard let task = self.task, self.isOpen else { return }
            task.send(.string(text)) { _ in }
        }
    }

    // MARK: - Private, on `queue`

    private func open() {
        guard wanted, let url else { return }
        let t = session.webSocketTask(with: url)
        t.maximumMessageSize = 4 << 20
        task = t
        onState?(.connecting, nil)
        t.resume()
        receive(t)
        queue.asyncAfter(deadline: .now() + Self.connectTimeout) { [weak self, weak t] in
            guard let self, let t, t === self.task, !self.isOpen else { return }
            t.cancel(with: .goingAway, reason: nil)  // no answer: give up and retry
        }
    }

    private func receive(_ t: URLSessionWebSocketTask) {
        t.receive { [weak self] result in
            guard let self else { return }
            switch result {
            case .success(.string(let text)):
                self.onText?(text)
            case .success(.data(let data)):
                if let text = String(data: data, encoding: .utf8) { self.onText?(text) }
            case .success:
                break
            case .failure:
                return  // the delegate reports the close and retries
            }
            self.receive(t)
        }
    }

    private func dropped(_ t: URLSessionTask, why: String?) {
        guard t === task else { return }
        task = nil
        setOpen(false)
        guard wanted else { return }
        onState?(.retrying, why)
        queue.asyncAfter(deadline: .now() + Self.retryDelay) { [weak self] in
            guard let self, self.wanted, self.task == nil else { return }
            self.open()
        }
    }

    private func setOpen(_ value: Bool) {
        openLock.withLock { isOpenLocked = value }
    }

    // MARK: - URLSessionWebSocketDelegate (delivered on `queue`)

    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didOpenWithProtocol protocol: String?) {
        guard webSocketTask === task else { return }
        setOpen(true)
        onState?(.open, nil)
    }

    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask,
                    didCloseWith closeCode: URLSessionWebSocketTask.CloseCode, reason: Data?) {
        dropped(webSocketTask, why: "closed by GX10")
    }

    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        dropped(task, why: error.map { ($0 as NSError).localizedDescription })
    }
}
