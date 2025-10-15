---
page_title: "Function: truncate"
description: |-
  Truncates text to a specified length with customizable suffix
---

# truncate (Function)

> Shortens text to a specified maximum length while preserving readability with optional suffix

The `truncate` function shortens text to a specified maximum length, adding a suffix (like "...") to indicate truncation. It's useful for creating previews, fitting text into limited display space, and maintaining consistent text lengths.

## When to Use This

- **Text previews**: Create excerpt previews for articles or descriptions
- **UI constraints**: Fit text into limited display areas
- **List formatting**: Maintain consistent text lengths in lists
- **Table displays**: Prevent text overflow in table cells
- **Log summaries**: Create shortened log entries for overviews

**Anti-patterns (when NOT to use):**
- When full text must always be preserved
- For text that's already within the desired length
- When truncation would remove critical information
- For structured data that requires complete content

## Quick Start

```terraform
# Basic text truncation
locals {
  long_description = "This is a very long description that needs to be shortened for display purposes"
  short_preview = provider::pyvider::truncate(local.long_description, 30)  # Returns: "This is a very long descrip..."
}

# Custom suffix
locals {
  article_title = "Advanced Terraform Provider Development Best Practices"
  truncated_title = provider::pyvider::truncate(local.article_title, 25, " [more]")  # Returns: "Advanced Terraform Pro [more]"
}
```

## Examples

### Basic Usage

```terraform
# Basic truncation with default suffix
locals {
  long_texts = [
    "This is a very long text that needs to be shortened for display",
    "Short text",
    "Another extremely long description that exceeds our display limits",
    ""
  ]

  # Truncate to 30 characters with default "..." suffix
  truncated_basic = [
    for text in local.long_texts :
    provider::pyvider::truncate(text, 30)
  ]
  # Results:
  # ["This is a very long text th...", "Short text", "Another extremely long desc...", ""]

  # Different length limits
  truncated_lengths = {
    short = provider::pyvider::truncate("Long description for testing truncation", 10)  # "Long desc..."
    medium = provider::pyvider::truncate("Long description for testing truncation", 20) # "Long description for..."
    long = provider::pyvider::truncate("Long description for testing truncation", 50)   # "Long description for testing truncation" (no truncation)
  }
}

# Custom suffix examples
locals {
  article_title = "Advanced Terraform Provider Development Best Practices for Enterprise"

  custom_suffixes = {
    ellipsis = provider::pyvider::truncate(local.article_title, 25, "...")          # "Advanced Terraform Prov..."
    more_indicator = provider::pyvider::truncate(local.article_title, 25, " [more]")  # "Advanced Terraform [more]"
    read_more = provider::pyvider::truncate(local.article_title, 25, " →")          # "Advanced Terraform Prov →"
    no_suffix = provider::pyvider::truncate(local.article_title, 25, "")            # "Advanced Terraform Prov"
  }
}

# Edge cases and null handling
locals {
  edge_cases = {
    exact_length = provider::pyvider::truncate("Exactly 20 chars lng", 20)    # "Exactly 20 chars lng" (no truncation)
    shorter_text = provider::pyvider::truncate("Short", 20)                   # "Short" (no truncation)
    empty_string = provider::pyvider::truncate("", 10)                        # ""
    null_text = provider::pyvider::truncate(null, 10)                         # null
    zero_length = provider::pyvider::truncate("Any text", 0)                  # ""
    negative_length = provider::pyvider::truncate("Any text", -5)             # ""
  }
}

output "truncation_examples" {
  value = {
    basic = local.truncated_basic
    lengths = local.truncated_lengths
    custom_suffixes = local.custom_suffixes
    edge_cases = local.edge_cases
  }
}
```

### Content Management

