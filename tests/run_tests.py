#!/usr/bin/env python3
"""
The libraries' tests, run with a release's binary:

  libraries  every library loads and answers a call
  net        net.request against a local HTTP server, through each platform's client

Each case prints PASS/FAIL per check and DONE <failures> at its end. A run passes when it exits with 0,
prints DONE 0 and no FAIL.

    python tests/run_tests.py --bin <folder with runscript> [--libraries <folder with the DLLs>]

Without --libraries the DLLs are looked for in build/libraries, as a DLL build makes them. --static runs
executables that have the libraries bound in, without DLLs.
"""

import argparse
import gzip
import hashlib
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = HERE / "cases"
REPO = HERE.parent
EXE = ".exe" if os.name == "nt" else ""
TIMEOUT = 120

SUITE_TITLES = {"libraries": "Libraries", "net": "Net (net.request)"}

DLL_MESSAGES = ["could not list module directory", "Could not load module", "DLL modules are not supported"]

BIG_BODY = bytes(i % 251 for i in range(1024 * 1024))


class TestHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def answer(self, status, body=b"", headers=None, send_body=True):
        self.send_response(status)
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if send_body:
            self.wfile.write(body)

    def route(self, send_body):
        path = self.path.split("?")[0]
        if path == "/hello":
            self.answer(200, b"hello", {"Content-Type": "text/plain", "X-Test": "yes"}, send_body)
        elif path == "/redirect":
            self.answer(302, b"", {"Location": "/hello"}, send_body)
        elif path == "/gzip":
            if "gzip" not in self.headers.get("Accept-Encoding", ""):
                self.answer(406, b"the client didn't accept gzip", None, send_body)
            else:
                self.answer(200, gzip.compress(b"compressed hello"), {"Content-Encoding": "gzip"}, send_body)
        elif path == "/big":
            self.answer(200, BIG_BODY, {"Content-Type": "application/octet-stream"}, send_body)
        elif path == "/empty":
            self.answer(200, b"", None, send_body)
        elif path == "/slow":
            time.sleep(6)
            self.answer(200, b"late", None, send_body)
        else:
            self.answer(404, b"nope", None, send_body)

    def do_GET(self):
        self.route(True)

    def do_HEAD(self):
        self.route(False)

    # method|body|X-Custom|Content-Type
    def echo(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(length) if length else b""
        text = "|".join([self.command, body.decode("utf-8", "replace"), self.headers.get("X-Custom", ""),
                         self.headers.get("Content-Type", "")])
        self.answer(200, text.encode("utf-8"))

    def do_POST(self):
        self.echo()

    def do_PUT(self):
        self.echo()


def start_server():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), TestHandler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


class Run:
    def __init__(self, suite, case, arguments):
        self.suite = suite
        self.case = case
        self.arguments = arguments
        self.output = ""
        self.passes = 0
        self.failures = []
        self.problems = []

    @property
    def ok(self):
        return not self.problems and not self.failures


def find_libraries(given):
    if given:
        return Path(given).resolve()
    build = REPO / "build" / "libraries"
    for folder in [build / "Release", build / "MinSizeRel", build / "RelWithDebInfo", build / "Debug", build]:
        if any(folder.glob("fs.*")):
            return folder
    sys.exit("Couldn't find the library DLLs under build/libraries, pass --libraries")


def execute(run, runscript, project):
    command = [str(runscript), f"cases/{run.case}.luau", ".config.luau", *run.arguments]
    try:
        result = subprocess.run(command, cwd=project, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=TIMEOUT)
        run.output = result.stdout.decode("utf-8", errors="replace")
        code = result.returncode
    except subprocess.TimeoutExpired as error:
        run.output = (error.stdout or b"").decode("utf-8", errors="replace")
        run.problems.append(f"timed out after {TIMEOUT} s")
        return

    done = None
    for line in run.output.splitlines():
        if line.startswith("PASS "):
            run.passes += 1
        elif line.startswith("FAIL "):
            run.failures.append(line[5:])
        elif line.startswith("DONE "):
            done = line[5:].strip()
    if code != 0:
        run.problems.append(f"exited with {code}")
    if done is None:
        run.problems.append("never printed DONE")
    elif done != str(len(run.failures)):
        run.problems.append(f"printed DONE {done} with {len(run.failures)} failed checks")
    for message in DLL_MESSAGES:
        if message in run.output:
            run.problems.append(f"printed \"{message}\"")


