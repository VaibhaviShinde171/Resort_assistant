# agents.py
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from tools import all_tools

# load environment
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Create LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """You are a concise Resort Booking Assistant.
Always use available tools to answer user requests.
- For booking requests, call add_booking_tool with the user's full sentence.
- For listing rooms, call view_rooms_tool.
- For viewing bookings, call view_bookings_tool.
- For cancelling, call cancel_booking_tool with the customer's name.
- For bills, call generate_bill_tool with the customer's name.
- For resort info, call resort_info_tool.
Non-Resort Questions:
- If the user asks ANYTHING unrelated to resort operations,
  use `tavily_tool` to search the web and answer.

Always try to use tools wherever possible.
Return only the final tool output.
Return only the tool output as the final response when possible.
"""

agent = create_agent(llm, tools=all_tools, system_prompt=SYSTEM_PROMPT)


# a helper function to get the desired output format.
def _extract_text(result) -> str:
    """
    Robust extraction from agent.invoke output.
    Accepts dict with 'messages' (objects or dicts), or plain strings.
    """
    if isinstance(result, dict) and "messages" in result:
        msgs = result["messages"]
        for m in reversed(msgs):
            if isinstance(m, dict) and "content" in m:
                return m["content"]
            if hasattr(m, "content"):
                return m.content
        return str(msgs)
    if isinstance(result, dict):
        return result.get("output") or result.get("text") or str(result)
    return str(result)


def run_agent(user_input: str) -> str:
    """
    Send user input to the LLM agent and return cleaned content for UI.
    """
    
    try:
        payload = {"messages": [{"role": "user", "content": user_input}]}
        result = agent.invoke(payload)
    except Exception:
        result = agent.invoke({"input": user_input})
    return _extract_text(result)
