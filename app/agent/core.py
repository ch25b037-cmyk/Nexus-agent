# app/agent/core.py
import json
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from groq import Groq
from sqlalchemy.orm import Session

from app.agent.schemas import AGENT_TOOLS
from app.agent.tools import (
    search_jobs_semantic, get_top_skills, get_job_by_id,
    filter_jobs_parametric, analyze_skill_gap, get_highest_paying_roles
)
from app.utils.cost_tracker import track_tokens
from typing import Optional

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

AGENT_SYSTEM_PROMPT = """You are NEXUS, an autonomous Career Intelligence Agent.
You have access to a live database of career opportunities through specialized tools.

GUIDELINES:
1. Always use tools to query the database when the user asks about jobs, skills, or specific roles. Do NOT make up job listings or skill counts.
2. If the user asks for jobs related to a tech stack or profile, call `search_jobs_semantic`.
3. If the user asks about in-demand skills, call `get_top_skills`.
4. If the user asks for details or links for a specific job, call `get_job_by_id`.
5. Keep your tone professional, encouraging, and actionable. Provide concrete guidance for students and job seekers.
"""



def execute_tool_call(db: Session, tool_name: str, tool_args: dict) -> Any:
    """Safely dispatches tool calls from the LLM to local Python functions."""
    if tool_name == "search_jobs_semantic":
        return search_jobs_semantic(db, query=tool_args.get("query", ""), limit=tool_args.get("limit", 5))
    elif tool_name == "get_top_skills":
        return get_top_skills(db, limit=tool_args.get("limit", 5))
    elif tool_name == "get_job_by_id":
        return get_job_by_id(db, job_id=tool_args.get("job_id", 0))
    elif tool_name == "filter_jobs_parametric":
        return filter_jobs_parametric(db, category=tool_args.get("category"), remote_only=tool_args.get("remote_only", False), limit=tool_args.get("limit", 5))
    elif tool_name == "analyze_skill_gap":
        return analyze_skill_gap(db, job_id=tool_args.get("job_id", 0), candidate_skills=tool_args.get("candidate_skills", []))
    elif tool_name == "get_highest_paying_roles":
        return get_highest_paying_roles(db, limit=tool_args.get("limit", 5))
    else:
        return {"error": f"Unknown tool: {tool_name}"}

# In app/agent/core.py:

def run_agent_turn(db: Session, conversation_history: List[Dict[str, Any]], user_message: str, max_steps: int = 10,user_id: Optional[int] = None   # <-- Add user_id!
) -> str:
    """
    Executes an autonomous ReAct loop:
    Guarantees all messages in conversation_history are standard Python dicts for FastAPI JSON serialization.
    """
    conversation_history.append({"role": "user", "content": user_message})

    for step in range(max_steps):
        messages = [{"role": "system", "content": AGENT_SYSTEM_PROMPT}] + conversation_history

        response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            tools=AGENT_TOOLS,
            tool_choice="auto",
            temperature=0.2
        )
        track_tokens("agent", "openai/gpt-oss-120b", getattr(response, "usage", None), user_id=user_id)
        response_message = response.choices[0].message

        # If the model wants to call one or more tools
        if response_message.tool_calls:
            # Convert tool_calls into clean Python dicts for FastAPI/Pydantic
            tool_calls_payload = []
            for tc in response_message.tool_calls:
                tool_calls_payload.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                })

            # Append as a pure Python dictionary (NOT a raw SDK object!)
            conversation_history.append({
                "role": "assistant",
                "content": response_message.content or "",
                "tool_calls": tool_calls_payload
            })

            # Execute each tool
            for tool_call in response_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                print(f"\n[⚡ Agent Action - Step {step + 1}] Calling tool: '{tool_name}' with args: {tool_args}")

                tool_result = execute_tool_call(db, tool_name, tool_args)

                # Append tool result as a pure dictionary
                conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": json.dumps(tool_result)
                })
        else:
            # Final answer reached: append and return
            final_answer = response_message.content or "Here is the information you requested."
            conversation_history.append({"role": "assistant", "content": final_answer})
            return final_answer

    fallback = "I gathered the database information but hit the maximum reasoning steps. Please refine your query."
    conversation_history.append({"role": "assistant", "content": fallback})
    return fallback
