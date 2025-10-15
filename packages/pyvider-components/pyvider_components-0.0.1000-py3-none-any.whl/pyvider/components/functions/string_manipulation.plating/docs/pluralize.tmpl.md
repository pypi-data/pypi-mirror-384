---
page_title: "Function: pluralize"
description: |-
  Pluralizes words based on count with support for custom plural forms
---

# pluralize (Function)

> Converts words to plural form based on count with intelligent English pluralization rules

The `pluralize` function converts words to their plural form based on a count value. It automatically applies English pluralization rules and allows custom plural forms for irregular words. Returns singular form for count of 1, plural form otherwise.

## When to Use This

- **User interface messages**: Display grammatically correct messages
- **Report generation**: Create proper text in dynamic reports
- **Notification systems**: Generate contextual notifications
- **Data summaries**: Create readable count descriptions
- **Form validation**: Display appropriate error messages

**Anti-patterns (when NOT to use):**
- For non-English text (function uses English rules)
- When count is always singular or plural
- For technical terms that don't follow standard rules
- When grammar requirements are complex

## Quick Start

```terraform
# Basic pluralization
locals {
  item_count = 5
  message = "${local.item_count} ${provider::pyvider::pluralize("file", local.item_count)}"  # Returns: "5 files"
}

# Custom plural form
locals {
  child_count = 3
  description = "${local.child_count} ${provider::pyvider::pluralize("child", local.child_count, "children")}"  # Returns: "3 children"
}
```

## Examples

### Basic Usage

```terraform
# Standard pluralization rules
locals {
  items = ["apple", "box", "child", "mouse"]
  counts = [1, 2, 3, 4]

  # Apply pluralization for each count
  apple_text = "${local.counts[0]} ${provider::pyvider::pluralize("apple", local.counts[0])}"  # "1 apple"
  box_text = "${local.counts[1]} ${provider::pyvider::pluralize("box", local.counts[1])}"      # "2 boxes"
  child_text = "${local.counts[2]} ${provider::pyvider::pluralize("child", local.counts[2], "children")}"  # "3 children"
  mouse_text = "${local.counts[3]} ${provider::pyvider::pluralize("mouse", local.counts[3], "mice")}"      # "4 mice"
}

# Zero and negative counts
locals {
  zero_files = provider::pyvider::pluralize("file", 0)       # "files"
  negative_items = provider::pyvider::pluralize("item", -2)   # "items"
}

# Edge cases
locals {
  decimal_count = provider::pyvider::pluralize("record", 1.5)  # "records" (non-integer counts are plural)
  null_count = provider::pyvider::pluralize("entry", null)     # null
}
```

### Report Generation

```terraform
# Resource usage reports
data "aws_instances" "all" {}

locals {
  instance_count = length(data.aws_instances.all.ids)

  # Generate grammatically correct report
  usage_report = "Currently running ${local.instance_count} ${provider::pyvider::pluralize("instance", local.instance_count)}"

  # More complex reporting
  disk_usage = 1024  # GB
  memory_usage = 16  # GB

  resource_summary = join("\n", [
    "${local.disk_usage} ${provider::pyvider::pluralize("GB", local.disk_usage)} of disk space",
    "${local.memory_usage} ${provider::pyvider::pluralize("GB", local.memory_usage)} of memory"
  ])
}

# Conditional messaging
locals {
  error_count = 3
  warning_count = 1

  status_message = join(", ", compact([
    local.error_count > 0 ? "${local.error_count} ${provider::pyvider::pluralize("error", local.error_count)}" : null,
    local.warning_count > 0 ? "${local.warning_count} ${provider::pyvider::pluralize("warning", local.warning_count)}" : null
  ]))
}

output "reports" {
  value = {
    usage = local.usage_report
    resources = local.resource_summary
    status = local.status_message != "" ? local.status_message : "No issues found"
  }
}
```

### User Interface Messages

