---
page_title: "Function: to_kebab_case"
description: |-
  Converts text to kebab-case format with lowercase letters and hyphens
---

# to_kebab_case (Function)

> Converts text to kebab-case format by replacing separators with hyphens and using lowercase

The `to_kebab_case` function converts text to kebab-case format, which uses lowercase letters with hyphens separating words. This format is commonly used in URLs, CSS classes, and HTML attributes.

## When to Use This

- **URL slugs**: Create SEO-friendly URLs from page titles
- **CSS class names**: Generate consistent CSS class naming
- **HTML attributes**: Create valid HTML data attributes
- **File names**: Generate web-safe filenames
- **Configuration keys**: Use in systems that prefer kebab-case

**Anti-patterns (when NOT to use):**
- JavaScript variable names (use camelCase instead)
- Database column names (use snake_case instead)
- When preserving original case is important
- For content that needs to remain readable

## Quick Start

```terraform
# Convert page title to URL slug
locals {
  page_title = "User Profile Settings"
  url_slug = provider::pyvider::to_kebab_case(local.page_title)  # Returns: "user-profile-settings"
}

# Convert to CSS class name
variable "component_name" {
  default = "navigationMenu"
}

locals {
  css_class = provider::pyvider::to_kebab_case(var.component_name)  # Returns: "navigation-menu"
}
```

## Examples

### Basic Usage

```terraform
# Standard kebab-case conversion
locals {
  text_inputs = [
    "User Profile Settings",
    "navigationMenu",
    "data_source_config",
    "API-EndPoint-Handler",
    "Mixed_Format-Text Input"
  ]

  # Convert all to kebab-case
  kebab_outputs = [
    for text in local.text_inputs :
    provider::pyvider::to_kebab_case(text)
  ]
  # Results: ["user-profile-settings", "navigation-menu", "data-source-config", "api-end-point-handler", "mixed-format-text-input"]
}

# Different input formats
locals {
  format_examples = {
    camel_case = provider::pyvider::to_kebab_case("userProfileData")           # "user-profile-data"
    pascal_case = provider::pyvider::to_kebab_case("UserProfileData")         # "user-profile-data"
    snake_case = provider::pyvider::to_kebab_case("user_profile_data")        # "user-profile-data"
    space_separated = provider::pyvider::to_kebab_case("user profile data")   # "user-profile-data"
    mixed_separators = provider::pyvider::to_kebab_case("User_Profile-Data")  # "user-profile-data"
    already_kebab = provider::pyvider::to_kebab_case("user-profile-data")     # "user-profile-data"
  }
}

# Edge cases and special handling
locals {
  edge_cases = {
    empty_string = provider::pyvider::to_kebab_case("")                    # ""
    single_word = provider::pyvider::to_kebab_case("user")                # "user"
    uppercase_word = provider::pyvider::to_kebab_case("USER")             # "user"
    with_numbers = provider::pyvider::to_kebab_case("user123Profile")     # "user123-profile"
    special_chars = provider::pyvider::to_kebab_case("user@profile.com")  # "user-profile-com"
    null_input = provider::pyvider::to_kebab_case(null)                   # null
  }
}

output "kebab_case_examples" {
  value = {
    conversions = local.kebab_outputs
    formats = local.format_examples
    edge_cases = local.edge_cases
  }
}
```

### URL Generation

