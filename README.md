# sage-faculty-twin

`sage-faculty-twin` is designed as one scholar's own digital twin system, not a generic faculty
support bot.
In this repository the default identity is Zhang Shuhao's teaching-and-research workflow: students
can ask a question, sketch an agenda, or start a booking request, and the system responds with
grounded guidance instead of a blank chatbot.

Under the hood it combines a FastAPI surface, SAGE workflow orchestration, NeuroMem-backed memory,
and an OpenAI-compatible LLM endpoint to answer questions, guide meeting preparation, and manage a
reviewable booking flow.

This repository is prepared for publication under the IntelliStream organization, but the product
framing stays personal-first: it should feel like one person's working academic twin. If you fork
it for someone else, replace the owner identity, homepage content, and persona profile first.

Release planning for the organization baseline lives in [ROADMAP.md](ROADMAP.md).

## What It Does

- Answers student questions with persona, policy, and retrieval-aware workflow routing.
- Supports office-hour and meeting booking with availability rules, admin review, and follow-up.
- Maintains short-term conversation memory and long-term student profile memory with NeuroMem.
- Imports offline knowledge from homepage content, course pages, PDFs, and curated FAQ notes.
- Exposes admin panels for knowledge, bookings, escalations, memory profiles, analytics, and
  service lifecycle control.

In practice, that means the repo is built to feel less like "chat with a model" and more like
"walk into a prepared academic office": the assistant can say what to bring, what it knows, what
still needs human approval, and what should happen next.

## Why It's Different

- It treats student support like an office workflow, not a one-shot chat completion.
- It keeps answer basis, follow-up actions, and booking review visible instead of hiding system
  behavior behind a black box.
- It combines offline knowledge sync with conversation memory, so repeated questions can feel
  contextual without depending on live scraping.
- It is built to stop at the right boundary: the avatar can prepare, recommend, and route, while
  sensitive approvals still stay with the human owner.

## Architecture

- `src/sage_faculty_twin/api.py`: FastAPI routes and static web entry points.
- `src/sage_faculty_twin/service.py`: workflow orchestration, answer grounding, and admin actions.
- `src/sage_faculty_twin/knowledge_base.py`: local, NeuroMem, and SageVDB knowledge retrieval.
- `src/sage_faculty_twin/memory_store.py`: conversation and profile memory handling.
- `src/sage_faculty_twin/knowledge_import.py`: offline homepage and course-material ingestion.
- `src/sage_faculty_twin/operations_store.py`: operations-console task status overlay.
- `src/sage_faculty_twin/web/`: browser UI for students and admins.

For the original product framing, see [docs/product-outline.md](docs/product-outline.md).

## Quick Start

Use an existing non-venv Python environment.

```bash
cd /path/to/sage-faculty-twin
python -m pip install -e .[dev]
cp .env.example .env
PYTHONPATH="$PWD/src:$PWD/../SAGE/src:$PWD/../neuromem:$PWD/../sageVDB" \
python -m uvicorn sage_faculty_twin.api:app --reload
```

Then open `http://127.0.0.1:8000/docs` for the API schema or the root page for the chat UI.

The extra `PYTHONPATH` entries are only needed when you want to import sibling source checkouts
directly instead of installed wheels.

If you change frontend assets, auth routes, or session logic while a local server is already
running, restart the app process before testing again. Otherwise the browser may still be talking
to an older process that does not include your latest endpoints or UI behavior.

## Try It Like This

Once the app is up, a few prompts that show the product shape quickly are:

- `和老师约时间前，我应该先准备什么？`
- `帮我预约下周三下午讨论论文提纲，我会带 draft 和问题清单。`
- `我之前提到过的研究主题是什么？`
- `大模型推理引擎 Tutorial 7 主要讲了什么，我应该先看哪部分？`
- `数据库实验课开始前，我应该先准备哪些环境和材料？`

These tend to exercise the answer-basis panel, recent-memory reuse, follow-up actions, and the
booking or review routing logic in one pass.

## Demo Flow

If you want the shortest path to seeing the product shape, use this order:

1. Ask a preparation question such as `和老师约时间前，我应该先准备什么？` to see grounded answers
   plus follow-up suggestions.
