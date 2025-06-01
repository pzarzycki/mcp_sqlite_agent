import os
import json
from tools import get_db_schema, explore_db_schema, query_database
from openrouter_llm import ask_llm

class MCPHost:
    def __init__(self):
        self.schema_cache = None
        self.tools = {
            "get_db_schema": self.get_db_schema,
            "explore_db_schema": self.explore_db_schema,
            "query_database": self.query_database
        }

    def handle_user_input(self, user_input):
        # System prompt describing available tools
        system_prompt = (
            "You are an intelligent agent with access to tools. Always respond in JSON format.\n"
            "Available tools:\n"
            "- get_db_schema: Returns the schema of the SQLite database.\n"
            "- explore_db_schema: Explores the database schema and caches it.\n"
            "- query_database: Run an SQL query against the database (for summaries, statistics, or sample data, use this tool with an appropriate SQL query).\n"
            "When you need to use a tool, respond ONLY with a JSON object like this:\n"
            '{"tool": "tool_name", "input": "input string"}.\n'
            "If you have enough information to answer, respond ONLY with a JSON object like this:\n"
            '{"answer": "your answer here"}.\n'
            "Do not include any other text in your response.\n"
            "If you do not understand the question or cannot comply, respond with: {\"error\": \"I cannot comply\"}."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        for step in range(3):  # Limit to 3 tool-use steps
            print(f"[DEBUG] Step {step + 1}: Sending messages to LLM: {messages}")
            response = ask_llm(messages)
            print(f"[DEBUG] Step {step + 1}: LLM response: {response}")
            try:
                data = json.loads(response)
            except Exception:
                print(f"[DEBUG] Step {step + 1}: Failed to parse LLM response.")
                messages.append({"role": "assistant", "content": "Your response was not in the required JSON format. Please try again."})
                continue
            if "error" in data:
                print(f"[DEBUG] Step {step + 1}: LLM error response: {data['error']}\n")
                return "The agent could not process your request. Please try rephrasing."
            if "tool" in data:
                tool_name = data["tool"]
                tool_input = data.get("input", "")
                print(f"[DEBUG] Step {step + 1}: Calling tool '{tool_name}' with input: {tool_input}")
                if tool_name in self.tools:
                    tool_result = self.tools[tool_name](tool_input)
                    print(f"[DEBUG] Step {step + 1}: Tool result: {tool_result}")
                    messages.append({"role": "assistant", "content": response})
                    messages.append({"role": "user", "content": f"Tool result: {tool_result}"})
                else:
                    return f"[Agent Error] Unknown tool: {tool_name}"
            elif "answer" in data:
                print(f"[DEBUG] Step {step + 1}: Final answer: {data['answer']}")
                return data["answer"]
            else:
                print(f"[DEBUG] Step {step + 1}: Unexpected LLM response: {response}")
                return f"[Agent Error] Unexpected LLM response: {response}"
        print("[DEBUG] Exceeded maximum tool-use steps.")
        # Fallback: Provide a partial answer based on gathered information
        if self.schema_cache:
            return "I couldn't fully explore the database, but here's what I know about its schema: " + str(self.schema_cache)
        return "[Agent Error] Too many tool-use steps."

    def get_db_schema(self, _input=None):
        if self.schema_cache is None:
            self.schema_cache = get_db_schema()
        return self.schema_cache

    def explore_db_schema(self, _input=None):
        self.schema_cache = explore_db_schema()
        return self.schema_cache

    def query_database(self, query):
        return query_database(query)
