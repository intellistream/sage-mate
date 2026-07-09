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

claude_hust_source="${SAGE_MATE_CLAUDE_HUST_DIR:-}"
vllm_metal_source="${SAGE_MATE_VLLM_METAL_DIR:-$repo_root/deps/vllm-metal-hust}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --zip) build_zip=true ;;
        --claude-hust-dir)
            shift
            [[ $# -ge 1 ]] || { echo "--claude-hust-dir requires a path" >&2; exit 2; }
            claude_hust_source="${1/#\~/$HOME}"
            ;;
        --claude-hust-dir=*)
            claude_hust_source="${1#*=}"
            claude_hust_source="${claude_hust_source/#\~/$HOME}"
            ;;
        --vllm-metal-dir)
            shift
            [[ $# -ge 1 ]] || { echo "--vllm-metal-dir requires a path" >&2; exit 2; }
            vllm_metal_source="${1/#\~/$HOME}"
            ;;
        --vllm-metal-dir=*)
            vllm_metal_source="${1#*=}"
            vllm_metal_source="${vllm_metal_source/#\~/$HOME}"
            ;;
        -h|--help)
            cat <<'EOF'
Usage: tools/build_macos_local_code_package.sh [--zip] [--claude-hust-dir PATH] [--vllm-metal-dir PATH]

Builds dist/sage-mate-macos.dmg for macOS users.
Pass --zip to also build a zip fallback.
The DMG includes claude-code-hust, vllm-metal-hust, and pinned deps/vllm-hust source so Code Assistant does not clone them on user Macs.
EOF
            exit 0
            ;;
        *) echo "Unknown argument: $1" >&2; exit 2 ;;
    esac
    shift
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
    --exclude '/dist' \
    --exclude '/build' \
    --exclude '/logs' \
    --exclude '/data' \
    --exclude '/data.pre_recovery_*' \
    --exclude '*.egg-info' \
    "$repo_root/" "$payload_dir/"

