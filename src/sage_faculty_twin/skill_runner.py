"""Skill runner for the agent skill system.

Executes skills with their multi-turn tool-calling reasoning loops.
The runner manages the conversation between the LLM and tool handlers,
feeding tool results back to the model until a final answer is produced
or max turns is reached.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from .skills import SkillContext, SkillDefinition, SkillResult

if TYPE_CHECKING:
    from .llm_client import VllmChatClient
    from .skill_tools import SkillToolRegistry

logger = logging.getLogger(__name__)


class SkillRunner:
    """Executes skills with multi-turn tool-calling agent loops."""

    def __init__(
        self,
        llm_client: VllmChatClient,
        tool_registry: SkillToolRegistry,
    ) -> None:
        self._llm = llm_client
        self._tools = tool_registry

    def run(self, skill: SkillDefinition, context: SkillContext) -> SkillResult:
        """Execute a skill's multi-turn reasoning loop.

        The loop works as follows:
        1. Build initial messages from skill's system prompt and user prompt template
        2. Call LLM with the skill's tool definitions
        3. If LLM returns tool_calls, execute them and append results to messages
        4. Repeat until LLM returns a final text answer or max_turns is reached

        Args:
            skill: The skill definition to execute.
            context: Runtime context with the user's question and profile.

        Returns:
            SkillResult with the final answer and execution metadata.
        """
        # Build initial messages
        try:
            user_content = skill.user_prompt_template.format(
                question=context.question,
                profile=context.visitor_profile,
                retrieved_context=context.pre_fetched_context or "(no pre-fetched context)",
                course=context.course_context or "(no course context)",
            )
        except KeyError as exc:
            return SkillResult(
                skill_id=skill.skill_id,
                success=False,
                error=f"Missing template variable: {exc}",
            )

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": skill.system_prompt},
            {"role": "user", "content": user_content},
        ]

        # Convert skill tools to OpenAI format
        openai_tools = [tool.to_openai_tool() for tool in skill.tools]

        # If no tools, do a single-turn call
        if not openai_tools:
            return self._run_no_tools(skill, messages, context)

        # Multi-turn tool-calling loop
        tool_calls_made = 0
        turns_used = 0

        for turn in range(skill.max_turns):
            turns_used = turn + 1
            try:
                response = self._llm.chat_with_tools_sync(
                    messages=messages,
                    tools=openai_tools,
                    temperature=0.2,
                    tool_choice="auto",
                )
            except Exception as exc:
                logger.warning("Skill %s LLM call failed on turn %d: %s", skill.skill_id, turn, exc)
                return SkillResult(
                    skill_id=skill.skill_id,
                    success=False,
                    error=f"LLM call failed: {exc}",
                    turns_used=turns_used,
                )

            # Check if we have tool calls
            tool_calls = response.get("tool_calls", [])
            content = response.get("content")

            if tool_calls:
                # Execute each tool call and append results
                for call in tool_calls:
                    tool_calls_made += 1
                    call_id = call.get("id", f"call_{tool_calls_made}")
                    tool_name = call.get("name", "")
                    arguments = call.get("arguments", {})

                    logger.debug(
                        "Skill %s calling tool %s with args: %s",
                        skill.skill_id,
                        tool_name,
                        arguments,
                    )

                    # Find the handler name from skill tool definitions
                    handler_name = self._resolve_handler(skill, tool_name)
                    if handler_name is None:
                        result = json.dumps({"error": f"Unknown tool: {tool_name}"})
                    else:
                        result = self._tools.execute(handler_name, arguments)

                    # Append assistant message with tool call
                    messages.append({
                        "role": "assistant",
                        "content": content or "",
                        "tool_calls": [{
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(arguments),
                            },
                        }],
                    })

                    # Append tool result
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": result,
                    })
            else:
                # No tool calls - we have our final answer
                final_answer = content or ""
                logger.info(
                    "Skill %s completed in %d turns with %d tool calls",
                    skill.skill_id,
                    turns_used,
                    tool_calls_made,
                )
                return SkillResult(
                    skill_id=skill.skill_id,
                    answer=final_answer,
                    tool_calls_made=tool_calls_made,
                    turns_used=turns_used,
                    output_format=skill.output_format,
                    success=True,
                )

        # Max turns reached without final answer
        logger.warning(
            "Skill %s reached max turns (%d) without final answer",
            skill.skill_id,
            skill.max_turns,
        )
        return SkillResult(
            skill_id=skill.skill_id,
            answer="[Skill execution reached maximum turns without producing a final answer]",
            tool_calls_made=tool_calls_made,
            turns_used=turns_used,
            output_format=skill.output_format,
            success=False,
            error="Max turns reached",
        )

    def _run_no_tools(
        self,
        skill: SkillDefinition,
        messages: list[dict[str, Any]],
        context: SkillContext,
    ) -> SkillResult:
        """Run a skill without tools (single-turn)."""
        system_prompt = messages[0]["content"]
        user_prompt = messages[1]["content"]

        try:
            answer = self._llm.answer_question_sync(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2,
                enable_thinking=False,
            )
            return SkillResult(
                skill_id=skill.skill_id,
                answer=answer,
                tool_calls_made=0,
                turns_used=1,
                output_format=skill.output_format,
                success=True,
            )
        except Exception as exc:
            logger.warning("Skill %s no-tools call failed: %s", skill.skill_id, exc)
            return SkillResult(
                skill_id=skill.skill_id,
                success=False,
                error=f"LLM call failed: {exc}",
            )

    def _resolve_handler(self, skill: SkillDefinition, tool_name: str) -> str | None:
        """Resolve a tool name to its handler name from skill definitions."""
        for tool_def in skill.tools:
            if tool_def.name == tool_name:
                return tool_def.handler
        return None
