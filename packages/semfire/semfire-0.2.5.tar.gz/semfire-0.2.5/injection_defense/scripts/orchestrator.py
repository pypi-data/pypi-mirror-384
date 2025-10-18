#!/usr/bin/env python3
import os
import sys
import json
import openai

def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: orchestrator.py \"<user prompt>\"")
    user_prompt = sys.argv[1]
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit("Error: OPENAI_API_KEY not set")
    openai.api_key = api_key
    allowed_actions = ["add", "multiply"]
    system_prompt = (
        "You are a privileged orchestrator. Given the user request, "
        "choose one of the allowed actions and output a JSON object with "
        "format: {\"action\": <action_name>, \"args\": {\"a\": number, \"b\": number}} "
        "without extra keys or explanation."
    )
    user = f"Allowed actions: {allowed_actions}. User says: \"{user_prompt}\"."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user},
        ],
        temperature=0,
    )
    content = response.choices[0].message.content.strip()
    try:
        plan = json.loads(content)
    except json.JSONDecodeError:
        sys.exit(f"Failed to parse JSON from LLM response: {content}")
    print(json.dumps(plan))

if __name__ == "__main__":
    main()