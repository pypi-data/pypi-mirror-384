# API response processing with JQ transformations

# Example 1: GitHub API response processing
data "pyvider_http_api" "github_user" {
  url = "https://api.github.com/users/octocat"
  headers = {
    "Accept" = "application/vnd.github.v3+json"
    "User-Agent" = "Terraform-Pyvider-Example"
  }
}

data "pyvider_http_api" "github_repos" {
  url = "https://api.github.com/users/octocat/repos"
  headers = {
    "Accept" = "application/vnd.github.v3+json"
    "User-Agent" = "Terraform-Pyvider-Example"
  }
}

# Transform GitHub user profile
data "pyvider_lens_jq" "github_profile" {
  json_input = data.pyvider_http_api.github_user.response_body
  query = "{
    username: .login,
    display_name: (.name // .login),
    profile: {
      bio: .bio,
      location: .location,
      company: .company,
      blog: .blog,
      avatar_url: .avatar_url
    },
    stats: {
      public_repos: .public_repos,
      public_gists: .public_gists,
      followers: .followers,
      following: .following
    },
    account_info: {
      created_at: .created_at,
      updated_at: .updated_at,
      account_type: .type,
      is_hireable: (.hireable // false)
    }
  }"
}

# Process repository data
data "pyvider_lens_jq" "github_repo_analysis" {
  json_input = data.pyvider_http_api.github_repos.response_body
  query = "{
    repository_summary: {
      total_repos: length,
      public_repos: [.[] | select(.private == false)] | length,
      private_repos: [.[] | select(.private == true)] | length,
      fork_count: [.[] | select(.fork == true)] | length,
      original_repos: [.[] | select(.fork == false)] | length
    },
    language_stats: (
      [.[].language] | map(select(. != null)) |
      group_by(.) | map({language: .[0], count: length}) |
      sort_by(.count) | reverse
    ),
    popularity_metrics: {
      total_stars: ([.[].stargazers_count] | add),
      total_forks: ([.[].forks_count] | add),
      total_watchers: ([.[].watchers_count] | add),
      most_starred: (max_by(.stargazers_count) | {name, stars: .stargazers_count, url: .html_url}),
      most_forked: (max_by(.forks_count) | {name, forks: .forks_count, url: .html_url})
    },
    recent_activity: {
      recently_updated: ([.[] | select(.updated_at > \"2023-01-01\")] | length),
      last_update: ([.[].updated_at] | max),
      repos_with_issues: ([.[] | select(.has_issues == true)] | length),
      repos_with_wiki: ([.[] | select(.has_wiki == true)] | length)
    },
    top_repositories: (
      sort_by(.stargazers_count) | reverse | .[0:5] | map({
        name,
        description: (.description // \"No description\"),
        language,
        stars: .stargazers_count,
        forks: .forks_count,
        url: .html_url,
        last_updated: .updated_at
      })
    )
  }"
}

# Example 2: REST API data processing
data "pyvider_http_api" "jsonplaceholder_posts" {
  url = "https://jsonplaceholder.typicode.com/posts"
}

data "pyvider_http_api" "jsonplaceholder_users" {
  url = "https://jsonplaceholder.typicode.com/users"
}

data "pyvider_http_api" "jsonplaceholder_comments" {
  url = "https://jsonplaceholder.typicode.com/comments"
}

# Combine and analyze blog data
data "pyvider_lens_jq" "blog_analysis" {
  json_input = jsonencode({
    posts = jsondecode(data.pyvider_http_api.jsonplaceholder_posts.response_body)
    users = jsondecode(data.pyvider_http_api.jsonplaceholder_users.response_body)
    comments = jsondecode(data.pyvider_http_api.jsonplaceholder_comments.response_body)
  })
  query = "{
    content_statistics: {
      total_posts: (.posts | length),
      total_users: (.users | length),
      total_comments: (.comments | length),
      avg_comments_per_post: ((.comments | length) / (.posts | length)),
      posts_per_user: ((.posts | length) / (.users | length))
    },
    user_activity: (
      .users | map({
        id,
        name,
        username,
        email,
        website: .website,
        company: .company.name,
        posts_count: ([.id as $uid | .posts[] | select(.userId == $uid)] | length),
        comments_made: ([.id as $uid | .comments[] | select(.email == .email)] | length)
      }) | sort_by(.posts_count) | reverse
    ),
    content_engagement: (
      .posts | map({
        id,
        title,
        author_id: .userId,
        author_name: ([.userId as $uid | .users[] | select(.id == $uid) | .name][0]),
        word_count: (.body | split(\" \") | length),
        comment_count: ([.id as $pid | .comments[] | select(.postId == $pid)] | length),
        engagement_score: ([.id as $pid | .comments[] | select(.postId == $pid)] | length) * 10 + (.body | split(\" \") | length)
      }) | sort_by(.engagement_score) | reverse | .[0:10]
    ),
    domain_analysis: {
      companies: ([.users[].company.name] | unique),
      domains: ([.users[].website | select(. != null) | split(\".\")[-1]] | unique),
      email_domains: ([.users[].email | split(\"@\")[1]] | group_by(.) | map({domain: .[0], count: length}) | sort_by(.count) | reverse)
    }
  }"
}

# Example 3: Weather API processing
data "pyvider_http_api" "weather_data" {
  url = "https://api.openweathermap.org/data/2.5/forecast?q=London&appid=demo_key&units=metric"
}

# Process weather forecast (handling potential API failures gracefully)
data "pyvider_lens_jq" "weather_forecast" {
  json_input = can(jsondecode(data.pyvider_http_api.weather_data.response_body)) ?
    data.pyvider_http_api.weather_data.response_body :
    jsonencode({
      cod = "401"
      message = "API key required"
      list = []
      city = {name = "Demo", country = "XX"}
    })

  query = "if .cod == \"200\" then {
    location: {
      city: .city.name,
      country: .city.country,
      coordinates: {lat: .city.coord.lat, lon: .city.coord.lon}
    },
    forecast_summary: {
      total_forecasts: (.list | length),
      forecast_days: ((.list | length) / 8),
      temperature_range: {
        min: ([.list[].main.temp_min] | min),
        max: ([.list[].main.temp_max] | max),
        avg: (([.list[].main.temp] | add) / (.list | length))
      },
      weather_conditions: ([.list[].weather[0].main] | group_by(.) | map({condition: .[0], occurrences: length}) | sort_by(.occurrences) | reverse),
      humidity_stats: {
        avg: (([.list[].main.humidity] | add) / (.list | length)),
        max: ([.list[].main.humidity] | max),
        min: ([.list[].main.humidity] | min)
      }
    },
    daily_forecasts: (
      .list | group_by(.dt_txt | split(\" \")[0]) | map({
        date: .[0].dt_txt | split(\" \")[0],
        temp_high: ([.[].main.temp_max] | max),
        temp_low: ([.[].main.temp_min] | min),
        conditions: ([.[].weather[0].main] | unique),
        avg_humidity: (([.[].main.humidity] | add) / length),
        readings_count: length
      })
    )
  } else {
    error: \"Weather API request failed\",
    error_code: .cod,
    error_message: .message,
    mock_data: {
      location: {city: \"Demo City\", country: \"XX\"},
      forecast_summary: {note: \"This is mock data due to API failure\"}
    }
  } end"
}

# Create comprehensive API processing report
resource "pyvider_file_content" "api_processing_report" {
  filename = "/tmp/api_processing_report.json"
  content = jsonencode({
    timestamp = timestamp()

    github_analysis = data.pyvider_http_api.github_user.status_code == 200 ? {
      profile = jsondecode(data.pyvider_lens_jq.github_profile.result)
      repository_analysis = jsondecode(data.pyvider_lens_jq.github_repo_analysis.result)
      api_status = "success"
    } : {
      api_status = "failed"
      status_code = data.pyvider_http_api.github_user.status_code
    }

    blog_analysis = data.pyvider_http_api.jsonplaceholder_posts.status_code == 200 ? {
      analysis = jsondecode(data.pyvider_lens_jq.blog_analysis.result)
      api_status = "success"
    } : {
      api_status = "failed"
      status_code = data.pyvider_http_api.jsonplaceholder_posts.status_code
    }

    weather_analysis = {
      forecast = jsondecode(data.pyvider_lens_jq.weather_forecast.result)
      api_status = data.pyvider_http_api.weather_data.status_code == 200 ? "success" : "failed"
      status_code = data.pyvider_http_api.weather_data.status_code
    }

    processing_summary = {
      apis_called = 6
      successful_calls = sum([
        data.pyvider_http_api.github_user.status_code == 200 ? 1 : 0,
        data.pyvider_http_api.github_repos.status_code == 200 ? 1 : 0,
        data.pyvider_http_api.jsonplaceholder_posts.status_code == 200 ? 1 : 0,
        data.pyvider_http_api.jsonplaceholder_users.status_code == 200 ? 1 : 0,
        data.pyvider_http_api.jsonplaceholder_comments.status_code == 200 ? 1 : 0,
        data.pyvider_http_api.weather_data.status_code == 200 ? 1 : 0
      ])
      jq_transformations = 4
    }
  })
}

resource "pyvider_file_content" "github_report" {
  count = data.pyvider_http_api.github_user.status_code == 200 ? 1 : 0

  filename = "/tmp/github_analysis_report.txt"
  content = join("\n", [
    "=== GitHub Profile Analysis ===",
    "",
    "Profile Information:",
    "- Username: ${jsondecode(data.pyvider_lens_jq.github_profile.result).username}",
    "- Display Name: ${jsondecode(data.pyvider_lens_jq.github_profile.result).display_name}",
    "- Location: ${lookup(jsondecode(data.pyvider_lens_jq.github_profile.result).profile, "location", "Not specified")}",
    "- Company: ${lookup(jsondecode(data.pyvider_lens_jq.github_profile.result).profile, "company", "Not specified")}",
    "",
    "Repository Statistics:",
    "- Total Repositories: ${jsondecode(data.pyvider_lens_jq.github_repo_analysis.result).repository_summary.total_repos}",
    "- Public Repositories: ${jsondecode(data.pyvider_lens_jq.github_repo_analysis.result).repository_summary.public_repos}",
    "- Forked Repositories: ${jsondecode(data.pyvider_lens_jq.github_repo_analysis.result).repository_summary.fork_count}",
    "- Original Repositories: ${jsondecode(data.pyvider_lens_jq.github_repo_analysis.result).repository_summary.original_repos}",
    "",
    "Popularity Metrics:",
    "- Total Stars: ${jsondecode(data.pyvider_lens_jq.github_repo_analysis.result).popularity_metrics.total_stars}",
    "- Total Forks: ${jsondecode(data.pyvider_lens_jq.github_repo_analysis.result).popularity_metrics.total_forks}",
    "- Most Starred: ${jsondecode(data.pyvider_lens_jq.github_repo_analysis.result).popularity_metrics.most_starred.name} (${jsondecode(data.pyvider_lens_jq.github_repo_analysis.result).popularity_metrics.most_starred.stars} stars)",
    "",
    "Programming Languages:",
    join("\n", [for lang in jsondecode(data.pyvider_lens_jq.github_repo_analysis.result).language_stats : "- ${lang.language}: ${lang.count} repositories"]),
    "",
    "Generated at: ${timestamp()}"
  ])
}

output "api_processing_results" {
  description = "Results from API data processing with JQ"
  value = {
    github_success = data.pyvider_http_api.github_user.status_code == 200
    blog_success = data.pyvider_http_api.jsonplaceholder_posts.status_code == 200
    weather_success = data.pyvider_http_api.weather_data.status_code == 200

    github_stats = data.pyvider_http_api.github_user.status_code == 200 ? {
      username = jsondecode(data.pyvider_lens_jq.github_profile.result).username
      total_repos = jsondecode(data.pyvider_lens_jq.github_repo_analysis.result).repository_summary.total_repos
      total_stars = jsondecode(data.pyvider_lens_jq.github_repo_analysis.result).popularity_metrics.total_stars
      languages = length(jsondecode(data.pyvider_lens_jq.github_repo_analysis.result).language_stats)
    } : null

    blog_stats = data.pyvider_http_api.jsonplaceholder_posts.status_code == 200 ? {
      total_posts = jsondecode(data.pyvider_lens_jq.blog_analysis.result).content_statistics.total_posts
      total_users = jsondecode(data.pyvider_lens_jq.blog_analysis.result).content_statistics.total_users
      total_comments = jsondecode(data.pyvider_lens_jq.blog_analysis.result).content_statistics.total_comments
      top_engaged_posts = length(jsondecode(data.pyvider_lens_jq.blog_analysis.result).content_engagement)
    } : null

    files_created = concat([
      pyvider_file_content.api_processing_report.filename
    ], data.pyvider_http_api.github_user.status_code == 200 ? [
      pyvider_file_content.github_report[0].filename
    ] : [])
  }
}