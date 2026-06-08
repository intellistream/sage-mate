# Runtime Data Boundary

This repository tracks the my-twin deployment state in Git so a fresh deploy can
recover the current knowledge base, conversation memory, queues, and user state.
The source-control boundary is therefore not "code only"; it is "code plus the
deployment data we intentionally want to recreate on another machine."

## Tracked Deployment State

These paths are expected to stay versioned because they define or preserve the
current deployable twin state:

- `data/_seed_faq.json`
- `data/persona/style_profile.md`
- `data/availability/current_week.json`
- `data/availability/history/`
- `data/knowledge_base/`
- `data/conversation_memory/`
- `data/artifact_memory_drafts/`
- `data/knowledge_gap_drafts/`
- `data/escalations/`
- `data/follow_up_actions/`
- `data/operations_task_state/`
- `data/suggestions/`
- `data/user_accounts/`
- `data/workflow_policies/`
- `data/workflow_scenarios/`
- `tools/cloudflared-config.example.yml`

## Ignored Backup And Scratch Artifacts

These paths are intentionally ignored because they are backup snapshots,
temporary export artifacts, or local scratch copies rather than the canonical
deployment state:

- `data.pre_recovery_*/`
- `data/*.backup-*/`
- `data/homepage/`
- `*.bak.*`
- `.runtime/`

## Operational Guidance

- Treat tracked data changes as deploy-state changes and review them before committing.
- Keep ad hoc recovery snapshots under the ignored backup naming patterns instead of mixing them with canonical tracked data.
- Use environment variables or mounted volumes when you want storage outside the repo, but keep the tracked dataset coherent enough for redeploy fallback.
- Keep `.env` local and publish only `.env.example`.
