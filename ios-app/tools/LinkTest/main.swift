// Runs the app's GX10Link and FrameMessage on a Mac against tools/fake_gx10.py.
// No ARKit: frames are synthetic (left half 1 m, right half 3 m, a few missing readings).
//
//   ./tools/run_link_test.sh            # builds this and runs it against the fake GX10
//   link-test ws://127.0.0.1:8765 60    # send 60 frames, check what comes back

import CoreImage
import CoreVideo
import Foundation

var failures = 0
func check(_ ok: Bool, _ what: String) {
    print(ok ? "ok   " : "FAIL ", what)
    if !ok { failures += 1 }
}

// ---------------------------------------------------------------- unit checks

check(FrameMessage.millimetres(1.0) == 1000, "1 m is 1000 mm")
check(FrameMessage.millimetres(0.3004) == 300, "0.3004 m rounds to 300 mm")
check(FrameMessage.millimetres(.nan) == 0, "NaN depth becomes 0")
check(FrameMessage.millimetres(.infinity) == 0, "infinite depth becomes 0")
check(FrameMessage.millimetres(-1) == 0, "negative depth becomes 0")
check(FrameMessage.millimetres(70) == 65535, "70 m clamps to 65535")

let k = FrameMessage.scaledIntrinsics(fx: 1600, fy: 1600, cx: 960, cy: 720,
                                      from: CGSize(width: 1920, height: 1440), toWidth: 256, height: 192)
check(abs(k.fx - 213.333) < 0.01 && abs(k.cx - 128) < 0.01 && abs(k.cy - 96) < 0.01, "intrinsics scale to 256x192")

let cols: [SIMD4<Float>] = [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]]
check(FrameMessage.pose(columns: cols) == (1...16).map(Double.init), "pose is column by column")

func makeBuffer(_ w: Int, _ h: Int, _ format: OSType) -> CVPixelBuffer {
    var buf: CVPixelBuffer?
    // Ask for padded rows so the row-stride handling is exercised.
    let attrs = [kCVPixelBufferBytesPerRowAlignmentKey: 256] as CFDictionary
    CVPixelBufferCreate(nil, w, h, format, attrs, &buf)
    return buf!
}

let dw = 256, dh = 192
let depthBuf = makeBuffer(dw, dh, kCVPixelFormatType_DepthFloat32)
let confBuf = makeBuffer(dw, dh, kCVPixelFormatType_OneComponent8)
CVPixelBufferLockBaseAddress(depthBuf, [])
CVPixelBufferLockBaseAddress(confBuf, [])
let dRow = CVPixelBufferGetBytesPerRow(depthBuf), cRow = CVPixelBufferGetBytesPerRow(confBuf)
for y in 0..<dh {
    let d = CVPixelBufferGetBaseAddress(depthBuf)!.advanced(by: y * dRow).assumingMemoryBound(to: Float32.self)
    let c = CVPixelBufferGetBaseAddress(confBuf)!.advanced(by: y * cRow).assumingMemoryBound(to: UInt8.self)
    for x in 0..<dw {
        d[x] = x % 50 == 0 ? .nan : (x < dw / 2 ? 1.0 : 3.0)
        c[x] = UInt8((x + y) % 3)
    }
}
CVPixelBufferUnlockBaseAddress(depthBuf, [])
CVPixelBufferUnlockBaseAddress(confBuf, [])
print("     depth rows \(dRow) bytes for \(dw * 4) bytes of data (padded: \(dRow > dw * 4))")

let depth = FrameMessage.depthMillimetres(depthBuf)!
let conf = FrameMessage.confidenceBytes(confBuf)!
check(depth.width == dw && depth.height == dh && depth.data.count == dw * dh * 2, "depth is 256x192 UInt16")
func mm(_ x: Int, _ y: Int) -> UInt16 {
    let i = (y * dw + x) * 2
    return UInt16(depth.data[i]) | UInt16(depth.data[i + 1]) << 8  // little-endian
}
check(mm(10, 100) == 1000 && mm(201, 100) == 3000 && mm(0, 5) == 0 && mm(255, 191) == 3000, "depth values and row order")
check(conf.count == dw * dh && conf[5 * dw + 7] == UInt8((7 + 5) % 3), "confidence values and row order")
check(FrameMessage.depthMillimetres(confBuf) == nil, "wrong pixel format is refused")

// Rows with padding at the end: 250 floats in rows rounded up to 1024 bytes.
let odd = makeBuffer(250, 4, kCVPixelFormatType_DepthFloat32)
CVPixelBufferLockBaseAddress(odd, [])
let oddRow = CVPixelBufferGetBytesPerRow(odd)
for y in 0..<4 {
    let d = CVPixelBufferGetBaseAddress(odd)!.advanced(by: y * oddRow).assumingMemoryBound(to: Float32.self)
    for x in 0..<250 { d[x] = Float32(y + 1) + Float32(x) / 1000 }
}
CVPixelBufferUnlockBaseAddress(odd, [])
let oddMM = FrameMessage.depthMillimetres(odd)!.data
let at = { (x: Int, y: Int) -> UInt16 in UInt16(oddMM[(y * 250 + x) * 2]) | UInt16(oddMM[(y * 250 + x) * 2 + 1]) << 8 }
check(oddRow > 1000 && oddMM.count == 250 * 4 * 2 && at(0, 2) == 3000 && at(249, 3) == 4249, "padded rows are skipped (\(oddRow) bytes per row)")

