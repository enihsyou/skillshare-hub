---
name: ai-commit
description: Create a scoped Git commit with the root agent's AI author identity and a privately resolved real-user co-author.
---

# AI Commit

The delegated agent owns inspection, message generation, staging, commit and
verification. Return the result to the main agent; do not delegate again.

## Author

Use the supplied root model name to construct
`<Root Model Name> - <Root Harness Name>` and pass it with `--author-name`.
Use the model's display name and remove `[1m]` / `(latest)` suffixes.
For example, a `gpt-6.1-terra` Codex root uses `GPT-6.1 Terra - Codex`,
including when the executor is Claude Code + MiniMax. The supplied model name
is sufficient; do not look for a rollout to verify it.

When only a Codex root rollout path is available, pass `--root-rollout <path>`
instead. The script reads the final `turn_context.payload.model` and formats
`<Model Display Name> - Codex`. Use `Root/current rollout` in the main agent
or the supplied `Root rollout` in a child; never pass the child's `Current
rollout`. If neither source is available, report the missing root identity;
do not search session directories or substitute the executor's identity.

The script supplies the Arapacati email
`292837902+arapacati[bot]@users.noreply.github.com`, `--no-gpg-sign`, and the
repository-configured user's `Co-Authored-By` trailer.

## Execute

Use two Shell invocations for an ordinary commit:

1. Combine `git status --short` and relevant diffs. For staged-only requests,
   inspect `git diff --cached`; for explicit paths, also inspect their worktree
   diff. Derive the commit message unless supplied. Resolve any mismatch between
   the requested scope and staged content, preserving unrelated changes.
2. Stage only authorized paths when needed, then run the script from the target
   repository. Stop if staging fails. For staged-only requests, do not run
   `git add`. Run `git diff --cached --check` after staging or when whitespace
   risk is apparent.

Commit the current index:

```text
uv run --no-project <skill-dir>/scripts/git-commit.py --author-name "GPT-6.1 Sol - Codex" --message "Commit subject"
```

Replace `<skill-dir>` with this skill's absolute directory. Append `--dry-run`
to run without creating a commit or changing the index.
Use `-m` or `--message` repeatedly for multiple paragraphs, like
`-m "Commit subject" -m "Commit body"`; paragraphs are joined with a blank line.

For an authorized amendment, inspect the previous commit as well as the index:
the resulting commit contains the previous commit's changes plus the staged
changes. Pass `--amend` without `--message` to reuse the existing message, or
pass `--message` to replace its subject and body. Existing trailers are retained
when replacing the message; the configured user's identical co-author trailer
is not added twice. Other existing co-authors are retained. An amendment may
also change only the message with an unchanged index.

The amended commit uses the current root AI author and Arapacati email, even
when the original author differs. Git preserves the original author date; the
committer and commit date reflect the amendment. The same identity and
`--dry-run` options apply to amendments. Inspect the resulting full message and
scope when reporting the result.

## Results

The script resolves the real user and returns the recorded commit metadata.

- Report hash, subject, Author and scope. Include other commit metadata or
  diagnostic output when useful or requested. If a commit was created before
  metadata collection failed, report its hash; do not retry the commit.
- Push only when explicitly requested, using `ai-push`, and include its result.
