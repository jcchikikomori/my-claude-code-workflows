#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys


def main():
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    try:
        tool_input = data.get("tool_input", {})
        file_path = tool_input.get("file_path", "")

        if not file_path or not file_path.endswith(".md"):
            sys.exit(0)

        plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
        config_path = os.path.join(plugin_root, "config", ".markdownlint.json") if plugin_root else None

        binary = shutil.which("markdownlint-cli2")
        if binary:
            cmd = [binary, "--fix"]
        else:
            npx = shutil.which("npx")
            if not npx:
                print(
                    "[markdown-format] markdownlint-cli2 not found and npx unavailable.\n"
                    "  Install: npm install -g markdownlint-cli2",
                    file=sys.stderr,
                )
                sys.exit(0)
            cmd = [npx, "markdownlint-cli2", "--fix"]

        if config_path and os.path.isfile(config_path):
            cmd += ["--config", config_path]

        cmd.append(file_path)

        result = subprocess.run(cmd, capture_output=True, text=True)

        # 0 = all fixed, 1 = unfixable violations remain — both are acceptable
        if result.returncode not in (0, 1):
            print(
                f"[markdown-format] unexpected exit {result.returncode}: {result.stderr.strip()}",
                file=sys.stderr,
            )

    except Exception as exc:
        print(f"[markdown-format] error: {exc}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
