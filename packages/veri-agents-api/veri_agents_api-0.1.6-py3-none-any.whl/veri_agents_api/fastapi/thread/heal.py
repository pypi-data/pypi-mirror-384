from typing import Any, cast
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage

def heal_missing_tool_results(state) -> tuple[Any, bool]:
    messages = cast(list[BaseMessage], state.pop("messages", []))

    modified = False

    normalized_messages = []
    seen_tcs = set()
    for i, message in enumerate(messages):
        normalized_messages.append(message)

        if isinstance(message, AIMessage):
            for tc in message.tool_calls:
                seen_tcs.add(tc["id"])

                next_msg = messages[i+1] if i+1 < len(messages) else None

                if not (isinstance(next_msg, ToolMessage) and next_msg.tool_call_id == tc["id"]):
                    # no tool call result, so inject dummy result
                    normalized_messages.append(
                        ToolMessage(
                            tool_call_id=tc["id"],
                            name=tc["name"],
                            content="⚠️ Tool execution missing; auto-injected failure."
                        )
                    )
                    modified = True

    return { **state, "messages": normalized_messages }, modified
