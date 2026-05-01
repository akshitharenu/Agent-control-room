import httpx
import os
import json
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

CONTROL_ROOM_URL = "https://agent-backend-ym1n.onrender.com"
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

# --- Tools ---
def web_search(query: str) -> str:
    return f"Search results for '{query}': Found relevant information."

def calculator(expression: str) -> str:
    try:
        # Basic sanitization
        safe_expr = expression.replace("^", "**")
        return str(eval(safe_expr, {"__builtins__": None}, {}))
    except Exception as e:
        return f"Error in calculation: {str(e)}"

def get_weather(city: str) -> str:
    return json.dumps({
        "city": city,
        "temperature": "38°C",
        "condition": "Sunny",
        "humidity": "45%"
    })

tool_functions = {
    "web_search": web_search,
    "calculator": calculator,
    "get_weather": get_weather
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Search query"}},
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Perform mathematical calculations",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "Math expression e.g. 25 * 48"}},
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a city",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string", "description": "City name"}},
                "required": ["city"]
            }
        }
    }
]

def log_to_control_room(endpoint: str, data: dict):
    try:
        httpx.post(f"{CONTROL_ROOM_URL}{endpoint}", json=data)
    except Exception as e:
        print(f"Logging error: {e}")

def run_agent(prompt: str, intent: str = None) -> dict:
    print(f"\n🤖 Agent starting for: {prompt}")
    
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        print("❌ Error: NVIDIA_API_KEY not found in environment")
        return {"error": "NVIDIA_API_KEY missing"}

    res = httpx.post(f"{CONTROL_ROOM_URL}/runs/start", json={
        "agent_name": "NVIDIA_Agent",
        "prompt": prompt,
        "intent": intent
    })
    run_id = res.json()["run_id"]
    print(f"📋 Run ID: {run_id}")

    messages = [{"role": "user", "content": prompt}]
    if intent:
        messages.insert(0, {"role": "system", "content": f"Your intent is: {intent}"})

    total_tokens = 0
    step = 1
    final_response = ""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    while True:
        payload = {
            "model": "meta/llama-3.1-70b-instruct",
            "messages": messages,
            "tools": tools,
            "temperature": 0.2,
            "max_tokens": 1024
        }

        log_to_control_room("/runs/log-event", {
            "run_id": run_id,
            "event_type": "agent_thinking",
            "data": {"status": "Agent is thinking..."},
            "step_number": step
        })

        try:
            print(f"📡 Calling NVIDIA API (Step {step})...")
            response = httpx.post(NVIDIA_API_URL, json=payload, headers=headers, timeout=60.0)
            response.raise_for_status()
            res_data = response.json()
        except Exception as e:
            error_msg = f"NVIDIA API Error: {str(e)}"
            if hasattr(e, 'response') and e.response:
                error_msg += f" | Details: {e.response.text}"
            print(f"❌ {error_msg}")
            log_to_control_room("/runs/finish", {
                "run_id": run_id,
                "status": "failed",
                "total_tokens": total_tokens,
                "total_cost": 0.0,
                "error": error_msg
            })
            return {"run_id": run_id, "error": error_msg}

        choice = res_data["choices"][0]
        message = choice["message"]
        usage = res_data.get("usage", {})
        tokens = usage.get("total_tokens", 0)
        total_tokens += tokens

        log_to_control_room("/runs/log-event", {
            "run_id": run_id,
            "event_type": "llm_call",
            "data": {
                "model": "meta/llama-3.1-70b-instruct", 
                "tokens": tokens, 
                "cost": 0.0
            },
            "step_number": step
        })
        step += 1

        tool_calls = message.get("tool_calls")
        if tool_calls:
            # Add assistant message to history
            messages.append(message)

            for tool_call in tool_calls:
                function_name = tool_call["function"]["name"]
                try:
                    arguments = json.loads(tool_call["function"]["arguments"])
                except:
                    arguments = {}
                
                # execute tool
                if function_name in tool_functions:
                    try:
                        result = tool_functions[function_name](**arguments)
                    except Exception as e:
                        result = str(e)
                else:
                    result = f"Error: Tool {function_name} not found"
                
                # log tool call WITH output
                log_to_control_room("/runs/log-event", {
                    "run_id": run_id,
                    "event_type": "tool_call",
                    "data": {
                        "tool": function_name,
                        "input": arguments,
                        "output": {"result": result}
                    },
                    "step_number": step
                })
                step += 1
                
                # append result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result
                })
        else:
            final_response = message.get("content", "")
            break

    log_to_control_room("/runs/finish", {
        "run_id": run_id,
        "status": "success",
        "total_tokens": total_tokens,
        "total_cost": 0.0
    })

    return {
        "run_id": run_id,
        "response": final_response,
        "total_tokens": total_tokens,
        "total_cost": 0.0
    }