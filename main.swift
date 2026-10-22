import Cocoa

let sudoersPath = "/etc/sudoers.d/lidawake"

@discardableResult
func run(_ path: String, _ args: [String]) -> (ok: Bool, out: String) {
    let p = Process()
    let pipe = Pipe()
    p.executableURL = URL(fileURLWithPath: path)
    p.arguments = args
    p.standardOutput = pipe
    p.standardError = pipe
    do { try p.run() } catch { return (false, "\(error)") }
    let data = pipe.fileHandleForReading.readDataToEndOfFile()
    p.waitUntilExit()
    return (p.terminationStatus == 0, String(decoding: data, as: UTF8.self))
}

// 정책서 §2: 앱 변수가 아니라 pmset 값이 진실의 원천
func sleepDisabled() -> Bool {
    run("/usr/bin/pmset", ["-g"]).out
        .split(separator: "\n")
        .contains { $0.contains("SleepDisabled") && $0.split(whereSeparator: \.isWhitespace).last == "1" }
}

@discardableResult
func setSleepDisabled(_ on: Bool) -> (ok: Bool, out: String) {
    run("/usr/bin/sudo", ["-n", "/usr/bin/pmset", "-a", "disablesleep", on ? "1" : "0"])
}

// 정책서 §1: 최초 1회 관리자 인증으로 pmset disablesleep 0/1 두 명령만 NOPASSWD 허용
func installSudoersRule() -> (ok: Bool, out: String) {
    let rule = "\(NSUserName()) ALL=(root) NOPASSWD: /usr/bin/pmset -a disablesleep 0, /usr/bin/pmset -a disablesleep 1\n"
    let tmp = NSTemporaryDirectory() + "lidawake.sudoers"
    do { try rule.write(toFile: tmp, atomically: true, encoding: .utf8) } catch { return (false, "\(error)") }
    defer { try? FileManager.default.removeItem(atPath: tmp) }
    let sh = "/usr/sbin/visudo -cf '\(tmp)' && /usr/bin/install -m 0440 -o root -g wheel '\(tmp)' '\(sudoersPath)'"
    return run("/usr/bin/osascript", ["-e", "do shell script \"\(sh)\" with administrator privileges"])
}

@MainActor
func alert(_ text: String) {
    NSApp.activate(ignoringOtherApps: true)
    let a = NSAlert()
    a.messageText = "LidAwake"
    a.informativeText = text
    a.runModal()
}

@MainActor
final class App: NSObject, NSApplicationDelegate {
    let item = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)

    func applicationDidFinishLaunching(_ n: Notification) {
        item.button?.target = self
        item.button?.action = #selector(clicked)
        item.button?.sendAction(on: [.leftMouseUp, .rightMouseUp])
        refresh()
    }

    // 정책서 §3: 종료 시 잠자기 방지 해제
    func applicationWillTerminate(_ n: Notification) {
        if sleepDisabled() { setSleepDisabled(false) }
    }

    @objc func clicked() {
        let e = NSApp.currentEvent
        if e?.type == .rightMouseUp || e?.modifierFlags.contains(.control) == true {
            let menu = NSMenu()
            menu.addItem(withTitle: "종료", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
            item.menu = menu
            item.button?.performClick(nil)
            item.menu = nil
        } else {
            toggle()
        }
    }

    func toggle() {
        let target = !sleepDisabled()
        var r = setSleepDisabled(target)
        if !r.ok {
            let setup = installSudoersRule()
            if !setup.ok {
                if !setup.out.contains("-128") { alert("권한 설정 실패:\n\(setup.out)") }  // -128 = 사용자가 취소
                return
            }
            r = setSleepDisabled(target)
            if !r.ok { alert("pmset 실행 실패:\n\(r.out)") }
        }
        refresh()
    }

    func refresh() {
        let on = sleepDisabled()
        item.button?.image = NSImage(systemSymbolName: on ? "cup.and.saucer.fill" : "moon.zzz",
                                     accessibilityDescription: on ? "잠자기 방지 중" : "잠자기 허용")
        item.button?.toolTip = on ? "잠자기 방지 중 — 덮개를 닫아도 깨어 있음 (클릭: 해제)"
                                  : "잠자기 허용 — 평소 상태 (클릭: 잠자기 방지)"
    }
}

MainActor.assumeIsolated {
    let app = NSApplication.shared
    let delegate = App()
    app.delegate = delegate
    app.setActivationPolicy(.accessory)
    app.run()
}
