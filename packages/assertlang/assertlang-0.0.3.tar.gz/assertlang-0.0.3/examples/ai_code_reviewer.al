lang python
agent ai-code-reviewer
port 23456
llm anthropic claude-3-5-sonnet-20241022

tools:
  - github_fetch_pr
  - security_scanner
  - code_analyzer

prompt_template:
  You are an expert code reviewer with deep knowledge of software security,
  performance optimization, and best practices across multiple programming languages.

  Your goal is to analyze code thoroughly and provide actionable feedback.

expose review.analyze@v1:
  params:
    repo string
    pr_number int
  returns:
    summary string
    issues array
    suggestions array
  prompt_template:
    Analyze the pull request from the following repository and PR number.

    Look for:
    - Security vulnerabilities (SQL injection, XSS, authentication flaws)
    - Performance issues (N+1 queries, inefficient algorithms)
    - Code quality problems (duplicated code, poor naming, missing tests)
    - Best practice violations

    For each issue found, provide:
    - Severity level (critical, high, medium, low)
    - File and line number
    - Description of the problem
    - Suggested fix

    Return your analysis in the following structure:
    - summary: Brief overview of the code quality
    - issues: Array of problems found
    - suggestions: Array of improvement recommendations

expose review.submit@v1:
  params:
    pr_url string
  returns:
    review_id string
    status string
  prompt_template:
    You are reviewing a pull request at the given URL.
    Create a review ID and return pending status.
    This is a quick acknowledgment before full analysis.