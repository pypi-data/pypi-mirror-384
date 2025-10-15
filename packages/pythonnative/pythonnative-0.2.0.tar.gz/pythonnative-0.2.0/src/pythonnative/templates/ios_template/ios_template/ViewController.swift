//
//  ViewController.swift
//  ios_template
//
//  Created by Owen Carey on 6/19/23.
//

import UIKit
// PythonKit isn't available on iOS by default; guard its use so the
// template builds out of the box and falls back to a native label.
#if canImport(PythonKit)
import PythonKit
#endif
#if canImport(Python)
import Python
#endif

class ViewController: UIViewController {

    override func viewDidLoad() {
        super.viewDidLoad()
        NSLog("[PN][ViewController] viewDidLoad")
        if let bundleId = Bundle.main.bundleIdentifier {
            NSLog("[PN] Bundle Identifier: \(bundleId)")
        }
        NSLog("[PN] Bundle Path: \(Bundle.main.bundlePath)")
        NSLog("[PN] Resource Path: \(Bundle.main.resourcePath ?? "nil")")
        // Configure embedded Python if available in bundle
        if let resourcePath = Bundle.main.resourcePath {
            let pyStd = "\(resourcePath)/python-stdlib"
            let pyDyn = "\(resourcePath)/python-stdlib/lib-dynload"
            var pyPath = "\(pyStd):\(pyDyn):\(resourcePath):\(resourcePath)/app"
            let platSite = "\(resourcePath)/platform-site"
            if FileManager.default.fileExists(atPath: platSite) {
                pyPath += ":\(platSite)"
            }
            setenv("PYTHONHOME", pyStd, 1)
            setenv("PYTHONPATH", pyPath, 1)
            NSLog("[PN] Set PYTHONHOME=\(pyStd)")
            NSLog("[PN] Set PYTHONPATH=\(pyPath)")
        }
        #if canImport(PythonKit)
        // Ensure PythonKit knows where to load the Python library from when using an embedded framework.
        if let bundlePath = Bundle.main.bundlePath as String? {
            let frameworkLib = "\(bundlePath)/Frameworks/Python.framework/Python"
            setenv("PYTHON_LIBRARY", frameworkLib, 1)
            if FileManager.default.fileExists(atPath: frameworkLib) {
                NSLog("[PN] Using embedded Python lib at: \(frameworkLib)")
                PythonLibrary.useLibrary(at: frameworkLib)
            } else {
                NSLog("[PN] Embedded Python library not found at: \(frameworkLib)")
            }
        }
        NSLog("[PN] PythonKit available; attempting Python bootstrap of app.main_page.bootstrap(self)")
        // Attempt Python bootstrap of app.main_page.bootstrap(self)
        let sys = Python.import("sys")
        NSLog("[PN] Python version: \(sys.version)")
        NSLog("[PN] Initial sys.path: \(sys.path)")
        if let resourcePath = Bundle.main.resourcePath {
            sys.path.append(resourcePath)
            sys.path.append("\(resourcePath)/app")
            NSLog("[PN] Updated sys.path: \(sys.path)")
            // List bundled resources to verify Python files are present
            let fm = FileManager.default
            let appDir = "\(resourcePath)/app"
            if let entries = try? fm.contentsOfDirectory(atPath: appDir) {
                NSLog("[PN] Contents of /app in bundle: \(entries)")
            } else {
                NSLog("[PN] Could not list contents of \(appDir).")
            }
        }
        do {
            let app = try Python.attemptImport("app.main_page")
            let pyNone = Python.None
            let builtins = Python.import("builtins")
            let getattrFn = builtins.getattr
            let bootstrap = try getattrFn.throwing.dynamicallyCall(withArguments: [app, "bootstrap", pyNone])
            if bootstrap != Python.None {
                do {
                    let isCallable = try Python.callable.throwing.dynamicallyCall(withArguments: [bootstrap])
                    if Bool(isCallable) == true {
                        // Pass the native UIViewController pointer into Python so it can be wrapped by rubicon.objc
                        let ptr = Unmanaged.passUnretained(self).toOpaque()
                        let addr = UInt(bitPattern: ptr)
                        NSLog("[PN] Passing native UIViewController pointer to Python: 0x%llx", addr)
                        _ = try bootstrap.throwing.dynamicallyCall(withArguments: [addr])
                        NSLog("[PN] Python bootstrap succeeded; returning early from viewDidLoad")
                        return
                    } else {
                        NSLog("[PN] 'bootstrap' exists but is not callable")
                    }
                } catch {
                    NSLog("[PN] Python callable/bootstrap raised error: \(error)")
                    let sys = Python.import("sys")
                    NSLog("[PN] sys.path at call error: \(sys.path)")
                }
            } else {
                NSLog("[PN] Python bootstrap function not found on app.main_page")
            }
        } catch {
            NSLog("[PN] Python bootstrap failed during import/getattr: \(error)")
            let sys = Python.import("sys")
            NSLog("[PN] sys.path at failure: \(sys.path)")
        }
        #endif

        // Fallback UI if Python import/bootstrap fails
        NSLog("[PN] Python unavailable or bootstrap failed; showing fallback UILabel")
        let label = UILabel(frame: view.bounds)
        label.text = "Hello from PythonNative (iOS template)"
        label.textAlignment = .center
        label.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        view.addSubview(label)
    }


}