if git -C "$repo_root/deps/vllm-hust" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    vllm_hust_version=$(python3 - "$repo_root/deps/vllm-hust" <<'PY'
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
metadata = json.loads((root / "upstream_version.json").read_text(encoding="utf-8"))
release = metadata["release_version"]
upstream_commit = metadata["upstream_commit"]
distance = subprocess.check_output(
    ["git", "-C", str(root), "rev-list", "--count", f"{upstream_commit}..HEAD"],
    text=True,
).strip()
short = subprocess.check_output(
    ["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
    text=True,
).strip()
print(f"{release}.post1.dev{distance}+g{short}")
PY
)
    printf '%s\n' "$vllm_hust_version" > "$payload_dir/deps/vllm-hust/.sage-mate-vllm-hust-version"
fi

chmod +x "$payload_dir/tools/install_local_code_mode.sh"
chmod +x "$payload_dir/tools/build_macos_local_code_package.sh"
chmod +x "$payload_dir/tools/install_vllm_metal_runtime.sh"
chmod +x "$payload_dir/tools/run_vllm_metal_engine.sh"

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

if [[ -z "$claude_hust_source" ]]; then
    for candidate in \
        "$(dirname "$repo_root")/claude-code-hust" \
        "$HOME/Documents/claude-code-hust" \
        "$HOME/claude-code-hust"; do
        if [[ -x "$candidate/bin/claude-hust" && -d "$candidate/node_modules" ]]; then
            claude_hust_source="$candidate"
            break
        fi
    done
fi

if [[ -z "$claude_hust_source" || ! -x "$claude_hust_source/bin/claude-hust" ]]; then
    echo "claude-code-hust bundle source was not found." >&2
    echo "Pass --claude-hust-dir PATH or set SAGE_MATE_CLAUDE_HUST_DIR." >&2
    exit 1
fi
if [[ ! -d "$claude_hust_source/node_modules" ]]; then
    echo "claude-code-hust source is missing node_modules: $claude_hust_source" >&2
    echo "Run bun install in that checkout before building the DMG." >&2
    exit 1
fi

rsync -a \
    --exclude '.git' \
    --exclude '.env' \
    --exclude 'logs' \
    --exclude 'tmp' \
    "$claude_hust_source/" "$app_resources/claude-code-hust/"
chmod +x "$app_resources/claude-code-hust/bin/claude-hust"

bun_source="${SAGE_MATE_BUN_BIN:-}"
if [[ -z "$bun_source" ]]; then
    bun_source="$(command -v bun || true)"
fi
if [[ -z "$bun_source" && -x "$HOME/.bun/bin/bun" ]]; then
    bun_source="$HOME/.bun/bin/bun"
fi
if [[ -n "$bun_source" && -x "$bun_source" ]]; then
    mkdir -p "$app_resources/bun/bin"
    cp "$bun_source" "$app_resources/bun/bin/bun"
    chmod +x "$app_resources/bun/bin/bun"
else
    echo "Warning: Bun binary was not found; bundled claude-hust will require Bun on the user Mac." >&2
fi

if [[ -z "$vllm_metal_source" || ! -f "$vllm_metal_source/install.sh" || ! -f "$vllm_metal_source/pyproject.toml" ]]; then
    echo "vllm-metal-hust source was not found." >&2
    echo "Pass --vllm-metal-dir PATH or set SAGE_MATE_VLLM_METAL_DIR." >&2
    exit 1
fi

rsync -a \
    --exclude '.git' \
    --exclude '.venv-vllm-metal' \
    --exclude 'target' \
    --exclude '.pytest_cache' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    "$vllm_metal_source/" "$app_resources/vllm-metal-hust/"
chmod +x "$app_resources/vllm-metal-hust/install.sh"

cat > "$work_dir/SageMateApp.swift" <<'EOF'
import Cocoa
import WebKit

final class AppDelegate: NSObject, NSApplicationDelegate, NSWindowDelegate, WKNavigationDelegate, WKScriptMessageHandler {
    private var window: NSWindow!
    private var webView: WKWebView!
    private var statusLabel: NSTextField!
    private var serverProcess: Process?
    private var modelProcess: Process?
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
                try self.startLocalModelEngineIfConfigured()
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
        modelProcess?.terminate()
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

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard message.name == "sageMatePickDirectory" else { return }
        let payload = message.body as? [String: Any]
        showDirectoryPicker(requestId: payload?["requestId"] as? String ?? "")
    }

    private func showDirectoryPicker(requestId: String) {
        DispatchQueue.main.async {
            let panel = NSOpenPanel()
            panel.title = "选择本地项目文件夹"
            panel.prompt = "添加项目"
            panel.canChooseFiles = false
            panel.canChooseDirectories = true
            panel.allowsMultipleSelection = false
            panel.canCreateDirectories = false
            panel.directoryURL = FileManager.default.homeDirectoryForCurrentUser
            let completion: (NSApplication.ModalResponse) -> Void = { response in
                let path = (response == .OK) ? panel.url?.path : nil
                self.resolveDirectoryPicker(requestId: requestId, path: path)
            }
            if let window = self.window {
                panel.beginSheetModal(for: window, completionHandler: completion)
            } else {
                completion(panel.runModal())
            }
        }
    }

    private func resolveDirectoryPicker(requestId: String, path: String?) {
        guard !requestId.isEmpty else { return }
        let value = path.map(jsonString) ?? "null"
        let script = """
        (function() {
            var callbacks = window.__sageMateDirectoryPickerCallbacks || {};
            var callback = callbacks[\(jsonString(requestId))];
            if (!callback) return;
            delete callbacks[\(jsonString(requestId))];
            callback(\(value));
        })();
        """
        webView.evaluateJavaScript(script, completionHandler: nil)
    }

    private func buildWindow() {
        if window != nil {
            return
        }

        let config = WKWebViewConfiguration()
        let userContentController = WKUserContentController()
        userContentController.add(self, name: "sageMatePickDirectory")
        let bridgeScript = """
        window.sageMateDesktop = window.sageMateDesktop || {};
        window.sageMateDesktop.pickWorkspaceDirectory = function() {
            return new Promise(function(resolve) {
                var requestId = "pick-" + Date.now() + "-" + Math.random().toString(16).slice(2);
                window.__sageMateDirectoryPickerCallbacks = window.__sageMateDirectoryPickerCallbacks || {};
                window.__sageMateDirectoryPickerCallbacks[requestId] = resolve;
                window.webkit.messageHandlers.sageMatePickDirectory.postMessage({ requestId: requestId });
            });
        };
        """
        userContentController.addUserScript(WKUserScript(source: bridgeScript, injectionTime: .atDocumentStart, forMainFrameOnly: true))
        config.userContentController = userContentController
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

    private func claudeHustRoot() throws -> URL {
        try supportRoot().appendingPathComponent("claude-code-hust", isDirectory: true)
    }

    private func vllmMetalRoot() throws -> URL {
        try supportRoot().appendingPathComponent("vllm-metal-hust", isDirectory: true)
    }

    private func vllmMetalSourceRoot() throws -> URL {
        try vllmMetalRoot().appendingPathComponent("source", isDirectory: true)
    }

    private func bundledBinRoot() throws -> URL {
        try supportRoot().appendingPathComponent("bin", isDirectory: true)
    }

    private func runtimeRoot() throws -> URL {
        let runtime = try supportRoot().appendingPathComponent("runtime", isDirectory: true)
        log("Using app-managed runtime repository: \(runtime.path)")
        return runtime
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

        try syncBundledClaudeHustIfAvailable()
        try syncBundledBunIfAvailable()
        try syncBundledVllmMetalIfAvailable()

        let runtime = try runtimeRoot()
        try fm.createDirectory(at: runtime, withIntermediateDirectories: true)
        log("Runtime root: \(runtime.path)")

        let venvPython = target.appendingPathComponent(".venv/bin/python")
        let needsInstall = !fm.fileExists(atPath: venvPython.path)
        let needsConfigRefresh = try localCodeConfigNeedsRefresh(target: target, runtime: runtime)
        if needsInstall || needsConfigRefresh {
            showStatus(needsInstall ? "首次启动正在安装依赖，可能需要几分钟..." : "正在刷新本地 Code Assistant 配置...")
            let script = target.appendingPathComponent("tools/install_local_code_mode.sh")
            log("Installing dependencies with \(script.path)")
            var installArgs = [
                script.path,
                "--venv", target.appendingPathComponent(".venv").path,
                "--runtime-dir", runtime.path,
                "--code-backend", "claude_hust",
                "--claude-hust-dir", try claudeHustRoot().path,
                "--workspace-roots", "",
                "--vllm-metal-dir", try vllmMetalSourceRoot().path,
                "--port", String(port)
            ]
            if !needsInstall {
                installArgs.append("--skip-python-install")
            }
            try runShell(installArgs, cwd: target, logName: "install.log")
            log(needsInstall ? "Dependency install finished" : "Local Code Assistant config refreshed")
        } else {
            log("Existing virtualenv found")
        }
        try cleanupStaleServiceProcesses()
    }

    private func cleanupStaleServiceProcesses() throws {
        let root = try installRoot()
        let vllmRoot = try vllmMetalRoot()
        let patterns = [
            root.appendingPathComponent(".venv/bin/python").path + " -m uvicorn sage_faculty_twin.api:app",
            vllmRoot.appendingPathComponent("source/.venv-vllm-metal/bin/python").path + " -m vllm.entrypoints.cli.main serve"
        ]
        for pattern in patterns {
            try runShell([
                "/bin/bash",
                "-lc",
                "/usr/bin/pkill -f \(shellQuote(pattern)) >/dev/null 2>&1 || true"
            ], cwd: root, logName: "cleanup-processes.log")
        }
    }

    private func syncBundledClaudeHustIfAvailable() throws {
        let fm = FileManager.default
        guard let source = Bundle.main.resourceURL?.appendingPathComponent("claude-code-hust", isDirectory: true),
              fm.fileExists(atPath: source.appendingPathComponent("bin/claude-hust").path) else {
            log("No bundled claude-code-hust resource found")
            return
        }
        let target = try claudeHustRoot()
        try fm.createDirectory(at: target.deletingLastPathComponent(), withIntermediateDirectories: true)
        try runShell([
            "/usr/bin/rsync",
            "-a",
            "--delete",
            source.path + "/",
            target.path + "/"
        ], cwd: target.deletingLastPathComponent(), logName: "sync-claude-hust.log")
        try runShell([
            "/bin/chmod",
            "+x",
            target.appendingPathComponent("bin/claude-hust").path
        ], cwd: target.deletingLastPathComponent(), logName: "chmod-claude-hust.log")
        log("Bundled claude-code-hust synchronized")
    }

    private func syncBundledBunIfAvailable() throws {
        let fm = FileManager.default
        guard let source = Bundle.main.resourceURL?.appendingPathComponent("bun/bin/bun"),
              fm.fileExists(atPath: source.path) else {
            log("No bundled Bun resource found")
            return
        }
        let target = try bundledBinRoot().appendingPathComponent("bun")
        try fm.createDirectory(at: target.deletingLastPathComponent(), withIntermediateDirectories: true)
        if fm.fileExists(atPath: target.path) {
            try fm.removeItem(at: target)
        }
        try fm.copyItem(at: source, to: target)
        try runShell([
            "/bin/chmod",
            "+x",
            target.path
        ], cwd: target.deletingLastPathComponent(), logName: "chmod-bun.log")
        log("Bundled Bun synchronized")
    }

    private func syncBundledVllmMetalIfAvailable() throws {
        let fm = FileManager.default
        guard let source = Bundle.main.resourceURL?.appendingPathComponent("vllm-metal-hust", isDirectory: true),
              fm.fileExists(atPath: source.appendingPathComponent("install.sh").path) else {
            log("No bundled vllm-metal-hust resource found")
            return
        }
        let target = try vllmMetalSourceRoot()
        try fm.createDirectory(at: target.deletingLastPathComponent(), withIntermediateDirectories: true)
        try runShell([
            "/usr/bin/rsync",
            "-a",
            "--delete",
            "--exclude", ".venv-vllm-metal",
            "--exclude", "target",
            source.path + "/",
            target.path + "/"
        ], cwd: target.deletingLastPathComponent(), logName: "sync-vllm-metal.log")
        try runShell([
            "/bin/chmod",
            "+x",
            target.appendingPathComponent("install.sh").path
        ], cwd: target.deletingLastPathComponent(), logName: "chmod-vllm-metal.log")
        log("Bundled vllm-metal-hust synchronized")
    }

    private func localCodeConfigNeedsRefresh(target: URL, runtime: URL) throws -> Bool {
        let envURL = target.appendingPathComponent(".env")
        guard FileManager.default.fileExists(atPath: envURL.path) else {
            return true
        }
        let contents = (try? String(contentsOf: envURL, encoding: .utf8)) ?? ""
        let desiredCLI = try claudeHustRoot().appendingPathComponent("bin/claude-hust").path
        let desiredVllmMetal = try vllmMetalSourceRoot().path
        let desiredRuntime = runtime.path
        let hasNonEmptyWorkspaceRoots = contents
            .split(separator: "\n")
            .contains { line in
                line.hasPrefix("DIGITAL_TWIN_CODE_WORKSPACE_ROOTS=")
                    && !line.dropFirst("DIGITAL_TWIN_CODE_WORKSPACE_ROOTS=".count).isEmpty
            }
        let llmWasAutoPrefilledFromHostedService =
            contents.contains("DIGITAL_TWIN_LLM_BASE_URL=https://api.sage.org.ai/v1")
            && !contents.contains("DIGITAL_TWIN_LLM_USER_CONFIGURED=true")
        return !contents.contains("DIGITAL_TWIN_APP_PROFILE=code_assistant")
            || !contents.contains("DIGITAL_TWIN_DEPLOYMENT_MODE=local_code")
            || !contents.contains("DIGITAL_TWIN_CODE_WORKBENCH_ENABLED=true")
            || !contents.contains("DIGITAL_TWIN_CODE_AGENT_BACKEND=claude_hust")
            || !contents.contains("DIGITAL_TWIN_CLAUDE_HUST_CLI_PATH=\(desiredCLI)")
            || !contents.contains("SAGE_MATE_VLLM_METAL_DIR=\(desiredVllmMetal)")
            || !contents.contains("DIGITAL_TWIN_RUNTIME_DIR=\(desiredRuntime)")
            || hasNonEmptyWorkspaceRoots
            || llmWasAutoPrefilledFromHostedService
    }

    private func startServer() throws {
        showStatus("正在启动本地后端...")
        let root = try installRoot()
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/bash")
        let script = root.appendingPathComponent("tools/run_app_server.sh").path
        let python = root.appendingPathComponent(".venv/bin/python").path
        process.arguments = [
            "-c",
            "PYTHON_BIN=\(shellQuote(python)) APP_PORT=\(shellQuote(String(port))) exec \(shellQuote(script))"
        ]
        process.currentDirectoryURL = root
        var env = baseServiceEnvironment()
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

    private func startLocalModelEngineIfConfigured() throws {
        let root = try installRoot()
        let envURL = root.appendingPathComponent(".env")
        let contents = (try? String(contentsOf: envURL, encoding: .utf8)) ?? ""
        guard contents.contains("DIGITAL_TWIN_LOCAL_MODEL_BACKEND=vllm_metal") else {
            log("Local model engine is not configured for vllm_metal")
            return
        }
        let script = root.appendingPathComponent("tools/run_vllm_metal_engine.sh")
        guard FileManager.default.fileExists(atPath: script.path) else {
            log("vllm-metal engine script missing: \(script.path)")
            return
        }
        showStatus("正在启动本地 Apple GPU 模型引擎...")
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/bash")
        process.arguments = ["-c", "exec \(shellQuote(script.path))"]
        process.currentDirectoryURL = root
        process.environment = baseServiceEnvironment()
        let log = root.appendingPathComponent(".runtime/vllm-metal.log")
        try FileManager.default.createDirectory(at: log.deletingLastPathComponent(), withIntermediateDirectories: true)
        FileManager.default.createFile(atPath: log.path, contents: nil)
        let handle = try FileHandle(forWritingTo: log)
        process.standardOutput = handle
        process.standardError = handle
        try process.run()
        modelProcess = process
        self.log("Model process started: pid \(process.processIdentifier), log \(log.path)")
    }

    private func baseServiceEnvironment() -> [String: String] {
        var env: [String: String] = [
            "HOME": FileManager.default.homeDirectoryForCurrentUser.path,
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
            "SHELL": "/bin/zsh",
            "NO_COLOR": "1"
        ]
        if let tmp = ProcessInfo.processInfo.environment["TMPDIR"] {
            env["TMPDIR"] = tmp
        }
        if let supportBin = try? bundledBinRoot().path {
            env["PATH"] = supportBin + ":" + env["PATH"]!
        }
        return env
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

    private func jsonString(_ value: String) -> String {
        if let data = try? JSONSerialization.data(withJSONObject: value),
           let text = String(data: data, encoding: .utf8) {
            return text
        }
        return "\"\""
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