```terraform
# Blog post and article management
variable "blog_posts" {
  type = list(object({
    title       = string
    content     = string
    author      = string
    category    = string
    created_at  = string
  }))
  default = [
    {
      title = "Getting Started with Infrastructure as Code using Terraform"
      content = "Infrastructure as Code (IaC) has revolutionized how we manage and provision infrastructure. Terraform, developed by HashiCorp, is one of the most popular IaC tools that allows you to define infrastructure using declarative configuration files."
      author = "Jane Developer"
      category = "DevOps"
      created_at = "2024-01-15"
    },
    {
      title = "Advanced Kubernetes Networking Concepts"
      content = "Kubernetes networking can be complex, but understanding the core concepts is essential for running production workloads."
      author = "John Engineer"
      category = "Kubernetes"
      created_at = "2024-01-10"
    }
  ]
}

# Generate content previews for different display contexts
locals {
  blog_previews = {
    for post in var.blog_posts :
    post.title => {
      # Short preview for mobile cards
      mobile_preview = {
        title = provider::pyvider::truncate(post.title, 30)
        content = provider::pyvider::truncate(post.content, 80, "... Read more")
        author = post.author
      }

      # Medium preview for tablet/desktop lists
      desktop_preview = {
        title = provider::pyvider::truncate(post.title, 60)
        content = provider::pyvider::truncate(post.content, 150, "...")
        author = post.author
        category = post.category
      }

      # Newsletter preview with custom formatting
      newsletter_preview = {
        title = provider::pyvider::truncate(post.title, 45)
        excerpt = provider::pyvider::truncate(post.content, 120, " [Continue reading →]")
        byline = "By ${post.author} • ${post.category}"
      }

      # Social media preview
      social_preview = {
        title = provider::pyvider::truncate(post.title, 50)
        snippet = provider::pyvider::truncate(post.content, 100, " #${lower(post.category)}")
      }
    }
  }

  # Generate RSS feed descriptions
  rss_items = [
    for post in var.blog_posts : {
      title = post.title
      description = provider::pyvider::truncate(post.content, 200, "...")
      author = post.author
      category = post.category
      pubDate = post.created_at
    }
  ]
}

# SEO meta descriptions
locals {
  seo_descriptions = {
    for post in var.blog_posts :
    post.title => provider::pyvider::truncate(post.content, 160, "")  # Google typically shows ~160 chars
  }
}

output "content_management" {
  value = {
    previews = local.blog_previews
    rss_feed = local.rss_items
    seo_descriptions = local.seo_descriptions
  }
}
```

### UI Display

```terraform
# User interface component text truncation
variable "user_data" {
  type = list(object({
    full_name    = string
    job_title    = string
    company      = string
    bio          = string
    skills       = list(string)
  }))
  default = [
    {
      full_name = "Sarah Jessica Parker-Johnson"
      job_title = "Senior Software Engineering Manager"
      company = "Advanced Technology Solutions International Corp"
      bio = "Experienced engineering manager with 15+ years in software development, specializing in cloud infrastructure, microservices architecture, and team leadership."
      skills = ["Kubernetes", "AWS", "Python", "Go", "Docker", "Terraform"]
    },
    {
      full_name = "Bob Smith"
      job_title = "Developer"
      company = "StartupCo"
      bio = "Full-stack developer passionate about creating innovative solutions."
      skills = ["JavaScript", "React", "Node.js"]
    }
  ]
}

# Generate UI-appropriate text for different components
locals {
  user_cards = {
    for user in var.user_data :
    user.full_name => {
      # Compact card view
      compact = {
        name = provider::pyvider::truncate(user.full_name, 20)
        title = provider::pyvider::truncate(user.job_title, 25, "...")
        company = provider::pyvider::truncate(user.company, 20, "...")
        bio_snippet = provider::pyvider::truncate(user.bio, 60, "...")
      }

      # List item view
      list_item = {
        name = provider::pyvider::truncate(user.full_name, 30)
        title_company = "${provider::pyvider::truncate(user.job_title, 25)} at ${provider::pyvider::truncate(user.company, 20)}"
        bio = provider::pyvider::truncate(user.bio, 100, "... View profile")
      }

      # Table row view (very constrained)
      table_row = {
        name = provider::pyvider::truncate(user.full_name, 15)
        title = provider::pyvider::truncate(user.job_title, 20)
        company = provider::pyvider::truncate(user.company, 15)
        skills = provider::pyvider::truncate(join(", ", user.skills), 30, "...")
      }

      # Tooltip preview
      tooltip = {
        full_name = user.full_name
        title_company = "${user.job_title} at ${user.company}"
        bio = provider::pyvider::truncate(user.bio, 200)
      }
    }
  }

  # Navigation breadcrumb truncation
  breadcrumb_paths = [
    "Home / Products / Cloud Infrastructure / Container Orchestration / Kubernetes Services / Advanced Configuration",
    "Dashboard / User Management / Role Based Access Control / Permissions",
    "Settings / Integration / Third Party Services / API Keys / OAuth Configuration"
  ]

  breadcrumbs = [
    for path in local.breadcrumb_paths : {
      full_path = path
      truncated_mobile = provider::pyvider::truncate(path, 30, "...")
      truncated_tablet = provider::pyvider::truncate(path, 50, "...")
    }
  ]

  # Form field placeholders
  form_placeholders = {
    search = provider::pyvider::truncate("Search for users, documents, projects, or anything else", 40, "...")
    description = provider::pyvider::truncate("Enter a detailed description of your project including goals and requirements", 60, "...")
    tags = provider::pyvider::truncate("Add tags separated by commas (e.g., frontend, react, typescript)", 45, "...")
  }
}

# Notification message truncation
locals {
  notifications = [
    "Your deployment to production environment has completed successfully with 15 services updated",
    "New comment on your pull request: 'LGTM, but please update the documentation before merging'",
    "System maintenance scheduled for tonight from 11:00 PM to 2:00 AM EST - expect brief downtime"
  ]

  notification_display = [
    for notif in local.notifications : {
      full_message = notif
      mobile_toast = provider::pyvider::truncate(notif, 40, "... Tap for details")
      desktop_banner = provider::pyvider::truncate(notif, 80, "...")
      push_notification = provider::pyvider::truncate(notif, 50, "")  # No suffix for push notifications
    }
  ]
}

output "ui_display" {
  value = {
    user_cards = local.user_cards
    breadcrumbs = local.breadcrumbs
    form_placeholders = local.form_placeholders
    notifications = local.notification_display
  }
}
```