```terraform
# Blog post URL slug generation
variable "blog_posts" {
  type = list(object({
    title    = string
    category = string
    tags     = list(string)
  }))
  default = [
    {
      title = "Getting Started with Infrastructure as Code"
      category = "DevOps Tutorials"
      tags = ["terraform", "infrastructure", "automation"]
    },
    {
      title = "Advanced Kubernetes Networking Best Practices"
      category = "Container Orchestration"
      tags = ["kubernetes", "networking", "security"]
    }
  ]
}

# Generate SEO-friendly URL slugs
locals {
  blog_urls = {
    for post in var.blog_posts :
    post.title => {
      # Main URL slug from title
      slug = provider::pyvider::to_kebab_case(post.title)

      # Category-based URL structure
      category_slug = provider::pyvider::to_kebab_case(post.category)
      full_url = "/blog/${local.blog_urls[post.title].category_slug}/${local.blog_urls[post.title].slug}"

      # Tag-based URLs for filtering
      tag_urls = [
        for tag in post.tags :
        "/blog/tags/${provider::pyvider::to_kebab_case(tag)}"
      ]
    }
  }

  # API endpoint generation
  api_endpoints = {
    for post in var.blog_posts :
    post.title => {
      get_post = "/api/posts/${provider::pyvider::to_kebab_case(post.title)}"
      get_category = "/api/categories/${provider::pyvider::to_kebab_case(post.category)}"
      related_posts = "/api/posts/${provider::pyvider::to_kebab_case(post.title)}/related"
    }
  }
}

# Page route generation for SPA
locals {
  page_routes = {
    user_management = {
      list = "/users"
      create = "/users/create"
      edit = "/users/${provider::pyvider::to_kebab_case("Edit User Profile")}"  # "/users/edit-user-profile"
      settings = "/users/${provider::pyvider::to_kebab_case("Account Settings")}"  # "/users/account-settings"
    }

    admin_panel = {
      dashboard = "/admin/dashboard"
      user_roles = "/admin/${provider::pyvider::to_kebab_case("User Role Management")}"  # "/admin/user-role-management"
      system_config = "/admin/${provider::pyvider::to_kebab_case("System Configuration")}"  # "/admin/system-configuration"
    }
  }
}

# Static site generation paths
variable "content_sections" {
  type = list(object({
    name = string
    subsections = list(string)
  }))
  default = [
    {
      name = "Getting Started Guide"
      subsections = ["Installation Instructions", "Quick Start Tutorial", "Basic Configuration"]
    },
    {
      name = "Advanced Topics"
      subsections = ["Performance Optimization", "Security Best Practices", "Troubleshooting Guide"]
    }
  ]
}

locals {
  static_pages = flatten([
    for section in var.content_sections : [
      for subsection in section.subsections : {
        section_slug = provider::pyvider::to_kebab_case(section.name)
        subsection_slug = provider::pyvider::to_kebab_case(subsection)
        full_path = "/docs/${provider::pyvider::to_kebab_case(section.name)}/${provider::pyvider::to_kebab_case(subsection)}"
        breadcrumb = "${section.name} > ${subsection}"
      }
    ]
  ])
}

output "url_generation" {
  value = {
    blog_urls = local.blog_urls
    api_endpoints = local.api_endpoints
    page_routes = local.page_routes
    static_pages = local.static_pages
  }
}
```

### CSS Integration