// A real JPEG, 640x480.
let ci = CIContext()
let picture = CIImage(color: CIColor(red: 0.2, green: 0.5, blue: 0.8)).cropped(to: CGRect(x: 0, y: 0, width: 640, height: 480))
let jpeg = ci.jpegRepresentation(of: picture, colorSpace: CGColorSpace(name: CGColorSpace.sRGB)!, options: [:])!

func frame(_ seq: Int) throws -> Data {
    let header: [String: Any] = [
        "seq": seq, "t_capture": ProcessInfo.processInfo.systemUptime,
        "rgb_w": 640, "rgb_h": 480, "depth_w": dw, "depth_h": dh,
        "fx": k.fx, "fy": k.fy, "cx": k.cx, "cy": k.cy,
        "pose": FrameMessage.pose(columns: cols), "tracking": "normal",
        "lat": NSNull(), "lon": NSNull(), "gps_acc_m": NSNull(), "heading_deg": NSNull(),
        "thermal": FrameMessage.thermalName(.nominal),
    ]
    return try FrameMessage.pack(header: header, jpeg: jpeg, depth: depth.data, confidence: conf)
}

let sample = try frame(1)
let hlen = Int(sample[0]) | Int(sample[1]) << 8 | Int(sample[2]) << 16 | Int(sample[3]) << 24
let parsed = try JSONSerialization.jsonObject(with: sample[4..<(4 + hlen)]) as! [String: Any]
check(parsed["jpeg_len"] as? Int == jpeg.count && parsed["depth_len"] as? Int == dw * dh * 2
      && parsed["conf_len"] as? Int == dw * dh, "header lengths match the parts")
check(sample.count == 4 + hlen + jpeg.count + dw * dh * 3, "message is header + JPEG + depth + confidence")
check(parsed["lat"] is NSNull, "missing GPS is JSON null")
print("     one frame is \(sample.count / 1024) KB (JPEG \(jpeg.count / 1024) KB, depth \(dw * dh * 2 / 1024) KB, confidence \(dw * dh / 1024) KB)")

// ---------------------------------------------------------------- live link

let args = CommandLine.arguments
guard args.count >= 3, let url = URL(string: args[1]), let count = Int(args[2]) else {
    print(failures == 0 ? "unit checks passed (pass URL and frame count to test the link)" : "\(failures) failed")
    exit(failures == 0 ? 0 : 1)
}
let reconnect = args.count >= 4 && args[3] == "reconnect"

let link = GX10Link()
let states = NSMutableArray()
let texts = NSMutableArray()
let opened = DispatchSemaphore(value: 0)
link.onState = { state, why in
    print("     link:", state.rawValue, why ?? "")
    states.add(state.rawValue)
    if state == .open { opened.signal() }
}
link.onText = { text in texts.add(text) }

link.connect(to: url)
check(opened.wait(timeout: .now() + 5) == .success, "link opens")

// Send like the app: one in flight, about 15 a second.
var sent = 0, failedSends = 0
let start = Date()
var sendTimes: [Double] = []
for seq in 1...count {
    let data = try frame(seq)
    let done = DispatchSemaphore(value: 0)
    let t0 = Date()
    var ok = false
    link.send(data) { ok = $0; done.signal() }
    done.wait()
    sendTimes.append(Date().timeIntervalSince(t0) * 1000)
    if ok { sent += 1 } else { failedSends += 1 }
    if seq == 10 { link.sendText(#"{"text": "guide me to the apple"}"#) }  // what Capture.send(command:) sends
    Thread.sleep(forTimeInterval: max(0, Double(seq) / 15 - Date().timeIntervalSince(start)))
}
let elapsed = Date().timeIntervalSince(start)
sendTimes.sort()
print(String(format: "     %d frames in %.1f s (%.1f/s), send median %.1f ms, worst %.1f ms",
             sent, elapsed, Double(sent) / elapsed, sendTimes[sendTimes.count / 2], sendTimes.last!))
check(sent >= count - 1 && failedSends <= 1, "frames sent (\(sent) ok, \(failedSends) failed)")

Thread.sleep(forTimeInterval: 0.5)
check(texts.count >= Int(elapsed / 2) - 1, "guidance received (\(texts.count) messages)")
if let first = texts.firstObject as? String,
   let g = try? JSONSerialization.jsonObject(with: Data(first.utf8)) as? [String: Any] {
    check(g["state"] is String, "guidance has a state: \(first)")
}

if reconnect {
    // The fake GX10 closes after its frame count and is restarted by the script; the link must come back.
    print("     waiting for the fake GX10 to restart ...")
    let deadline = Date().addingTimeInterval(15)
    var back = false
    while Date() < deadline {
        if link.isOpen && (states.contains("Retrying")) { back = true; break }
        Thread.sleep(forTimeInterval: 0.2)
    }
    check(back, "link reconnects by itself after the GX10 drops")
    if back {
        let done = DispatchSemaphore(value: 0)
        var ok = false
        link.send(try frame(count + 1)) { ok = $0; done.signal() }
        done.wait()
        check(ok, "sends again after reconnecting")
    }
}

link.disconnect()
Thread.sleep(forTimeInterval: 0.3)
check(!link.isOpen, "disconnect closes the link")
print(failures == 0 ? "all checks passed" : "\(failures) checks FAILED")
exit(failures == 0 ? 0 : 1)
