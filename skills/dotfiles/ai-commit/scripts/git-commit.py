"""Commit the current index with the configured user as co-author."""

import argparse
import json
import re
import subprocess


AUTHOR_EMAIL = "292837902+arapacati[bot]@users.noreply.github.com"


def author_from_rollout(path):
    model = None
    with open(path, encoding="utf-8") as rollout:
        for line in rollout:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                raise RuntimeError("Root rollout contains invalid JSON") from None
            if record.get("type") == "turn_context":
                model = record["payload"].get("model")
    if not isinstance(model, str) or not model.strip() or model == "unavailable":
        raise RuntimeError("Root rollout's final turn_context has no usable model")
    model = re.sub(r"\s*(?:\[1m\]|\(latest\))", "", model).strip()
    gpt = re.fullmatch(r"gpt-(\d+(?:\.\d+)*)(?:-([a-z0-9-]+))?", model)
    if gpt:
        model = f"GPT-{gpt[1]}"
        if gpt[2]:
            model += " " + gpt[2].replace("-", " ").title()
    return f"{model} - Codex"


def git(*args):
    # Capture even errors: Git and hooks can include the real user's identity.
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace"
    )


def required(*args):
    result = git(*args)
    if result.returncode:
        raise RuntimeError(f"Git {args[0]} failed (exit {result.returncode}); output withheld")
    return result.stdout.rstrip("\r\n")


def commit(args):
    name = required("config", "--get", "user.name")
    email = required("config", "--get", "user.email")
    if not name.strip() or not email.strip() or any(c in name + email for c in "\r\n"):
        raise RuntimeError("Configure a nonempty, single-line Git user name and email locally")
    trailer = f"Co-Authored-By: {name} <{email}>"
    author = f"{args.author_name} <{AUTHOR_EMAIL}>"
    command = ["commit"]
    if args.amend:
        command = ["-c", "trailer.ifExists=addIfDifferent", "-c",
                   "trailer.co-authored-by.ifExists=addIfDifferent", *command]
    command += [f"--author={author}", "--no-gpg-sign"]
    if args.amend:
        command.append("--amend")
        if args.message is None:
            command.append("--no-edit")
        else:
            trailers = required("show", "-s", "--format=%(trailers:unfold)", "HEAD")
            command.extend(f"--trailer={item}" for item in trailers.splitlines())
    if args.message is not None:
        command.extend(["-m", args.message])
    command.append(f"--trailer={trailer}")
    if args.dry_run:
        result = git(*command, "--dry-run")
        if result.returncode not in (0, 1):
            raise RuntimeError(f"Git dry-run failed (exit {result.returncode}); output withheld")
        return {
            "mode": "dry-run", "author_argument": f"--author={author}",
            "coauthor_resolved": True, "committable": result.returncode == 0,
            "git_exit_code": result.returncode, "metadata_written": False,
        }, 0

    result = git(*command)
    if result.returncode:
        raise RuntimeError(f"Git commit failed (exit {result.returncode}); output withheld; inspect state before retrying")

    # Emit the hash first so a later metadata error cannot hide a completed commit.
    sha = required("rev-parse", "HEAD")
    print(json.dumps({"commit_created": sha}), flush=True)
    metadata = required("show", "-s", "--format=%an%x00%ae%x00%cn <%ce>%x00%B", sha)
    author_name, author_email, committer, message = metadata.split("\0", 3)
    return {
        "mode": "commit", "hash": sha, "subject": message.splitlines()[0],
        "author": f"{author_name} <{author_email}>", "committer": committer,
        "message": message,
        "paths": required("diff-tree", "--root", "--no-commit-id", "--name-only", "-r", sha).splitlines(),
        "status": required("status", "--short").splitlines(),
    }, 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    identity = parser.add_mutually_exclusive_group(required=True)
    identity.add_argument("--author-name")
    identity.add_argument("--root-rollout", help="Root Codex rollout JSONL path")
    parser.add_argument("-m", "--message", action="append", help="Commit message paragraph; repeat for multiple paragraphs")
    parser.add_argument("--amend", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.message is None and not args.amend:
        parser.error("--message is required unless --amend is used")
    if args.message is not None:
        args.message = "\n\n".join(args.message)
    if args.message is not None and not args.message.strip():
        parser.error("message must be nonempty")
    try:
        if args.root_rollout:
            args.author_name = author_from_rollout(args.root_rollout)
        if not args.author_name.strip() or any(c in args.author_name for c in "\r\n<>"):
            parser.error("author name must be nonempty and contain no newline or angle bracket")
        output, code = commit(args)
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        # Never serialize subprocess exceptions: they can contain private arguments.
        output = {"error": str(error) if isinstance(error, RuntimeError) else "Execution failed; details withheld"}
        code = 1
    print(json.dumps(output, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
