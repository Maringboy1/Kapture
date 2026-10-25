import argparse
import sys
import time

from kapture.single_instance import SingleInstance


def main():
    parser = argparse.ArgumentParser(prog="kapture")
    parser.add_argument("command", nargs="?", default="toggle",
                        choices=["toggle", "shot", "record", "stop", "pause", "resume", "status", "settings"])
    parser.add_argument("mode", nargs="?", default="full", choices=["full", "region", "window"])
    parser.add_argument("--hidden", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        from kapture.core.selftest import run_self_test
        sys.exit(run_self_test())

    if SingleInstance.is_running():
        msg = {"cmd": "show"}
        if args.command == "shot":
            msg = {"cmd": "shot", "mode": args.mode}
        elif args.command == "record":
            msg = {"cmd": "record", "mode": args.mode}
        elif args.command in ("stop", "pause", "resume"):
            msg = {"cmd": args.command}
        elif args.command == "settings":
            msg = {"cmd": "settings"}
        ok, resp = SingleInstance.send(msg)
        if ok:
            print(resp)
            return 0
        # fallthrough to start

    # start app
    from kapture.app import KaptureApp
    app = KaptureApp(sys.argv)
    # if a command was given, execute after startup
    if args.command not in ("toggle",):
        QTimer = None
        from PyQt6.QtCore import QTimer
        def run_cmd():
            if args.command == "shot":
                app.handle_shot_request(args.mode)
            elif args.command == "record":
                app.handle_record_request(args.mode)
            elif args.command == "stop":
                app.recorder.stop()
            elif args.command == "pause":
                app.recorder.pause()
            elif args.command == "resume":
                app.recorder.resume()
            elif args.command == "settings":
                app.open_settings()
        QTimer.singleShot(500, run_cmd)
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
