#!/usr/bin/env bash
# Build a distributable macOS DMG with a standalone Sage Mate app.

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
dist_dir="$repo_root/dist"
package_name="sage-mate-macos"
volume_name="Sage Mate"
build_zip=false
work_dir=$(mktemp -d "${TMPDIR:-/tmp}/${package_name}.XXXXXX")
app_version=$(sed -n 's/^version = "\([^"]*\)"/\1/p' "$repo_root/pyproject.toml" | head -n 1)
if [[ -z "$app_version" ]]; then
    echo "Could not read project version from pyproject.toml" >&2
    exit 1
fi

cleanup() {
    rm -rf "$work_dir"
}
trap cleanup EXIT

for arg in "$@"; do
    case "$arg" in
        --zip) build_zip=true ;;
        -h|--help)
            cat <<'EOF'
Usage: tools/build_macos_local_code_package.sh [--zip]

Builds dist/sage-mate-macos.dmg for macOS users.
Pass --zip to also build a zip fallback.
EOF
            exit 0
            ;;
        *) echo "Unknown argument: $arg" >&2; exit 2 ;;
    esac
done

mkdir -p "$dist_dir"

payload_dir="$work_dir/payload/faculty-twin"
mkdir -p "$payload_dir"

rsync -a \
    --exclude '.git' \
    --exclude '.env' \
    --exclude '.venv' \
    --exclude '.venv311' \
    --exclude '.pytest_cache' \
    --exclude '.runtime' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude 'dist' \
    --exclude 'build' \
    --exclude 'logs' \
    --exclude 'data' \
    --exclude 'data.pre_recovery_*' \
    --exclude '*.egg-info' \
    "$repo_root/" "$payload_dir/"

chmod +x "$payload_dir/tools/install_local_code_mode.sh"
chmod +x "$payload_dir/tools/build_macos_local_code_package.sh"

app_name="Sage Mate.app"
app_dir="$work_dir/$package_name/$app_name"
app_contents="$app_dir/Contents"
app_macos="$app_contents/MacOS"
app_resources="$app_contents/Resources"
mkdir -p "$app_macos" "$app_resources"
mkdir -p "$work_dir/$package_name"

cat > "$app_contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>en</string>
  <key>CFBundleDisplayName</key>
  <string>Sage Mate</string>
  <key>CFBundleExecutable</key>
  <string>SageMate</string>
  <key>CFBundleIconFile</key>
  <string>SageMate</string>
  <key>CFBundleIdentifier</key>
  <string>ai.sage.mate</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundleName</key>
  <string>Sage Mate</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>$app_version</string>
  <key>CFBundleVersion</key>
  <string>$app_version</string>
  <key>LSMinimumSystemVersion</key>
  <string>12.0</string>
  <key>NSAppTransportSecurity</key>
  <dict>
    <key>NSAllowsLocalNetworking</key>
    <true/>
  </dict>
</dict>
</plist>
EOF

iconset="$work_dir/SageMate.iconset"
mkdir -p "$iconset"
python3 - "$iconset" <<'PY'
from __future__ import annotations

import struct
import sys
import zlib
from pathlib import Path

iconset = Path(sys.argv[1])
targets = {
    "icon_16x16.png": 16,
    "icon_16x16@2x.png": 32,
    "icon_32x32.png": 32,
    "icon_32x32@2x.png": 64,
    "icon_128x128.png": 128,
    "icon_128x128@2x.png": 256,
    "icon_256x256.png": 256,
    "icon_256x256@2x.png": 512,
    "icon_512x512.png": 512,
    "icon_512x512@2x.png": 1024,
}


def chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def write_png(path: Path, size: int) -> None:
    rows: list[bytes] = []
    radius = size * 0.22
    for y in range(size):
        row = bytearray()
        for x in range(size):
            # Rounded-square alpha mask.
            cx = min(x, size - 1 - x)
            cy = min(y, size - 1 - y)
            alpha = 255
            if cx < radius and cy < radius:
                dx = radius - cx
                dy = radius - cy
                if dx * dx + dy * dy > radius * radius:
                    alpha = 0

            # Subtle teal-to-indigo gradient.
            t = (x + y) / max(1, 2 * (size - 1))
            r = int(18 + 34 * t)
            g = int(132 - 48 * t)
            b = int(142 + 72 * t)

            # Block "F" and "T" marks.
            white = False
            fx0, fx1 = int(size * 0.22), int(size * 0.43)
            tx0, tx1 = int(size * 0.54), int(size * 0.80)
            top, mid, bottom = int(size * 0.25), int(size * 0.47), int(size * 0.74)
            stroke = max(2, int(size * 0.055))
            if fx0 <= x <= fx0 + stroke and top <= y <= bottom:
                white = True
            if fx0 <= x <= fx1 and top <= y <= top + stroke:
                white = True
            if fx0 <= x <= int(size * 0.39) and mid <= y <= mid + stroke:
                white = True
            if tx0 <= x <= tx1 and top <= y <= top + stroke:
                white = True
            if int(size * 0.65) <= x <= int(size * 0.65) + stroke and top <= y <= bottom:
                white = True
            if white and alpha:
                r, g, b = 245, 250, 255
            row.extend((r, g, b, alpha))
        rows.append(b"\x00" + bytes(row))

    raw = b"".join(rows)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(png)


