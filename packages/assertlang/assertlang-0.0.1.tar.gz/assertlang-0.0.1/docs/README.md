AssertLang

Write once, run anywhere.

AssertLang is a domain-specific language (`.al`) for writing language-agnostic software. Write `.al` code once, run it in Python, Node.js, Go, Rust, .NET, Java, C++, or Next.js — fast, reproducible, and portable. All applications are exposed at a single memorable port: 23456.

⸻

✨ Core Idea
	•	One Port: All user-facing apps are exposed via http://127.0.0.1:23456/apps/<task_id>/.
	•	Five Verbs: A universal micro-language (plan.create, fs.apply, run.start, httpcheck.assert, report.finish).
	•	Ephemeral by Default: Apps are generated, validated, and discarded or patched.
	•	Agent-Native: Built for AI coding agents to deliver software live.
	•	Proof-Oriented: Every run produces artifacts, logs, and a verdict.

⸻

🚀 Quickstart

Install

git clone <repo-url>
cd promptware
make install   # or `pip install -e .` once package is scaffolded

Run a .al file

# Create hello.al
cat > hello.al << 'EOF'
lang python
start python app.py

file app.py:
  from http.server import BaseHTTPRequestHandler, HTTPServer
  class Handler(BaseHTTPRequestHandler):
      def do_GET(self):
          self.send_response(200)
          self.wfile.write(b'Hello, World!')
  if __name__ == '__main__':
      import os
      port = int(os.environ.get('PORT', '8000'))
      server = HTTPServer(('127.0.0.1', port), Handler)
      server.serve_forever()
EOF

# Run it
promptware run hello.al

Output:

✅ PASS: http://127.0.0.1:23456/apps/ab12cd/
Artifacts in .mcpd/ab12cd/


⸻

🛠 Repo Layout

/daemon           # mcpd core (five verbs + gateway)
/runners/python   # Python runner (Flask/FastAPI)
/runners/node     # Node.js runner (Express/Hono)
/runners/go       # Go runner (net/http)
/cli              # CLI tool (mcp)
/schemas          # JSON Schemas for verbs
/tests            # Unit + integration tests
/docs             # Manifesto, Tech Spec Pack, Versioning Policy


⸻

📚 Documentation

See the /docs folder for:
	•	AssertLang Manifesto → vision & principles
	•	Tech Spec Pack → detailed JSON schemas, error codes, CLI spec
	•	Networking Flow → UDS/TCP model, gateway on port 23456, and sandbox fallbacks
	•	Runner Protocol → stdin/stdout envelopes, health checks, failure codes
	•	Dependency Management → per-language setup (venv, npm install, go mod, etc.)
	•	Toolgen Template Catalog → current tool specs and adapter templates
	•	AssertLang DSL Roadmap → grammar milestones, adapter rollout, orchestrator plan
	•	Versioning Principles → what counts as breaking, @v1 policy
	•	Run `python scripts/show_dependency_allowlist.py [--plan plan.json]` to inspect approved dependencies, env overrides, private registries, and plan-level requests

⸻

🔑 Core Commands
	•	promptware run <file.al> → Full pipeline: .al DSL → app → validation
	•	promptware change <task_id> "<delta>" → Apply patch + restart
	•	mcp list → Show tasks, status, URLs
	•	mcp open <task_id> → Open artifacts and preview URL
	•	mcp export <task_id> <dir> → Export source tree
	•	mcp kill <task_id> → Stop and clean up
	•	promptware deps check [--plan plan.json] → Inspect allowlists and merged plan dependencies
	•	promptware deps trim-cache [--dry-run] → Prune dependency caches using allowlist TTL hints
	•	promptware dsl format <path> [--check] → Canonicalise .al files
	•	promptware dsl lint <path> → Surface DSL syntax/semantic issues

⸻

✅ MVP Acceptance Criteria
	•	.al DSL → File Plan → Files → Run → Validate → Report all automated.
	•	First runner: Python (working).
	•	Node.js and Go runners (working).
	•	User sees working endpoint on Port 23456.
	•	Artifacts logged in .mcpd/<task_id>/.

⸻

🧭 Roadmap
	•	M1 (2–3 wks): Python runner + daemon + CLI basics.
	•	M2 (4–6 wks): Node & Go runners, patch flow, artifact index.
	•	M3 (6–10 wks): GitHub Action mode, allowlist, secret scan.
	•	M4 (10–16 wks): Rust runner, managed gateway, auth/RBAC.

⸻

🙌 Contributing
	•	Style: Prettier/ESLint (Node), Black/Ruff (Python), gofmt/go vet (Go)
	•	All new runners must pass the conformance tests in /tests
	•	PRs must include updated schemas if verbs evolve

⸻

Slogan

One port, five verbs, infinite software.
