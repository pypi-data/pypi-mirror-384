---
page_title: "Function: to_camel_case"
description: |-
  Converts text to camelCase format with optional first letter capitalization
---

# to_camel_case (Function)

> Converts text to camelCase format by removing separators and capitalizing words

The `to_camel_case` function converts text to camelCase format, where the first word is lowercase and subsequent words are capitalized with no separators. It can optionally capitalize the first letter to create PascalCase.

## When to Use This

- **JavaScript variables**: Convert to standard JavaScript naming conventions
- **JSON property names**: Create camelCase keys for JSON objects
- **API field names**: Convert database column names to API-friendly format
- **Function naming**: Generate camelCase function or method names
- **Class properties**: Create property names following camelCase conventions

**Anti-patterns (when NOT to use):**
- Database column names (use snake_case instead)
- File names on case-sensitive systems
- Constants (use UPPER_SNAKE_CASE instead)
- When preserving original formatting is important

## Quick Start

```terraform
# Convert to standard camelCase
locals {
  field_name = "user_profile_data"
  camel_name = provider::pyvider::to_camel_case(local.field_name)  # Returns: "userProfileData"
}

# Convert to PascalCase (first letter capitalized)
locals {
  class_name = "database_connection"
  pascal_name = provider::pyvider::to_camel_case(local.class_name, true)  # Returns: "DatabaseConnection"
}
```

## Examples

### Basic Usage

```terraform
# Standard camelCase conversion
locals {
  database_fields = ["user_name", "email_address", "created_at", "is_active"]

  # Convert to camelCase (first letter lowercase)
  camel_fields = [
    for field in local.database_fields :
    provider::pyvider::to_camel_case(field)
  ]
  # Result: ["userName", "emailAddress", "createdAt", "isActive"]

  # Convert to PascalCase (first letter uppercase)
  pascal_fields = [
    for field in local.database_fields :
    provider::pyvider::to_camel_case(field, true)
  ]
  # Result: ["UserName", "EmailAddress", "CreatedAt", "IsActive"]
}

# Different input formats
locals {
  various_formats = {
    snake_case = provider::pyvider::to_camel_case("user_profile_data")      # "userProfileData"
    kebab_case = provider::pyvider::to_camel_case("user-profile-data")      # "userProfileData"
    space_separated = provider::pyvider::to_camel_case("user profile data") # "userProfileData"
    mixed_case = provider::pyvider::to_camel_case("User_Profile-data")      # "userProfileData"
  }

  pascal_variations = {
    snake_case = provider::pyvider::to_camel_case("user_profile_data", true)  # "UserProfileData"
    kebab_case = provider::pyvider::to_camel_case("user-profile-data", true)  # "UserProfileData"
    space_separated = provider::pyvider::to_camel_case("user profile data", true) # "UserProfileData"
  }
}

# Edge cases and special handling
locals {
  edge_cases = {
    empty_string = provider::pyvider::to_camel_case("")                    # ""
    single_word = provider::pyvider::to_camel_case("user")                # "user"
    single_word_pascal = provider::pyvider::to_camel_case("user", true)   # "User"
    already_camel = provider::pyvider::to_camel_case("userName")          # "userName"
    already_pascal = provider::pyvider::to_camel_case("UserName", true)   # "UserName"
    null_input = provider::pyvider::to_camel_case(null)                   # null
  }
}

output "camel_case_examples" {
  value = {
    camel = local.camel_fields
    pascal = local.pascal_fields
    variations = local.various_formats
    pascal_variations = local.pascal_variations
    edge_cases = local.edge_cases
  }
}
```

### API Field Mapping

