"""Print the prompt budget for representative NEXUS requests.

Token counts are estimates based on ~4 characters/token because the Ollama/Qwen
runtime tokenizer is not bundled with the backend. Live [CHAT PERF] logs emit
both exact component character counts and the same clearly-labelled estimate.
"""
import json
from app.agent.prompts import build_plan_system_prompt, build_conversation_system_prompt, compact_ui_context, plan_schema
from app.models import ChatUIContext, ConversationMessage

CTX = ChatUIContext(
    visible_widgets={"analytics": True, "overview": False, "response-time": False},
).model_dump(mode="json")
HISTORY = [
    ConversationMessage(role="user", content="Show analytics."),
    ConversationMessage(role="assistant", content="Analytics panel opened."),
]

def show(request: str) -> None:
    planned = any(token in request.lower() for token in ("accent", "analytics", "widgets", "hide", "show"))
    if planned:
        system = build_plan_system_prompt(request)
        schema = json.dumps(plan_schema(), ensure_ascii=False, separators=(",", ":"))
        context = json.dumps(compact_ui_context(CTX, request), ensure_ascii=False, separators=(",", ":"))
        parts = {"system": len(system), "schema": len(schema), "ui_context": len(context), "history": sum(len(x.content) for x in HISTORY), "current_user": len(request)}
    else:
        system = build_conversation_system_prompt()
        context = json.dumps(compact_ui_context(CTX, request), ensure_ascii=False, separators=(",", ":"))
        parts = {"system": len(system), "schema": 0, "ui_context": len(context), "history": sum(len(x.content) for x in HISTORY), "current_user": len(request)}
    total = sum(parts.values())
    print(request)
    for name, chars in parts.items():
        print(f"  {name:12s} chars={chars:5d}  tokens_est={round(chars/4):4d}")
    print(f"  {'TOTAL':12s} chars={total:5d}  tokens_est={round(total/4):4d}")

for item in ["hey", "What is recursion?", "change the accent color to red", "hide widgets", "show analytics"]:
    show(item)
