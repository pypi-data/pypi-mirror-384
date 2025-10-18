lang python
agent code-reviewer
port 23450
llm anthropic claude-3-5-sonnet-20241022

observability:
  traces: true
  metrics: true
  logs: structured
  export_to: console

prompt_template:
  You are an expert code reviewer with deep knowledge of:
  - Security vulnerabilities (SQL injection, XSS, CSRF, etc.)
  - Performance issues (N+1 queries, memory leaks, inefficient algorithms)
  - Code quality (readability, maintainability, best practices)
  - Testing coverage and quality

  Provide actionable, specific feedback with severity levels.

expose review.analyze@v1:
  params:
    code string
    language string
    context string
  returns:
    summary string
    issues array
    severity string
  prompt_template:
    Analyze the following {language} code for security issues, bugs, and quality concerns.

    Context: {context}

    Provide a structured review with:
    1. Summary (2-3 sentences)
    2. List of specific issues with line numbers
    3. Overall severity (low/medium/high/critical)

    Return as JSON with keys: summary, issues (array), severity

expose review.approve@v1:
  params:
    review_id string
    approved bool
    comments string
  returns:
    status string
    next_step string