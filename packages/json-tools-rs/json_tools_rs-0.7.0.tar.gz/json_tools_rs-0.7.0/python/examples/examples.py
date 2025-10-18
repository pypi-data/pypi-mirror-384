#!/usr/bin/env python3
"""
JSON Tools RS Python Advanced Examples

This example demonstrates the unified JSONTools API in Python with advanced features
including collision handling, filtering, transformations, and batch processing.
"""

from typing import Any, Dict

import json_tools_rs


def main() -> None:
    print("JSON Tools RS - Advanced Python Examples")
    print("Perfect Type Matching: Input Type = Output Type!")
    print("Unified JSONTools API with Advanced Features")
    print("=" * 50)

    # Example 1: Basic flattening
    print("\n1. Basic Flattening")
    print("-" * 20)

    # Now you can pass Python dicts directly - no need to serialize to JSON!
    json_data = {
        "user": {
            "profile": {"name": "John Doe", "age": 30, "email": "john@example.com"},
            "settings": {"theme": "dark", "notifications": True},
        },
        "metadata": {"created": "2024-01-01", "version": "1.0"},
    }

    print(f"Input (Python dict): {json_data}")

    # Use the unified JSONTools API with flatten() method
    tools = json_tools_rs.JSONTools().flatten()
    result = tools.execute(json_data)  # Pass Python dict directly!

    print(f"Output: {result}")

    # Example 2: Advanced configuration
    print("\n2. Advanced Configuration")
    print("-" * 30)

    # Use Python dict directly (much more convenient!)
    python_data: Dict[str, Any] = {
        "User": {
            "Name": "Alice",
            "Email": "",
            "Details": None,  # Python None becomes JSON null
            "Preferences": {},
            "Tags": [],
            "Active": True,
        }
    }

    print(f"Input (Python dict): {python_data}")

    # Configure with builder pattern using unified JSONTools API
    advanced_tools = (
        json_tools_rs.JSONTools()
        .flatten()
        .remove_empty_strings(True)
        .remove_nulls(True)
        .remove_empty_objects(True)
        .remove_empty_arrays(True)
        .separator("_")
        .lowercase_keys(True)
    )

    result = advanced_tools.execute(python_data)  # Pass Python dict directly!
    print(f"Output: {result}")

    # Example 3: Key and value replacements
    print("\n3. Key and Value Replacements")
    print("-" * 35)

    # Use Python dict directly
    python_patterns = {
        "user_name": "bob@example.com",
        "admin_role": "super",
        "user_status": "active@example.com",
    }

    print(f"Input (Python dict): {python_patterns}")

    replacement_tools = (
        json_tools_rs.JSONTools()
        .flatten()
        .key_replacement("^(user|admin)_", "")  # Standard Rust regex syntax
        .value_replacement("@example.com", "@company.org")
    )

    result = replacement_tools.execute(
        python_patterns
    )  # Pass Python dict directly!
    print(f"Output: {result}")

    # Example 4: Batch processing
    print("\n4. Batch Processing (Mixed Types)")
    print("-" * 35)

    # Mix of JSON strings and Python dicts
    mixed_batch = [
        '{"order1": {"item": "laptop", "price": 999}}',  # JSON string
        {"order2": {"item": "mouse", "price": 25}},  # Python dict
        {"order3": {"item": "keyboard", "price": 75}},  # Python dict
    ]

    print(f"Input (mixed types): {mixed_batch}")

    batch_tools = json_tools_rs.JSONTools().flatten()
    results = batch_tools.execute(mixed_batch)  # Handles mixed types automatically!

    print(f"Output: {results}")

    # Example 5: Basic unflattening
    print("\n5. Basic Unflattening")
    print("-" * 20)

    # Use the flattened result from Example 1
    flattened_data = result  # This is a Python dict from Example 1
    print(f"Input (flattened dict): {flattened_data}")

    # Use the unified JSONTools API with unflatten() method
    unflatten_tools = json_tools_rs.JSONTools().unflatten()
    restored = unflatten_tools.execute(flattened_data)  # Pass Python dict directly!

    print(f"Output (restored): {restored}")
    print(f"Type preserved: {type(restored)}")

    # Example 6: Advanced JSONTools unflattening configuration
    print("\n6. Advanced Unflattening Configuration")
    print("-" * 40)

    # Create some flattened data with prefixes
    flattened_with_prefixes = {
        "PREFIX_name": "john@company.org",
        "PREFIX_age": 30,
        "PREFIX_profile_city": "NYC",
    }

    print(f"Input (flattened dict): {flattened_with_prefixes}")

    # Configure unflattening with transformations using unified API
    advanced_unflatten_tools = (
        json_tools_rs.JSONTools()
        .unflatten()
        .separator("_")
        .lowercase_keys(True)
        .key_replacement("prefix_", "user_")
        .value_replacement("@company.org", "@example.com")
    )

    restored_advanced = advanced_unflatten_tools.execute(flattened_with_prefixes)
    print(f"Output (transformed): {restored_advanced}")

    # Example 7: Roundtrip demonstration
    print("\n7. Complete Roundtrip (Flatten → Unflatten)")
    print("-" * 45)

    # Start with complex nested data
    original_complex = {
        "user": {
            "profile": {"name": "Alice", "age": 28},
            "emails": ["alice@work.com", "alice@personal.com"],
            "settings": {
                "theme": "light",
                "notifications": {"email": True, "sms": False},
            },
        },
        "metadata": {"created": "2024-01-01", "version": 2.1},
    }

    print(f"Original: {original_complex}")

    # Flatten using unified JSONTools API
    roundtrip_flatten_tools = json_tools_rs.JSONTools().flatten()
    flattened_complex = roundtrip_flatten_tools.execute(original_complex)
    print(f"Flattened: {flattened_complex}")

    # Unflatten using unified JSONTools API
    roundtrip_unflatten_tools = json_tools_rs.JSONTools().unflatten()
    restored_complex = roundtrip_unflatten_tools.execute(flattened_complex)
    print(f"Restored: {restored_complex}")

    # Verify they're identical
    print(f"Roundtrip successful: {original_complex == restored_complex}")

    # Example 8: Batch unflattening with type preservation
    print("\n8. Batch Unflattening (Type Preservation)")
    print("-" * 45)

    # Create batch of flattened data (mix of strings and dicts)
    flattened_batch_strings = [
        '{"order.id": 1, "order.item": "laptop"}',
        '{"order.id": 2, "order.item": "mouse"}',
        '{"order.id": 3, "order.item": "keyboard"}',
    ]

    flattened_batch_dicts = [
        {"product.name": "laptop", "product.price": 999},
        {"product.name": "mouse", "product.price": 25},
        {"product.name": "keyboard", "product.price": 75},
    ]

    print(f"String batch input: {flattened_batch_strings}")

    batch_unflatten_tools = json_tools_rs.JSONTools().unflatten()

    # Process string batch → returns list of strings
    string_results = batch_unflatten_tools.execute(flattened_batch_strings)
    print(f"String batch output: {string_results}")
    print(f"Output types: {[type(item) for item in string_results]}")

    print(f"\nDict batch input: {flattened_batch_dicts}")

    # Process dict batch → returns list of dicts
    dict_results = batch_unflatten_tools.execute(flattened_batch_dicts)
    print(f"Dict batch output: {dict_results}")
    print(f"Output types: {[type(item) for item in dict_results]}")

    # Example 9: Collision handling strategies
    print("\n9. Collision Handling Strategies")
    print("-" * 35)

    # Data that will cause key collisions after transformation
    collision_data = {
        "user_name": "John",
        "admin_name": "Jane",
        "guest_name": "Bob",
    }

    print(f"Input (will cause collisions): {collision_data}")

    # Strategy 1: Handle collisions by collecting values into arrays
    handle_collision_tools = (
        json_tools_rs.JSONTools()
        .flatten()
        .key_replacement("(user|admin|guest)_", "")  # Standard Rust regex syntax
        .handle_key_collision(True)
    )

    collision_result = handle_collision_tools.execute(collision_data)
    print(f"Handle collision (arrays): {collision_result}")
    print("Note: All colliding values are collected into an array")

    print("\n" + "=" * 60)
    print("10. Parallel Processing (Automatic)")
    print("=" * 60)

    # Parallel processing is automatic for large batches (10+ items by default)
    large_batch = [{"user_id": i, "data": {"value": i * 10}} for i in range(50)]

    # Default: automatic parallel processing for batches >= 10 items
    default_tools = json_tools_rs.JSONTools().flatten()
    results = default_tools.execute(large_batch)
    print(f"Processed {len(results)} items (automatic parallelization)")
    print(f"Sample result: {results[0]}")

    # Configure parallel processing thresholds
    custom_parallel_tools = (
        json_tools_rs.JSONTools()
        .flatten()
        .parallel_threshold(25)  # Only parallelize batches of 25+ items
        .num_threads(4)  # Limit to 4 threads
        .nested_parallel_threshold(200)  # Parallelize large nested structures (200+ keys/items)
    )

    results = custom_parallel_tools.execute(large_batch)
    print(f"Custom parallel config: processed {len(results)} items")
    print("Note: Parallel processing provides significant speedup for large batches")
    print("      and large nested structures without any code changes!")

    print("\n" + "=" * 60)
    print("✅ All examples completed successfully!")
    print("🚀 JSONTools provides a complete, unified API for JSON manipulation")
    print("   with perfect type preservation, advanced collision handling,")
    print("   and automatic parallel processing for optimal performance!")


if __name__ == "__main__":
    main()
