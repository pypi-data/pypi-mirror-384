locals {
  example_result = pyvider_nested_data_processor(
    # Function arguments here
  )
}

output "function_result" {
  description = "Result of pyvider_nested_data_processor function"  
  value       = local.example_result
}
