# Runtime Data Boundary

This repository is intended to be publishable as source code under the IntelliStream organization.
That means runtime-generated state should stay out of version control.

## Versioned Templates

These files are designed to stay in the repository as safe defaults or templates:

- `data/persona/style_profile.md`
- `data/availability/current_week.json`
- `tools/cloudflared-config.example.yml`

## Ignored Runtime State

These directories are generated or mutated while the app runs and should not be committed:

- `data/knowledge_base/`
- `data/homepage/`
- `data/conversation_memory/`
- `data/knowledge_gap_drafts/`
- `data/escalations/`
- `data/follow_up_actions/`
- `data/operations_task_state/`
- `data/user_accounts/`
- `.runtime/`

## Operational Guidance

- Treat the tracked availability file as a template or development sample, not a production schedule.
- Use environment variables to point production deployments at external volumes or mounted storage.
- Back up generated knowledge and conversation memory outside the Git repository.
- Keep `.env` local and publish only `.env.example`.