```terraform
# Form validation messages
variable "uploaded_files" {
  type    = list(string)
  default = []
}

locals {
  file_count = length(var.uploaded_files)
  max_files = 5

  # Dynamic validation messages
  file_status = local.file_count <= local.max_files ?
    "Uploaded ${local.file_count} ${provider::pyvider::pluralize("file", local.file_count)}" :
    "Error: ${local.file_count} ${provider::pyvider::pluralize("file", local.file_count)} exceeds limit of ${local.max_files}"
}

# Notification templates
locals {
  pending_tasks = 7
  completed_tasks = 23

  # Generate user-friendly notifications
  task_notifications = {
    pending = "You have ${local.pending_tasks} ${provider::pyvider::pluralize("task", local.pending_tasks)} pending"
    completed = "Completed ${local.completed_tasks} ${provider::pyvider::pluralize("task", local.completed_tasks)} today"
  }

  # Irregular plural forms for better UX
  person_count = 4
  person_message = "${local.person_count} ${provider::pyvider::pluralize("person", local.person_count, "people")} online"
}

# Dynamic button labels
locals {
  selected_items = 2

  action_labels = {
    delete = "Delete ${local.selected_items} ${provider::pyvider::pluralize("Item", local.selected_items)}"
    export = "Export ${local.selected_items} ${provider::pyvider::pluralize("Record", local.selected_items)}"
    archive = "Archive ${local.selected_items} ${provider::pyvider::pluralize("Document", local.selected_items)}"
  }
}

output "ui_messages" {
  value = {
    file_status = local.file_status
    notifications = local.task_notifications
    person_status = local.person_message
    actions = local.action_labels
  }
}
```

## Signature

`pluralize(word: string, count: number, custom_plural?: string) -> string`

## Arguments

- **`word`** (string, required) - The word to pluralize. If `null`, returns `null`.
- **`count`** (number, required) - The count to determine singular/plural form. If `null`, returns `null`.
  - Count of exactly `1` returns singular form
  - Count of `0`, negative numbers, or decimal values returns plural form
- **`custom_plural`** (string, optional) - Custom plural form for irregular words. If not provided, applies standard English pluralization rules:
  - Words ending in 's', 'x', 'z', 'ch', 'sh' → add 'es' (box → boxes)
  - Words ending in consonant + 'y' → change 'y' to 'ies' (city → cities)
  - Words ending in 'f' or 'fe' → change to 'ves' (leaf → leaves)
  - Most other words → add 's' (cat → cats)

## Return Value

Returns the appropriately formatted word:
- **Singular form**: When count is exactly `1`
- **Plural form**: When count is `0`, negative, decimal, or greater than `1`
- **Custom plural**: Uses `custom_plural` parameter when provided and count requires plural form
- **Null**: When either `word` or `count` is `null`

## Common Irregular Plurals

For better user experience, consider using `custom_plural` for these common irregular forms:

```terraform
# Common irregular plurals
locals {
  examples = {
    child = provider::pyvider::pluralize("child", 2, "children")       # "children"
    person = provider::pyvider::pluralize("person", 3, "people")       # "people"
    mouse = provider::pyvider::pluralize("mouse", 4, "mice")           # "mice"
    goose = provider::pyvider::pluralize("goose", 2, "geese")          # "geese"
    foot = provider::pyvider::pluralize("foot", 2, "feet")             # "feet"
    tooth = provider::pyvider::pluralize("tooth", 3, "teeth")          # "teeth"
    man = provider::pyvider::pluralize("man", 5, "men")                # "men"
    woman = provider::pyvider::pluralize("woman", 4, "women")          # "women"
    datum = provider::pyvider::pluralize("datum", 10, "data")          # "data"
    criterion = provider::pyvider::pluralize("criterion", 3, "criteria") # "criteria"
  }
}
```

## Related Functions

- [`tostring`](./tostring.md) - Convert numbers to strings for messages
- [`format`](./format.md) - Format strings with placeholders
- [`join`](./join.md) - Join multiple message parts
- [`contains`](./contains.md) - Check for specific words or patterns
- [`replace`](./replace.md) - Replace text in generated messages