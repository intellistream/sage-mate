# Code Assistant Controlled Apply Patch Design

This document defines the proposed design for a future controlled apply-patch capability in the
Sage Mate `code_assistant` profile. It is a design note only; the current implementation remains
propose-only and must not write repository files.

## Goals

The apply-patch capability should let a local user take an LLM-produced unified diff, inspect it,
explicitly approve it, and apply it to an allowlisted workspace with reversible bookkeeping.

The feature is intentionally scoped to local, user-owned repositories:

- Available only in `DIGITAL_TWIN_DEPLOYMENT_MODE=local_code`.
- Available only when `DIGITAL_TWIN_APP_PROFILE=code_assistant`.
- Disabled unless a separate explicit setting enables patch application.
- Never available in hosted or web deployments.

## Why Propose-Only Remains the Default

Propose-only is the safe default because code changes are qualitatively different from code
analysis. Reading files and suggesting a diff does not mutate user state; applying a diff can break a
working tree, overwrite uncommitted work, introduce secrets into files, or run into subtle
environment-specific behavior.

Default propose-only behavior also keeps the local code workbench easy to reason about:

- The LLM can be wrong, incomplete, or maliciously steered by prompt-injected repository content.
- The repository may already contain user edits that should not be overwritten.
- The app should be usable for review, explanation, and planning without becoming an autonomous
  coding agent.
- The same UI and API can safely exist in more environments when mutation is absent.

For these reasons, `/code propose` and `POST /code/propose` remain read-only. Apply support, if
introduced, must be a separate command/API path with explicit opt-in configuration and an approval
step per patch.

## User Confirmation Flow

Patch application should require a two-stage user-confirmation flow.

1. Proposal stage:
   - The assistant returns a structured proposal containing summary, affected files, unified diff,
     risks, suggested tests, and model metadata.
   - The proposal receives a stable `proposal_id` derived from workspace id, normalized diff
     content, base git state, and timestamp.
   - No files are written during this stage.

2. Review stage:
   - The UI renders the normalized diff with file-by-file additions, deletions, renames, and mode
     changes.
   - The UI shows current git status and highlights files with existing user modifications.
   - The user must choose an explicit action such as `Apply patch`, not a conversational yes/no that
     can be confused with normal chat.
   - The confirmation must include the exact `proposal_id` and a hash of the normalized diff.

3. Apply stage:
   - The backend re-loads the stored proposal and verifies the submitted hash.
   - The backend re-checks git status and file preimages before applying.
   - If validation passes, the backend applies the patch and records an undo patch.
   - The response reports changed files, skipped files, warnings, and suggested next commands.

The confirmation is single-use. Any change to the proposal text, normalized diff, selected
workspace, git base state, or affected file preimage invalidates the pending approval.

## Diff Validation

The app should treat model output as untrusted text and validate it before presenting or applying
it.

Validation should include:

- Parse the proposal as a strict unified diff, not free-form text.
- Reject diffs with malformed hunks, inconsistent line counts, binary blobs, or unsupported patch
  metadata.
- Normalize paths, hunk headers, line endings, and trailing whitespace before hashing.
- Require each hunk's preimage context to match the current file content.
- Require newly created files to not already exist unless the diff is explicitly a modification.
- Require deleted files to match the expected preimage.
- Reject patches that touch files outside the selected workspace or outside the workspace's git
  repository when the workspace is git-backed.
- Reject patches that change ignored runtime data, local secrets, `.env` files, lock files, or
  generated artifacts unless a future allowlist explicitly permits them.
- Reject patches that contain command execution, shell transcript text, or markdown fences around
  the diff.

Implementation should prefer the platform patch parser or a small strict parser over ad hoc string
splitting. Before applying, run a dry-run check equivalent to `git apply --check` for git-backed
workspaces. For non-git workspaces, perform the same hunk preimage validation directly against file
contents.

## Path Escape Defense

Every file path in a patch must be resolved against the selected workspace root. The resolver must
reject path escapes before any read or write happens.

Required checks:

- Strip only valid unified-diff prefixes such as `a/` and `b/`; do not strip arbitrary leading path
  segments.
- Decode and normalize paths before validation.
- Reject absolute paths.
- Reject paths containing `..` segments after normalization.
- Reject symlink traversal that resolves outside the workspace.
- Reject hardlink or special-file targets that are not regular files.
- Reject Windows drive prefixes and UNC-style paths even on Unix hosts.
- Resolve the final target with `realpath` or equivalent and verify it is equal to or below the
  canonical workspace root.
- On case-insensitive filesystems, use the platform's canonical path comparison rules to avoid
  casing-based bypasses.

Patch validation and file application must use the same path resolver. A path accepted for preview
must not be reinterpreted differently during application.

## Undo Patch and Revert Mechanism

Every successful apply operation must create a reversible record before reporting success.

The apply record should include:

- `apply_id`
- `proposal_id`
- workspace id and canonical workspace root
- normalized diff hash
- git HEAD commit, when available
- pre-apply git status summary
- list of affected files
- generated reverse unified diff
- timestamp and user identity, when available

For git-backed workspaces, the backend should generate the undo patch from the actual applied file
changes, not from the model's proposed reverse diff. A safe sequence is:

