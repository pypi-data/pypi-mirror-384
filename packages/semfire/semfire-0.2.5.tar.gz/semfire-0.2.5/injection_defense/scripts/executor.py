#!/usr/bin/env python3
import sys
import json

def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: executor.py '<plan_json>'")
    try:
        plan = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        sys.exit(f"Invalid JSON plan: {e}")
    action = plan.get("action")
    args = plan.get("args", {})
    a = args.get("a")
    b = args.get("b")
    if action == "add":
        result = add(a, b)
    elif action == "multiply":
        result = multiply(a, b)
    else:
        sys.exit(f"Unknown action: {action}")
    print(result)

if __name__ == "__main__":
    main()