def report(runs, verbose):
    for run in runs:
        print(f"{'ok  ' if run.ok else 'FAIL'} {run.suite}/{run.case} ({run.passes + len(run.failures)} checks)")
        if not run.ok or verbose:
            for problem in run.problems:
                print(f"       {problem}")
            for line in run.output.splitlines():
                print(f"       | {line}")

    print()
    lines = []
    for suite in dict.fromkeys(run.suite for run in runs):
        suite_runs = [run for run in runs if run.suite == suite]
        passed = sum(1 for run in suite_runs if run.ok)
        checks = sum(run.passes for run in suite_runs)
        failed_checks = sum(len(run.failures) for run in suite_runs)
        line = (f"{SUITE_TITLES[suite]}: {passed} runs passed, {len(suite_runs) - passed} failed; "
                f"{checks} checks passed, {failed_checks} failed")
        print(line)
        lines.append(line)

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as out:
            mark = "✅" if all(run.ok for run in runs) else "❌"
            out.write(f"### {mark} Library tests on {sys.platform}\n\n")
            for line in lines:
                out.write(f"- {line}\n")
            for run in runs:
                if not run.ok:
                    reasons = run.problems + run.failures
                    out.write(f"- ❌ `{run.suite}/{run.case}`: {'; '.join(reasons)}\n")
            out.write("\n")
    return all(run.ok for run in runs)


def main():
    parser = argparse.ArgumentParser(description="The Luwow libraries' tests")
    parser.add_argument("--bin", required=True, help="folder with the release's runscript")
    parser.add_argument("--libraries", help="folder with the library DLLs (default: found under build/libraries)")
    parser.add_argument("--static", action="store_true", help="the executables have the libraries bound in")
    parser.add_argument("--suite", choices=["all", "libraries", "net"], default="all")
    parser.add_argument("--verbose", action="store_true", help="print every run's output")
    args = parser.parse_args()

    runscript = Path(args.bin).resolve() / ("runscript" + EXE)
    if not runscript.is_file():
        sys.exit(f"{runscript} doesn't exist")
    suites = ["libraries", "net"] if args.suite == "all" else [args.suite]

    workspace = Path(tempfile.mkdtemp(prefix="luwow-libraries-"))
    try:
        # A static build loads no DLLs, its config gets an empty folder
        libraries = workspace / "no-libraries" if args.static else find_libraries(args.libraries)
        libraries.mkdir(exist_ok=True)
        print(f"runscript: {runscript}")
        print(f"Libraries: {'bound into the executables' if args.static else libraries}")
        print()

        project = workspace / "project"
        shutil.copytree(CASES, project / "cases")
        (project / "types").mkdir()
        config = {"luau": {"aliases": {"Luwow": "./types"}, "dlls": libraries.as_posix()}}
        (project / ".config.luau").write_text(f"return {to_luau(config)}\n", encoding="utf-8")
        scratch = workspace / "scratch"
        scratch.mkdir()

        runs = []
        server = None
        if "libraries" in suites:
            runs.append(Run("libraries", "libraries", [scratch.as_posix(), sys.platform]))
        if "net" in suites:
            server, url = start_server()
            runs.append(Run("net", "net", [url, scratch.as_posix(), hashlib.md5(BIG_BODY).hexdigest()]))

        for run in runs:
            execute(run, runscript, project)
        if server:
            server.shutdown()
        ok = report(runs, args.verbose)
    finally:
        shutil.rmtree(workspace, ignore_errors=True)

    sys.exit(0 if ok else 1)


def to_luau(value):
    if isinstance(value, dict):
        return "{ " + ", ".join(f"{key} = {to_luau(item)}" for key, item in value.items()) + " }"
    return json.dumps(value)


if __name__ == "__main__":
    main()