```terraform
# CSS class generation from component names
variable "ui_components" {
  type = list(object({
    name = string
    variants = list(string)
    states = list(string)
  }))
  default = [
    {
      name = "Navigation Menu"
      variants = ["Primary Button", "Secondary Button", "Icon Button"]
      states = ["Default State", "Hover State", "Active State", "Disabled State"]
    },
    {
      name = "Modal Dialog"
      variants = ["Small Modal", "Large Modal", "Full Screen Modal"]
      states = ["Open State", "Closing State", "Error State"]
    }
  ]
}

# Generate BEM-style CSS classes
locals {
  css_classes = {
    for component in var.ui_components :
    component.name => {
      # Block (component)
      block = provider::pyvider::to_kebab_case(component.name)

      # Elements (variants)
      elements = {
        for variant in component.variants :
        variant => "${provider::pyvider::to_kebab_case(component.name)}__${provider::pyvider::to_kebab_case(variant)}"
      }

      # Modifiers (states)
      modifiers = {
        for state in component.states :
        state => "${provider::pyvider::to_kebab_case(component.name)}--${provider::pyvider::to_kebab_case(state)}"
      }
    }
  }
}

# Tailwind CSS custom class generation
variable "design_tokens" {
  type = map(object({
    category = string
    values = map(string)
  }))
  default = {
    brand_colors = {
      category = "Brand Colors"
      values = {
        "Primary Blue" = "#007bff"
        "Secondary Gray" = "#6c757d"
        "Success Green" = "#28a745"
        "Warning Orange" = "#ffc107"
      }
    }
    spacing_scale = {
      category = "Spacing Scale"
      values = {
        "Extra Small" = "0.25rem"
        "Small Space" = "0.5rem"
        "Medium Space" = "1rem"
        "Large Space" = "2rem"
      }
    }
  }
}

locals {
  tailwind_classes = {
    for token_group, config in var.design_tokens :
    token_group => {
      category_class = provider::pyvider::to_kebab_case(config.category)

      utility_classes = {
        for name, value in config.values :
        name => {
          class_name = provider::pyvider::to_kebab_case(name)
          css_variable = "--${local.tailwind_classes[token_group].category_class}-${provider::pyvider::to_kebab_case(name)}"
          utility_class = ".${local.tailwind_classes[token_group].category_class}-${provider::pyvider::to_kebab_case(name)}"
        }
      }
    }
  }
}

# SCSS/SASS variable generation
locals {
  scss_variables = flatten([
    for token_group, config in var.design_tokens : [
      for name, value in config.values : {
        variable_name = "$${provider::pyvider::to_kebab_case(config.category)}-${provider::pyvider::to_kebab_case(name)}"
        css_value = value
        scss_declaration = "$${provider::pyvider::to_kebab_case(config.category)}-${provider::pyvider::to_kebab_case(name)}: ${value};"
      }
    ]
  ])
}

# CSS custom properties (CSS variables)
locals {
  css_custom_properties = flatten([
    for token_group, config in var.design_tokens : [
      for name, value in config.values : {
        property_name = "--${provider::pyvider::to_kebab_case(config.category)}-${provider::pyvider::to_kebab_case(name)}"
        css_value = value
        declaration = "--${provider::pyvider::to_kebab_case(config.category)}-${provider::pyvider::to_kebab_case(name)}: ${value};"
      }
    ]
  ])
}

output "css_integration" {
  value = {
    bem_classes = local.css_classes
    tailwind_classes = local.tailwind_classes
    scss_variables = local.scss_variables
    css_custom_properties = local.css_custom_properties
  }
}
```

## Signature

`to_kebab_case(text: string) -> string`

## Arguments

- **`text`** (string, required) - The text to convert to kebab-case. Handles various input formats:
  - `camelCase` (userName)
  - `PascalCase` (UserName)
  - `snake_case` (user_name)
  - `space separated` (user name)
  - `Mixed-Format_text` (mixed separators)
  - If `null`, returns `null`

## Return Value

Returns the converted string in kebab-case format:
- **kebab-case**: All lowercase with hyphens separating words → `user-profile-data`
- **Empty string**: Returns `""` when input is empty
- **Null**: Returns `null` when input is `null`

## Processing Rules

The function applies these transformations:
1. **Convert to lowercase**: All characters converted to lowercase
2. **Replace separators**: Underscores (`_`), spaces (` `), and existing hyphens become single hyphens
3. **Word boundaries**: CamelCase and PascalCase word boundaries become hyphens
4. **Clean up**: Multiple consecutive separators become single hyphens
5. **Trim**: Leading and trailing separators are removed

## Common Use Cases

```terraform
# URL-safe slugs
locals {
  page_slug = provider::pyvider::to_kebab_case("About Our Company")  # "about-our-company"

  # CSS class names
  component_class = provider::pyvider::to_kebab_case("HeaderNavigation")  # "header-navigation"

  # HTML data attributes
  data_attribute = "data-${provider::pyvider::to_kebab_case("userPreference")}"  # "data-user-preference"

  # File names for web assets
  filename = "${provider::pyvider::to_kebab_case("Product Feature Image")}.jpg"  # "product-feature-image.jpg"
}
```

## Related Functions

- [`to_snake_case`](./to_snake_case.md) - Convert to snake_case format
- [`to_camel_case`](./to_camel_case.md) - Convert to camelCase format
- [`lower`](./lower.md) - Convert to lowercase
- [`replace`](./replace.md) - Replace specific text patterns
- [`split`](./split.md) - Split strings for processing