```terraform
# Database to API field mapping
variable "database_schema" {
  type = map(object({
    column_name = string
    data_type   = string
    is_nullable = bool
  }))
  default = {
    user_id = {
      column_name = "user_id"
      data_type   = "integer"
      is_nullable = false
    }
    email_address = {
      column_name = "email_address"
      data_type   = "varchar"
      is_nullable = false
    }
    created_at = {
      column_name = "created_at"
      data_type   = "timestamp"
      is_nullable = false
    }
  }
}

# Generate API-friendly field names
locals {
  api_fields = {
    for key, value in var.database_schema :
    provider::pyvider::to_camel_case(key) => {
      original_column = value.column_name
      type           = value.data_type
      required       = !value.is_nullable
    }
  }
  # Result: {
  #   "userId" = { original_column = "user_id", type = "integer", required = true }
  #   "emailAddress" = { original_column = "email_address", type = "varchar", required = true }
  #   "createdAt" = { original_column = "created_at", type = "timestamp", required = true }
  # }

  # Generate JSON schema for API documentation
  json_schema_properties = {
    for key, value in var.database_schema :
    provider::pyvider::to_camel_case(key) => {
      type = value.data_type == "integer" ? "number" :
             value.data_type == "varchar" ? "string" :
             value.data_type == "timestamp" ? "string" : "string"
      format = value.data_type == "timestamp" ? "date-time" : null
    }
  }
}

# Configuration mapping for different environments
locals {
  config_mappings = {
    # Environment variables to configuration keys
    env_to_config = {
      for env_var in ["DATABASE_HOST", "API_SECRET_KEY", "CACHE_TTL_SECONDS"] :
      provider::pyvider::to_camel_case(replace(lower(env_var), "_", " ")) => env_var
    }
    # Result: {
    #   "databaseHost" = "DATABASE_HOST"
    #   "apiSecretKey" = "API_SECRET_KEY"
    #   "cacheTtlSeconds" = "CACHE_TTL_SECONDS"
    # }

    # Generate TypeScript interface
    typescript_interface = join("\n", [
      "interface ApiResponse {",
      join("\n", [
        for key, value in local.api_fields :
        "  ${key}${value.required ? "" : "?"}: ${value.type == "integer" ? "number" : "string"};"
      ]),
      "}"
    ])
  }
}

output "api_mapping" {
  value = {
    api_fields = local.api_fields
    json_schema = local.json_schema_properties
    config_mapping = local.config_mappings.env_to_config
    typescript = local.config_mappings.typescript_interface
  }
}
```

### JavaScript Code Generation

