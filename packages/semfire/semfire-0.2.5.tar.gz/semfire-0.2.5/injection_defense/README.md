# injection-defense

This project implements a general-purpose “LLM firewall” to defend against prompt injection attacks.

See docs/ROADMAP.md for the full plan and roadmap.

## Step 1: Minimal Prototype – Action-Selector

In this step, we implement a basic Action-Selector agent that can perform safe mathematical operations (addition and multiplication) based on the user request.

### Requirements
- Python 3.7+
- openai (see requirements.txt)
- Set the environment variable `OPENAI_API_KEY` for the OpenAI API.

### Usage
1. Orchestrator: choose an action plan without execution.
   ```bash
   python3 scripts/orchestrator.py "<user prompt>"
   ```
   Example:
   ```bash
   python3 scripts/orchestrator.py "What is 5 plus 3?"
   ```
   Output:
   ```json
   {"action": "add", "args": {"a": 5, "b": 3}}
   ```

2. Executor: execute the plan.
   ```bash
   python3 scripts/executor.py '{"action": "add", "args": {"a":5,"b":3}}'
   ```
   Output:
   ```
   8
   ```

## GitHub Project Setup

To automate creation of GitHub Issues, labels, and a Kanban project board:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set environment variables:
   ```bash
   export GITHUB_TOKEN=<token-with-repo-access>
   export GITHUB_REPOSITORY=<owner/repo>
   ```
   Optionally, store them in a `.env` file and load with:
   ```bash
   echo "GITHUB_TOKEN=<token>" > .env
   echo "GITHUB_REPOSITORY=<owner/repo>" >> .env
   source .env
   ```
   `.env` is already added to `.gitignore` to prevent accidental commits.
3. Run the setup script:
   ```bash
   python3 scripts/setup_github_board.py
   ```

Alternatively, you can copy–paste these CLI commands into your shell to create the Step 1 issues (one at a time; ensure you've run `gh auth login` and are in the correct repo directory):

```bash
gh issue create \
  --title "Step 1: Minimal Prototype – Action-Selector" \
  --body "Implement scripts/orchestrator.py and scripts/executor.py for basic add/multiply prototype." \
  --label roadmap-step-1,type:feature

gh issue create \
  --title "Step 1.1: Harden Orchestrator JSON-Plan Validation" \
  --body "Add validation in orchestrator to reject plans missing or extra keys (action, args[a,b])." \
  --label roadmap-step-1,security,type:feature

gh issue create \
  --title "Step 1.2: Harden Executor Args Validation" \
  --body "Add validation in executor to reject args objects missing or extra keys (a, b)." \
  --label roadmap-step-1,security,type:feature
```

To add each issue directly to the “LLM Firewall Roadmap” project in the Backlog column, append `--project "LLM Firewall Roadmap"` to each command.