1. Capture current file contents or git blobs for every affected path.
2. Apply the validated patch.
3. Generate the reverse diff from pre-apply snapshots to post-apply contents.
4. Store the reverse diff in Sage Mate runtime data outside the repository.

Undo should be exposed as a separate explicit command/API operation, for example:

```text
/code undo-patch <workspace> <apply_id>
```

Undo must run the same path validation, hunk preimage matching, and user confirmation flow as apply.
If the working tree has changed since the patch was applied, undo should fail with a conflict report
instead of forcing a revert.

The feature should not call `git reset`, `git checkout`, or other broad destructive operations.
Revert is patch-scoped and file-scoped.

## Test Command Authorization

Applying a patch and running tests are separate privileges. The user may approve a patch without
approving any command execution.

Test execution should follow the existing `/code run` safety model:

- Commands must be allowlisted.
- Commands must be displayed to the user before execution.
- Write-capable commands require explicit per-command confirmation unless they are separately
  allowlisted for the selected workspace.
- The UI should distinguish suggested tests from commands that will actually run.
- The backend must not infer permission to run tests from permission to apply a patch.

The assistant may suggest commands such as:

```bash
PYTHONPATH=src pytest tests/test_parser.py
node --check src/sage_faculty_twin/web/app.js
```

The user must authorize each command or a named command group. Authorization should include command
string, working directory, timeout, and whether filesystem writes are expected. Long-running,
networked, privileged, or destructive commands should remain blocked unless a future explicit policy
allows them.

## Why Apply Does Not Auto Commit or Push

The controlled apply-patch feature stops at working-tree changes. It must not automatically commit
or push because those operations publish state and create durable history outside the immediate
patch application boundary.

Reasons:

- The user may want to inspect, edit, or partially stage the result.
- Tests may fail or require local-only setup.
- Commit messages require project context and human intent.
- Push can expose private code, secrets, or unfinished work to a remote.
- Branch protections, signing requirements, and review policy differ by repository.
- Existing uncommitted user work may be intentionally mixed into the working tree but should not be
  included in an assistant-generated commit.

The app may suggest follow-up commands such as `git diff`, `git status`, or a test command. It
should leave commit and push to explicit user action outside the apply flow.

## Hosted and Web Mode Permanent Disablement

Hosted and browser-only web deployments must permanently disable apply patch. This is not a feature
flag that hosted operators can turn on.

Reasons:

- Hosted Faculty Twin is a multi-user service for chat, scheduling, knowledge, and operations. It
  must not read, clone, store, or execute user repositories.
- Applying patches requires filesystem mutation near user code. That belongs on the user's own
  machine, not on the hosted application server.
- Web sessions cannot reliably prove that a repository path belongs to the current user or that
  mutation is locally reversible.
- Hosted code execution would create unacceptable risks around tenant isolation, secret exposure,
  repository persistence, and remote command execution.
- Keeping hosted mode permanently read-only for code workflows preserves the product boundary
  documented in `local-code-mode.md`.

In hosted mode, code workbench APIs should remain unavailable even if workspace paths or
`claude-code-hust` binaries exist on the server. The server must fail closed.

## Boundary With claude-code-hust

`claude-code-hust` may be used as a separate local code-analysis backend, but it is not the Sage
Mate workflow owner.

Sage Mate owns:

- deployment-mode enforcement,
- app profile selection,
- workspace allowlist and path resolution,
- proposal storage,
- diff normalization and validation,
- user confirmation UI,
- patch application and undo records,
- command authorization,
- workflow trace reporting.

`claude-code-hust` may own:

- local repository inspection inside a temporary or allowlisted workspace,
- model-facing code reasoning,
- generating proposed changes,
- returning structured text or unified diff suggestions.

It must not bypass Sage Mate's confirmation flow, path escape checks, diff validation, undo
bookkeeping, or hosted-mode disablement. When configured, it should be treated as an untrusted local
proposal source whose output goes through the same validation path as any internal model response.

## Integration Order

Apply patch should land after the rest of the local code-assistant foundation is stable. In
particular, it must come after `/code doctor`, the backend adapter boundary, and Code Session
support, so patch application can reuse the established diagnostics, provider routing, and
session-level trace model.

The first apply-patch version should consume only `CodeProposeResponse.unified_diff`. It should not
accept arbitrary chat text, external files, command output, or direct CLI-side mutations as patch
input.

`claude-code-hust` may generate or suggest diffs, but it must not bypass Sage Mate's confirmation
flow or write directly to the user's real repository. Any diff it produces must return through the
same `CodeProposeResponse.unified_diff` path and pass Sage Mate validation before the user can apply
it.

The UI must show the normalized diff, risks, and suggested tests before presenting the confirmation
control. Confirmation should be a deliberate action after review, not an inline continuation of the
assistant conversation.

## Minimum Acceptance Criteria

A future implementation should not be considered ready unless it satisfies all of the following:

- Propose-only remains the default for every install.
- Apply is available only in local `code_assistant` mode with explicit opt-in.
- Hosted and web deployments cannot enable apply through configuration.
- Every apply requires a reviewed diff, stable proposal id, diff hash, and explicit user action.
- Every hunk is validated against current file contents before mutation.
- Every affected path is proven to stay inside the selected workspace.
- Every successful apply stores a reverse patch outside the repository.
- Undo uses the same validation and confirmation discipline as apply.
- Test commands require separate user authorization.
- Commit and push are never automatic.
