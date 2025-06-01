import asyncio
import argparse
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from openrouter_llm import ask_llm

class MCPSQLiteAgent:
    def __init__(self, debug=False):
        self.debug = debug

    def debug_print(self, *args, **kwargs):
        if self.debug:
            print("[DEBUG]", *args, **kwargs)

async def agent_loop(debug=False):
    async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # Get schema for LLM context
            tools = await session.list_tools()
            schema_result = await session.read_resource("schema://main")
            schema = schema_result.contents[0].text if hasattr(schema_result.contents[0], 'text') else str(schema_result)
            print("MCP Smart Agent connected. Type your question or 'exit' to quit.")
            while True:
                user_input = input("\n> ").strip()
                if user_input.lower() in ("exit", "quit"):
                    print("Goodbye!")
                    break
                if not user_input:
                    continue
                # Multi-step LLM planning loop
                messages = [
                    {"role": "system", "content": (
                        "You are an intelligent agent with access to tools. Always respond in JSON format.\n"
                        "Available tools:\n"
                        "- query_database: Run an SQL query against the database.\n"
                        "The SQLite schema is as follows:\n" + schema + "\n"
                        "When you need to use a tool, respond ONLY with a JSON object like this:\n"
                        '{"tool": "tool_name", "input": "input string"}.\n'
                        "If you have enough information to answer, respond ONLY with a JSON object like this:\n"
                        '{"answer": "your answer here"}.\n'
                        "Do not include any other text in your response.\n"
                        "If you do not understand the question or cannot comply, respond with: {\"error\": \"I cannot comply\"}."
                    )},
                    {"role": "user", "content": user_input}
                ]
                # Add conversation memory: keep only user questions and final answers
                if 'conversation_history' not in locals():
                    conversation_history = []
                # Prepend conversation history to messages
                full_messages = conversation_history + messages
                for step in range(5):
                    llm_response = ask_llm(full_messages)
                    if debug:
                        print(f"[DEBUG] LLM step {step+1} response: {llm_response}")
                    try:
                        import json
                        data = json.loads(llm_response)
                    except Exception:
                        full_messages.append({"role": "assistant", "content": "Your response was not in the required JSON format. Please try again."})
                        continue
                    if "error" in data:
                        print(f"Agent error: {data['error']}")
                        break
                    if "tool" in data:
                        tool_name = data["tool"]
                        tool_input = data.get("input", "")
                        if tool_name == "query_database":
                            tool_result = await session.call_tool("query_database", {"sql": tool_input})
                            if debug:
                                print(f"[DEBUG] Tool result: {tool_result}")
                            # Do NOT add tool call/results to conversation history
                            full_messages.append({"role": "assistant", "content": llm_response})
                            full_messages.append({"role": "user", "content": f"Tool result: {tool_result}"})
                        else:
                            print(f"Unknown tool: {tool_name}")
                            break
                    elif "answer" in data:
                        print(f"Answer: {data['answer']}")
                        # Only add user question and final answer to conversation history
                        conversation_history.append({"role": "user", "content": user_input})
                        conversation_history.append({"role": "assistant", "content": llm_response})
                        # Keep only the last 20 messages (10 Q&A pairs)
                        conversation_history = conversation_history[-20:]
                        break
                    else:
                        print(f"Unexpected LLM response: {llm_response}")
                        break
                else:
                    print("[Agent Error] Too many tool-use steps.")
                # Update conversation history for next user turn
                conversation_history = full_messages[-20:]  # keep last 20 messages for context

def main():
    parser = argparse.ArgumentParser(description="MCP SQLite Agent")
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()

    debug = args.debug
    # Pass debug flag to agent logic
    asyncio.run(agent_loop(debug=debug))

if __name__ == "__main__":
    main()
