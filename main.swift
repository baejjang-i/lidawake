import Cocoa

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
    let sh = "/usr/sbin/visudo -cf '\(tmp)' && /usr/bin/install -m 0440 -o root -g wheel '\(tmp)' /etc/sudoers.d/lidawake"
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
    let awake = NSImage(systemSymbolName: "cup.and.saucer.fill", accessibilityDescription: "잠자기 방지 중")
    let asleep = NSImage(systemSymbolName: "moon.zzz", accessibilityDescription: "잠자기 허용")

    func applicationDidFinishLaunching(_ n: Notification) {
        item.button?.target = self
        item.button?.action = #selector(clicked)
        item.button?.sendAction(on: [.leftMouseUp, .rightMouseUp])
        show(sleepDisabled())
    }

    // 정책서 §3: 종료 시 잠자기 방지 해제 (이미 0이어도 무해하므로 상태 조회 없이 바로 실행)
    func applicationWillTerminate(_ n: Notification) {
        setSleepDisabled(false)
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
        malloc_zone_pressure_relief(nil, 0)  // 클릭 처리(메뉴·경고창·프로세스)로 늘어난 힙을 즉시 반환
    }

    func toggle() {
        let target = !sleepDisabled()  // 정책서 §2: 클릭 시점의 실제 값 기준
        if setSleepDisabled(target).ok { return show(target) }
        let setup = installSudoersRule()
        if !setup.ok {
            if !setup.out.contains("-128") { alert("권한 설정 실패:\n\(setup.out)") }  // -128 = 사용자가 취소
            return
        }
        let r = setSleepDisabled(target)
        if !r.ok { alert("pmset 실행 실패:\n\(r.out)") }
        show(r.ok ? target : sleepDisabled())
    }

    func show(_ on: Bool) {
        item.button?.image = on ? awake : asleep
        item.button?.toolTip = on ? "잠자기 방지 중 — 덮개를 닫아도 깨어 있음 (클릭: 해제)"
                                  : "잠자기 허용 — 평소 상태 (클릭: 잠자기 방지)"
    }
}

MainActor.assumeIsolated {
    let app = NSApplication.shared
    let delegate = App()
    app.delegate = delegate
    app.run()
}