## Signature

`truncate(text: string, max_length: number, suffix?: string) -> string`

## Arguments

- **`text`** (string, required) - The text to truncate. If `null`, returns `null`.
- **`max_length`** (number, required) - Maximum length of the output string including the suffix. Must be >= 0.
  - If `max_length` is 0 or negative, returns empty string
  - If text length <= max_length, returns original text (no truncation)
- **`suffix`** (string, optional) - Text to append when truncation occurs. Defaults to `"..."`.
  - The suffix counts toward the `max_length` limit
  - If suffix is longer than `max_length`, only the suffix (truncated) is returned
  - Use empty string `""` for no suffix

## Return Value

Returns the truncated string:
- **No truncation needed**: Returns original text when `length(text) <= max_length`
- **With truncation**: Returns text truncated to `max_length` including suffix
- **Edge cases**:
  - Returns `""` when `max_length <= 0`
  - Returns `null` when input `text` is `null`
  - Returns suffix (possibly truncated) when suffix is longer than `max_length`

## Truncation Behavior

- **Character-based**: Truncates at exact character position (not word boundaries)
- **Suffix inclusion**: The suffix length is included in the `max_length` calculation
- **Precision**: If `max_length = 20` and `suffix = "..."`, the text portion will be max 17 characters
- **No truncation**: Text shorter than or equal to `max_length` is returned unchanged

## Common Use Cases

```terraform
# UI component sizing
locals {
  # Mobile card titles (limited space)
  mobile_title = provider::pyvider::truncate(title, 25, "...")

  # Table cell content (prevent overflow)
  table_cell = provider::pyvider::truncate(description, 40)

  # Tooltip previews (reasonable length)
  tooltip_text = provider::pyvider::truncate(full_content, 150)

  # SEO meta descriptions (Google limit)
  meta_description = provider::pyvider::truncate(content, 160, "")
}
```

## Related Functions

- [`length`](./length.md) - Get string length for truncation decisions
- [`split`](./split.md) - Split text for word-boundary truncation
- [`join`](./join.md) - Rejoin truncated word arrays
- [`replace`](./replace.md) - Replace text patterns
- [`upper`](./upper.md) - Convert case of truncated text