2. Ask for a meeting with a bit of context such as `帮我预约下周三下午讨论论文提纲，我会带 draft 和问题清单。`
   to trigger booking intent, preparation hints, and reviewable request output.
3. Ask a continuity question such as `我之前提到过的研究主题是什么？` to verify recent-memory reuse.
4. Open the admin side to inspect the same interaction from the operations view: bookings,
   knowledge updates, service status, and escalation surfaces.

## Configuration

The app reads configuration from environment variables prefixed with `DIGITAL_TWIN_`.
The most important values are:

- `DIGITAL_TWIN_OWNER_NAME`: the real person this twin stands in for.
- `DIGITAL_TWIN_OWNER_ROLE`: that person's role label in prompts and UI copy.
- `DIGITAL_TWIN_LLM_BASE_URL`: OpenAI-compatible LLM endpoint.
- `DIGITAL_TWIN_API_KEY`: optional API key for the LLM endpoint.
- `DIGITAL_TWIN_KNOWLEDGE_BACKEND`: `neuromem`, `local`, or `sagevdb`.
- `DIGITAL_TWIN_HOMEPAGE_DIR`: local homepage export used for offline sync or `/home/` serving.
- `DIGITAL_TWIN_HOMEPAGE_PUBLIC_URL`: canonical public homepage URL shown in the top bar.
- `DIGITAL_TWIN_AVAILABILITY_SCHEDULE_PATH`: weekly availability JSON file.
- `DIGITAL_TWIN_BOOKING_NOTIFICATION_EMAIL`: mailbox that receives booking notifications.
- `DIGITAL_TWIN_ADMIN_USERNAME`, `DIGITAL_TWIN_ADMIN_PASSWORD`,
  `DIGITAL_TWIN_ADMIN_SESSION_SECRET`: admin access settings.

See [.env.example](.env.example) for a starter configuration.

## Knowledge and Memory

The repository supports an offline-first knowledge flow:

1. Import homepage content, course pages, and PDFs into the local knowledge store.
2. Persist searchable knowledge records under the configured knowledge directory.
3. Query the persisted store during chat instead of re-reading source repositories online.

To import homepage knowledge offline:

```bash
cd /path/to/sage-faculty-twin
PYTHONPATH="$PWD/src:$PWD/../SAGE/src:$PWD/../neuromem" \
python -m sage_faculty_twin.knowledge_import \
  --homepage-dir /path/to/homepage-repo \
  --knowledge-dir data/knowledge_base \
  --knowledge-backend neuromem
```

The chat workflow also stores:

- short-term conversation memory for same-thread follow-up,
- long-term student profile memory for stable preferences and recurring context,
- booking preference summaries and collaboration-style summaries.

## Local Operations

Useful entry points:

```bash
./manage.sh status
./manage.sh install --start
./tools/run_app_server.sh
./tools/run_local_site.sh
./tools/run_named_tunnel.sh
```

When you run the managed local services, use `./manage.sh restart` after changing frontend files,
auth handlers, or other runtime-loaded app code. If you are running `uvicorn` directly instead,
stop it and start it again before validating the change in the browser.

Deployment and operations details are documented in [docs/deployment.md](docs/deployment.md).
The admin operations-console flow is documented in [docs/ops-console.md](docs/ops-console.md).

## Runtime Data Boundaries

This repository intentionally keeps versioned templates separate from runtime-generated state.
Tracked templates include:

- `data/persona/style_profile.md`
- `data/availability/current_week.json`

Ignored runtime directories include generated knowledge, conversation memory, escalations,
follow-up queues, homepage exports, and local runtime artifacts.

See [docs/runtime-data.md](docs/runtime-data.md) for the full boundary and backup guidance.

## Roadmap

The repository-level release baseline and next-step product plan are summarized in
[ROADMAP.md](ROADMAP.md). For the longer product direction, see
[docs/product-outline.md](docs/product-outline.md).

## Development

Run targeted tests with the local source tree on `PYTHONPATH`:

```bash
cd /path/to/sage-faculty-twin
PYTHONPATH=src pytest tests/
```

For contribution expectations, see [CONTRIBUTING.md](CONTRIBUTING.md).
