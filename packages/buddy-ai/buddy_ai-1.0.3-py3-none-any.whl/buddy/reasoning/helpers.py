from typing import Any, Dict, List, Literal, Optional

from buddy.models.base import Model
from buddy.models.message import Message
from buddy.reasoning.step import NextAction, ReasoningStep
from buddy.run.messages import RunMessages
from buddy.utils.log import logger


def get_reasoning_agent(
    reasoning_model: Model,
    monitoring: bool = False,
    telemetry: bool = False,
    debug_mode: bool = False,
    debug_level: Literal[1, 2] = 1,
    session_state: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
    extra_data: Optional[Dict[str, Any]] = None,
) -> "Agent":  # type: ignore  # noqa: F821
    from buddy.agent import Agent

    return Agent(
        model=reasoning_model,
        monitoring=monitoring,
        telemetry=telemetry,
        debug_mode=debug_mode,
        debug_level=debug_level,
        session_state=session_state,
        context=context,
        extra_data=extra_data,
    )


def get_next_action(reasoning_step: ReasoningStep) -> NextAction:
    next_action = reasoning_step.next_action or NextAction.FINAL_ANSWER
    if isinstance(next_action, str):
        try:
            return NextAction(next_action)
        except ValueError:
            logger.warning(f"Reasoning error. Invalid next action: {next_action}")
            return NextAction.FINAL_ANSWER
    return next_action


def update_messages_with_reasoning(
    run_messages: RunMessages,
    reasoning_messages: List[Message],
) -> None:
    run_messages.messages.append(
        Message(
            role="assistant",
            content="I have worked through this problem in-depth, running all necessary tools and have included my raw, step by step research. ",
            add_to_agent_memory=False,
        )
    )
    for message in reasoning_messages:
        message.add_to_agent_memory = False
    run_messages.messages.extend(reasoning_messages)
    run_messages.messages.append(
        Message(
            role="assistant",
            content="Now I will summarize my reasoning and provide a final answer. I will skip any tool calls already executed and steps that are not relevant to the final answer.",
            add_to_agent_memory=False,
        )
    )