for filename, size in targets.items():
    write_png(iconset / filename, size)
PY

if command -v iconutil >/dev/null 2>&1; then
    iconutil -c icns "$iconset" -o "$app_resources/SageMate.icns"
else
    echo "iconutil not found; app will use the default macOS app icon." >&2
fi

rsync -a "$payload_dir/" "$app_resources/faculty-twin/"

cat > "$work_dir/SageMateApp.swift" <<'EOF'
import Cocoa
import WebKit

final class AppDelegate: NSObject, NSApplicationDelegate, NSWindowDelegate, WKNavigationDelegate {
    private var window: NSWindow!
    private var webView: WKWebView!
    private var statusLabel: NSTextField!
    private var serverProcess: Process?
    private let port = 55601
    private lazy var launcherLogURL: URL = {
        let root = (try? supportRoot()) ?? FileManager.default.homeDirectoryForCurrentUser
        return root.appendingPathComponent("launcher.log")
    }()

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        log("Application launched")
        buildWindow()
        showMainWindow()

        DispatchQueue.global(qos: .userInitiated).async {
            do {
                try self.prepareInstallIfNeeded()
                try self.startServer()
                self.waitForServer()
            } catch {
                self.log("Startup failed: \(error)")
                self.showStatus("启动失败：\(error.localizedDescription)")
            }
        }
    }

    func applicationWillTerminate(_ notification: Notification) {
        log("Application terminating")
        serverProcess?.terminate()
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        showMainWindow()
        return true
    }

    func applicationDidBecomeActive(_ notification: Notification) {
        if window == nil || !window.isVisible {
            showMainWindow()
        }
    }

    func windowShouldClose(_ sender: NSWindow) -> Bool {
        sender.orderOut(nil)
        return false
    }

    private func buildWindow() {
        if window != nil {
            return
        }

        let config = WKWebViewConfiguration()
        webView = WKWebView(frame: .zero, configuration: config)
        webView.navigationDelegate = self

        statusLabel = NSTextField(labelWithString: "正在启动 Sage Mate...")
        statusLabel.alignment = .center
        statusLabel.font = NSFont.systemFont(ofSize: 15, weight: .medium)

        let container = NSView()
        container.wantsLayer = true
        container.layer?.backgroundColor = NSColor.windowBackgroundColor.cgColor
        container.addSubview(webView)
        container.addSubview(statusLabel)
        webView.translatesAutoresizingMaskIntoConstraints = false
        statusLabel.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            webView.leadingAnchor.constraint(equalTo: container.leadingAnchor),
            webView.trailingAnchor.constraint(equalTo: container.trailingAnchor),
            webView.topAnchor.constraint(equalTo: container.topAnchor),
            webView.bottomAnchor.constraint(equalTo: container.bottomAnchor),
            statusLabel.centerXAnchor.constraint(equalTo: container.centerXAnchor),
            statusLabel.centerYAnchor.constraint(equalTo: container.centerYAnchor),
        ])
        webView.isHidden = true

        window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 1180, height: 820),
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered,
            defer: false
        )
        window.title = "Sage Mate"
        window.center()
        window.contentView = container
        window.delegate = self
    }

    private func showMainWindow() {
        if window == nil {
            buildWindow()
        }
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    private func supportRoot() throws -> URL {
        let base = try FileManager.default.url(
            for: .applicationSupportDirectory,
            in: .userDomainMask,
            appropriateFor: nil,
            create: true
        )
        let root = base.appendingPathComponent("Sage Mate", isDirectory: true)
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        return root
    }

    private func installRoot() throws -> URL {
        try supportRoot().appendingPathComponent("app", isDirectory: true)
    }

    private func runtimeRoot() throws -> URL {
        let fm = FileManager.default
        let home = fm.homeDirectoryForCurrentUser
        let candidates = [
            home.appendingPathComponent("Documents/sage-faculty-twin-runtime-private", isDirectory: true),
            home.appendingPathComponent("sage-faculty-twin-runtime-private", isDirectory: true),
            home.appendingPathComponent("Documents/qixin-gaoke-sage-faculty-twin-runtime-private", isDirectory: true),
            home.appendingPathComponent("qixin-gaoke-sage-faculty-twin-runtime-private", isDirectory: true)
        ]
        for candidate in candidates {
            let dataDir = candidate.appendingPathComponent("data", isDirectory: true)
            let gitDir = candidate.appendingPathComponent(".git", isDirectory: true)
            if fm.fileExists(atPath: dataDir.path) || fm.fileExists(atPath: gitDir.path) {
                log("Using existing runtime repository: \(candidate.path)")
                return candidate
            }
        }
        return try supportRoot().appendingPathComponent("runtime", isDirectory: true)
    }

    private func prepareInstallIfNeeded() throws {
        showStatus("正在准备本地应用文件...")
        let fm = FileManager.default
        let target = try installRoot()
        let marker = target.appendingPathComponent("pyproject.toml")
        log("Preparing install root: \(target.path)")
        if !fm.fileExists(atPath: marker.path) {
            if fm.fileExists(atPath: target.path) {
                log("Removing incomplete install root")
                try fm.removeItem(at: target)
            }
            guard let source = Bundle.main.resourceURL?.appendingPathComponent("faculty-twin", isDirectory: true) else {
                throw NSError(domain: "SageMate", code: 1, userInfo: [NSLocalizedDescriptionKey: "应用包缺少 faculty-twin 资源。"])
            }
            guard fm.fileExists(atPath: source.path) else {
                throw NSError(domain: "SageMate", code: 2, userInfo: [NSLocalizedDescriptionKey: "应用包里的 faculty-twin 资源不存在。"])
            }
            log("Copying bundled source from \(source.path)")
            try fm.createDirectory(at: target.deletingLastPathComponent(), withIntermediateDirectories: true)
            try fm.copyItem(at: source, to: target)
            log("Bundled source copied")
            try runShell([
                "/bin/chmod",
                "+x",
                target.appendingPathComponent("tools/install_local_code_mode.sh").path,
                target.appendingPathComponent("tools/run_app_server.sh").path
            ], cwd: target, logName: "chmod.log")
        } else {
            log("Existing install root found")
            guard let source = Bundle.main.resourceURL?.appendingPathComponent("faculty-twin", isDirectory: true) else {
                throw NSError(domain: "SageMate", code: 3, userInfo: [NSLocalizedDescriptionKey: "应用包缺少 faculty-twin 资源。"])
            }
            try runShell([
                "/usr/bin/rsync",
                "-a",
                "--delete",
                "--exclude", ".env",
                "--exclude", ".venv",
                "--exclude", ".runtime",
                source.path + "/",
                target.path + "/"
            ], cwd: target, logName: "sync.log")
            try runShell([
                "/bin/chmod",
                "+x",
                target.appendingPathComponent("tools/install_local_code_mode.sh").path,
                target.appendingPathComponent("tools/run_app_server.sh").path
            ], cwd: target, logName: "chmod.log")
            log("Bundled source synchronized")
        }

        let runtime = try runtimeRoot()
        try fm.createDirectory(at: runtime, withIntermediateDirectories: true)
        log("Runtime root: \(runtime.path)")

        let venvPython = target.appendingPathComponent(".venv/bin/python")
        if !fm.fileExists(atPath: venvPython.path) {
            showStatus("首次启动正在安装依赖，可能需要几分钟...")
            let script = target.appendingPathComponent("tools/install_local_code_mode.sh")
            log("Installing dependencies with \(script.path)")
            try runShell([
                script.path,
                "--venv", target.appendingPathComponent(".venv").path,
                "--runtime-dir", runtime.path,
                "--port", String(port)
            ], cwd: target, logName: "install.log")
            log("Dependency install finished")
        } else {
            log("Existing virtualenv found")
        }
    }

    private func startServer() throws {
        showStatus("正在启动本地后端...")
        let root = try installRoot()
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/bash")
        process.arguments = [root.appendingPathComponent("tools/run_app_server.sh").path]
        process.currentDirectoryURL = root
        var env = ProcessInfo.processInfo.environment
        env["PYTHON_BIN"] = root.appendingPathComponent(".venv/bin/python").path
        env["APP_PORT"] = String(port)
        process.environment = env
        let log = root.appendingPathComponent(".runtime/app.log")
        try FileManager.default.createDirectory(at: log.deletingLastPathComponent(), withIntermediateDirectories: true)
        FileManager.default.createFile(atPath: log.path, contents: nil)
        let handle = try FileHandle(forWritingTo: log)
        process.standardOutput = handle
        process.standardError = handle
        try process.run()
        serverProcess = process
        self.log("Server process started: pid \(process.processIdentifier), log \(log.path)")
    }

    private func waitForServer() {
        showStatus("正在连接本地服务...")
        let deadline = Date().addingTimeInterval(90)
        func poll() {
            guard Date() < deadline else {
                self.showStatus("本地服务启动超时，请查看日志。")
                return
            }
            guard let url = URL(string: "http://127.0.0.1:\(self.port)/healthz") else { return }
            URLSession.shared.dataTask(with: url) { _, response, _ in
                if let http = response as? HTTPURLResponse, http.statusCode == 200 {
                    self.log("Server health check passed")
                    DispatchQueue.main.async {
                        self.statusLabel.isHidden = true
                        self.webView.isHidden = false
                        self.webView.load(URLRequest(url: URL(string: "http://127.0.0.1:\(self.port)/?setup=local-code&build=\(Int(Date().timeIntervalSince1970))")!))
                    }
                } else {
                    DispatchQueue.global().asyncAfter(deadline: .now() + 1.0, execute: poll)
                }
            }.resume()
        }
        poll()
    }

    private func runShell(_ args: [String], cwd: URL, logName: String) throws {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/bash")
        process.arguments = ["-lc", args.map { shellQuote($0) }.joined(separator: " ")]
        process.currentDirectoryURL = cwd
        let logURL = try supportRoot().appendingPathComponent(logName)
        FileManager.default.createFile(atPath: logURL.path, contents: nil)
        let handle = try FileHandle(forWritingTo: logURL)
        process.standardOutput = handle
        process.standardError = handle
        log("Running command: \(process.arguments?.joined(separator: " ") ?? "")")
        try process.run()
        process.waitUntilExit()
        try? handle.close()
        log("Command exited \(process.terminationStatus); output: \(logURL.path)")
        if process.terminationStatus != 0 {
            throw NSError(domain: "SageMate", code: Int(process.terminationStatus), userInfo: [NSLocalizedDescriptionKey: "安装命令失败，日志：\(logURL.path)"])
        }
    }

    private func shellQuote(_ value: String) -> String {
        "'" + value.replacingOccurrences(of: "'", with: "'\\''") + "'"
    }

    private func showStatus(_ text: String) {
        log("Status: \(text)")
        DispatchQueue.main.async {
            self.statusLabel.stringValue = text
            self.statusLabel.isHidden = false
        }
    }

    private func log(_ text: String) {
        let stamp = ISO8601DateFormatter().string(from: Date())
        let line = "[\(stamp)] \(text)\n"
        if let data = line.data(using: .utf8) {
            if !FileManager.default.fileExists(atPath: launcherLogURL.path) {
                FileManager.default.createFile(atPath: launcherLogURL.path, contents: nil)
            }
            if let handle = try? FileHandle(forWritingTo: launcherLogURL) {
                _ = try? handle.seekToEnd()
                try? handle.write(contentsOf: data)
                try? handle.close()
            }
        }
    }
}

