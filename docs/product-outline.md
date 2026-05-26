# Product Outline

## Vision

Build an always-on academic avatar that can represent the owner in routine student interactions
without pretending to replace the human for sensitive decisions.

## Primary User Journeys

1. A student asks a question about course logistics, reading advice, office hours, or research.
2. A student asks whether a meeting can be booked for a given topic and time window.
3. The assistant proposes available slots, collects context, and creates a booking request.

## Non-Goals for the First MVP

- No autonomous grade changes or policy exceptions.
- No hidden chain of tools that silently edits real calendars.
- No attempt to answer with confidential student data.

## System Shape

- `api.py`: HTTP contract.
- `service.py`: orchestration for question answering and booking.
- `llm_client.py`: thin OpenAI-compatible client for `vllm-hust`.
- `meeting.py`: deterministic booking rules and in-memory storage.
- `persona.py`: assistant identity and response framing.

## Planned Integrations

- SAGE retrieval pipelines for documents such as syllabi, FAQs, and lab onboarding notes.
- Calendar provider sync.
- Authentication and audit logging.
- Human escalation path for requests the avatar should not decide alone.
