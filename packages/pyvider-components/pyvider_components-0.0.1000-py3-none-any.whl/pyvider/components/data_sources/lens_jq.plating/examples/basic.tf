# Basic JQ data source transformation examples

# Example 1: Simple field extraction
data "pyvider_lens_jq" "extract_user_name" {
  json_input = jsonencode({
    name = "John Doe"
    age  = 30
    email = "john.doe@example.com"
    address = {
      street = "123 Main St"
      city   = "Anytown"
      state  = "CA"
      zip    = "12345"
    }
  })
  query = ".name"
}

# Example 2: Nested field extraction
data "pyvider_lens_jq" "extract_city" {
  json_input = jsonencode({
    user = {
      profile = {
        address = {
          city = "San Francisco"
          state = "CA"
        }
      }
    }
  })
  query = ".user.profile.address.city"
}

# Example 3: Array operations
data "pyvider_lens_jq" "process_hobbies" {
  json_input = jsonencode({
    hobbies = ["reading", "hiking", "coding", "photography"]
  })
  query = ".hobbies | length"
}

# Example 4: Filter array elements
data "pyvider_lens_jq" "filter_employees" {
  json_input = jsonencode([
    {
      name = "Alice"
      department = "Engineering"
      salary = 95000
      active = true
    },
    {
      name = "Bob"
      department = "Marketing"
      salary = 75000
      active = false
    },
    {
      name = "Carol"
      department = "Engineering"
      salary = 105000
      active = true
    }
  ])
  query = "[.[] | select(.active and .department == \"Engineering\")]"
}

# Example 5: Transform and map
data "pyvider_lens_jq" "user_summary" {
  json_input = jsonencode([
    {
      id = 1
      firstName = "John"
      lastName = "Doe"
      posts = [
        { title = "Hello World", likes = 5 },
        { title = "Getting Started", likes = 12 }
      ]
    },
    {
      id = 2
      firstName = "Jane"
      lastName = "Smith"
      posts = [
        { title = "Advanced Tips", likes = 25 },
        { title = "Best Practices", likes = 18 }
      ]
    }
  ])
  query = "map({
    id,
    full_name: (.firstName + \" \" + .lastName),
    total_likes: [.posts[].likes] | add,
    post_count: (.posts | length)
  })"
}

# Example 6: Statistical operations
data "pyvider_lens_jq" "salary_stats" {
  json_input = jsonencode([
    { name = "Alice", salary = 95000 },
    { name = "Bob", salary = 75000 },
    { name = "Carol", salary = 105000 },
    { name = "Dave", salary = 85000 }
  ])
  query = "{
    total_employees: length,
    total_salary: [.[].salary] | add,
    average_salary: ([.[].salary] | add / length),
    max_salary: [.[].salary] | max,
    min_salary: [.[].salary] | min
  }"
}

# Create summary file with results
resource "pyvider_file_content" "jq_basic_results" {
  filename = "/tmp/jq_basic_results.txt"
  content = join("\n", [
    "=== Basic JQ Transformation Results ===",
    "",
    "User Name: ${data.pyvider_lens_jq.extract_user_name.result}",
    "City: ${data.pyvider_lens_jq.extract_city.result}",
    "Number of Hobbies: ${data.pyvider_lens_jq.process_hobbies.result}",
    "",
    "Active Engineers: ${length(data.pyvider_lens_jq.filter_employees.result)}",
    "User Summaries: ${length(data.pyvider_lens_jq.user_summary.result)}",
    "",
    "Salary Statistics:",
    "- Total Employees: ${jsondecode(data.pyvider_lens_jq.salary_stats.result).total_employees}",
    "- Average Salary: $${jsondecode(data.pyvider_lens_jq.salary_stats.result).average_salary}",
    "- Max Salary: $${jsondecode(data.pyvider_lens_jq.salary_stats.result).max_salary}",
    "- Min Salary: $${jsondecode(data.pyvider_lens_jq.salary_stats.result).min_salary}",
    "",
    "Generated at: ${timestamp()}"
  ])
}

output "basic_jq_results" {
  description = "Results from basic JQ transformations"
  value = {
    user_name = data.pyvider_lens_jq.extract_user_name.result
    city = data.pyvider_lens_jq.extract_city.result
    hobby_count = data.pyvider_lens_jq.process_hobbies.result
    active_engineers = length(data.pyvider_lens_jq.filter_employees.result)
    user_summaries = length(data.pyvider_lens_jq.user_summary.result)
    salary_stats = jsondecode(data.pyvider_lens_jq.salary_stats.result)
  }
}