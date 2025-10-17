# Promptware DSL Demo
# Demonstrates: sequential calls, variable assignment, conditionals, state management

call http as fetch_repo {
  url: "https://api.github.com/repos/anthropics/anthropic-sdk-python"
  method: "GET"
}

let repo_name = fetch_repo.name
let star_count = fetch_repo.stargazers_count
let is_popular = star_count > 100

if is_popular {
  call logger as log_popular {
    level: "info"
    message: "Popular repo found!"
  }
} else {
  call logger as log_unpopular {
    level: "info"
    message: "Small repo"
  }
}

state summary {
  let final_message = repo_name
}