```terraform
# Generate JavaScript/TypeScript code
variable "terraform_resources" {
  type = list(object({
    resource_type = string
    name         = string
    attributes   = list(string)
  }))
  default = [
    {
      resource_type = "aws_s3_bucket"
      name         = "app_storage_bucket"
      attributes   = ["bucket_name", "versioning_enabled", "public_read_policy"]
    },
    {
      resource_type = "aws_lambda_function"
      name         = "data_processor_lambda"
      attributes   = ["function_name", "runtime_version", "memory_size"]
    }
  ]
}

# Generate JavaScript class definitions
locals {
  js_classes = {
    for resource in var.terraform_resources :
    provider::pyvider::to_camel_case(resource.resource_type, true) => {
      class_name = provider::pyvider::to_camel_case(resource.resource_type, true)
      instance_name = provider::pyvider::to_camel_case(resource.name)

      properties = [
        for attr in resource.attributes :
        provider::pyvider::to_camel_case(attr)
      ]

      constructor_params = join(", ", [
        for attr in resource.attributes :
        "${provider::pyvider::to_camel_case(attr)}: string"
      ])

      class_definition = join("\n", [
        "class ${provider::pyvider::to_camel_case(resource.resource_type, true)} {",
        join("\n", [
          for attr in resource.attributes :
          "  private ${provider::pyvider::to_camel_case(attr)}: string;"
        ]),
        "",
        "  constructor(${join(", ", [for attr in resource.attributes : "${provider::pyvider::to_camel_case(attr)}: string"])}) {",
        join("\n", [
          for attr in resource.attributes :
          "    this.${provider::pyvider::to_camel_case(attr)} = ${provider::pyvider::to_camel_case(attr)};"
        ]),
        "  }",
        "",
        join("\n", [
          for attr in resource.attributes :
          "  get${provider::pyvider::to_camel_case(attr, true)}(): string {\n    return this.${provider::pyvider::to_camel_case(attr)};\n  }"
        ]),
        "}"
      ])
    }
  }

  # Generate React component prop interfaces
  react_interfaces = {
    for resource in var.terraform_resources :
    "${provider::pyvider::to_camel_case(resource.resource_type, true)}Props" => {
      interface_name = "${provider::pyvider::to_camel_case(resource.resource_type, true)}Props"

      interface_definition = join("\n", [
        "interface ${provider::pyvider::to_camel_case(resource.resource_type, true)}Props {",
        join("\n", [
          for attr in resource.attributes :
          "  ${provider::pyvider::to_camel_case(attr)}: string;"
        ]),
        "  onUpdate?: () => void;",
        "  className?: string;",
        "}"
      ])
    }
  }

  # Generate function names for API endpoints
  api_functions = {
    for resource in var.terraform_resources :
    resource.resource_type => {
      get_function = "get${provider::pyvider::to_camel_case(resource.name, true)}"
      create_function = "create${provider::pyvider::to_camel_case(resource.name, true)}"
      update_function = "update${provider::pyvider::to_camel_case(resource.name, true)}"
      delete_function = "delete${provider::pyvider::to_camel_case(resource.name, true)}"

      crud_functions = {
        get = "get${provider::pyvider::to_camel_case(resource.name, true)}"
        create = "create${provider::pyvider::to_camel_case(resource.name, true)}"
        update = "update${provider::pyvider::to_camel_case(resource.name, true)}"
        delete = "delete${provider::pyvider::to_camel_case(resource.name, true)}"
      }
    }
  }
}

output "javascript_generation" {
  value = {
    class_definitions = [for k, v in local.js_classes : v.class_definition]
    react_interfaces = [for k, v in local.react_interfaces : v.interface_definition]
    api_functions = local.api_functions
  }
}
```

## Signature

`to_camel_case(text: string, upper_first?: boolean) -> string`

## Arguments

- **`text`** (string, required) - The text to convert to camelCase. Handles various input formats:
  - `snake_case` (user_name)
  - `kebab-case` (user-name)
  - `space separated` (user name)
  - `Mixed_Format-text` (mixed separators)
  - If `null`, returns `null`
- **`upper_first`** (boolean, optional) - Whether to capitalize the first letter (PascalCase). Defaults to `false`.
  - `false` (default): Returns camelCase → `userName`
  - `true`: Returns PascalCase → `UserName`

## Return Value

Returns the converted string in camelCase or PascalCase format:
- **camelCase** (upper_first = false): First letter lowercase, subsequent words capitalized → `userProfileData`
- **PascalCase** (upper_first = true): All words capitalized including first → `UserProfileData`
- **Empty string**: Returns `""` when input is empty
- **Null**: Returns `null` when input is `null`

## Processing Rules

The function applies these transformations:
1. **Separators removed**: Underscores (`_`), hyphens (`-`), and spaces (` `) are removed
2. **Word boundaries**: Each separator creates a new word boundary
3. **Capitalization**: Each word after the first is capitalized (unless `upper_first` is true)
4. **Consecutive separators**: Multiple separators are treated as a single separator
5. **Preserve existing**: Already camelCase text is handled gracefully

## Related Functions

- [`to_snake_case`](./to_snake_case.md) - Convert to snake_case format
- [`to_kebab_case`](./to_kebab_case.md) - Convert to kebab-case format
- [`upper`](./upper.md) - Convert to uppercase
- [`lower`](./lower.md) - Convert to lowercase
- [`replace`](./replace.md) - Replace specific text patterns