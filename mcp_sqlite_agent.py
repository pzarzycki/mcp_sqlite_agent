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
                # Dynamically build tool list for prompt
                tool_lines = []
                for tool in tools:
                    if isinstance(tool, dict):
                        name = tool.get('name', str(tool))
                        desc = tool.get('description', '')
                    elif isinstance(tool, (tuple, list)):
                        name = tool[0] if len(tool) > 0 else str(tool)
                        desc = tool[1] if len(tool) > 1 else ''
                    else:
                        name = str(tool)
                        desc = ''
                    if desc:
                        tool_lines.append(f"- {name}: {desc}")
                    else:
                        tool_lines.append(f"- {name}")
                tool_list_str = '\n'.join(tool_lines)
                # Multi-step LLM planning loop
                # Gather tool usage examples from MCP if available
                example_lines = []
                for tool in tools:
                    # Only process if tool is a dict and has examples
                    if isinstance(tool, dict) and tool.get('examples'):
                        for ex in tool['examples']:
                            user = ex.get('user') or ex.get('input')
                            assistant = ex.get('assistant') or ex.get('output')
                            if user and assistant:
                                example_lines.append(f"User: {user}\nAssistant: {assistant}")
                examples_str = '\n'.join(example_lines)

                system_prompt = f"""
You are an intelligent agent with access to tools. Always respond in JSON format.
Available tools:
{tool_list_str}
The SQLite schema is as follows:
{schema}
When you need to use a tool, respond ONLY with a JSON object like this:
{{"tool": "tool_name", "input": "input string"}}.
If you have enough information to answer, respond ONLY with a JSON object like this:
{{"answer": "your answer here"}}.
Do not include any other text in your response.
If you do not understand the question or cannot comply, respond with: {{"error": "I cannot comply"}}.

# Examples of tool use:
{examples_str}
Always use a tool if the answer requires data from the database. Only answer directly if you are absolutely certain you do not need to use a tool.
"""
                messages = [
                    {"role": "system", "content": system_prompt},
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