@main
enum SageMateMain {
    private static var delegate: AppDelegate?

    static func main() {
        let app = NSApplication.shared
        let appDelegate = AppDelegate()
        delegate = appDelegate
        app.delegate = appDelegate
        app.run()
    }
}
EOF

swiftc "$work_dir/SageMateApp.swift" \
    -parse-as-library \
    -o "$app_macos/SageMate" \
    -framework Cocoa \
    -framework WebKit

cat > "$work_dir/$package_name/README-FIRST.txt" <<'EOF'
Sage Mate for macOS

1. Drag "Sage Mate.app" to Applications, or double-click it in this DMG.
2. The app starts a local backend and opens an embedded window.
3. Choose Faculty Twin or Code Assistant mode in Settings.

Your repositories stay on this Mac. The hosted Faculty Twin server does not
clone, store, or execute your code.
EOF

dmg_path="$dist_dir/$package_name.dmg"
rm -f "$dmg_path"

if command -v hdiutil >/dev/null 2>&1; then
    hdiutil create \
        -volname "$volume_name" \
        -srcfolder "$work_dir/$package_name" \
        -ov \
        -format UDZO \
        "$dmg_path" >/dev/null
    printf 'Built: %s\n' "$dmg_path"
else
    echo "hdiutil not found; cannot build DMG on this host." >&2
    build_zip=true
fi

if $build_zip; then
    (
        cd "$work_dir"
        zip -qr "$dist_dir/$package_name.zip" "$package_name"
    )
    printf 'Built: %s\n' "$dist_dir/$package_name.zip"
fi
