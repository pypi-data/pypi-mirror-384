# JSON Tools RS

A high-performance Rust library for advanced JSON manipulation with SIMD-accelerated parsing, providing unified flattening and unflattening operations through a clean builder pattern API.

[![Crates.io](https://img.shields.io/crates/v/json-tools-rs.svg)](https://crates.io/crates/json-tools-rs)
[![Documentation](https://docs.rs/json-tools-rs/badge.svg)](https://docs.rs/json-tools-rs)
[![License](https://img.shields.io/badge/license-MIT%2FApache--2.0-blue.svg)](LICENSE-MIT)

## Why JSON Tools RS?

JSON Tools RS is designed for developers who need to:
- **Transform nested JSON** into flat structures for databases, CSV exports, or analytics
- **Clean and normalize** JSON data from external APIs or user input
- **Process large batches** of JSON documents efficiently
- **Maintain type safety** with perfect roundtrip support (flatten → unflatten → original)
- **Work with both Rust and Python** using the same consistent API

Unlike simple JSON parsers, JSON Tools RS provides a complete toolkit for JSON transformation with production-ready performance and error handling.

## Features

- 🚀 **Unified API**: Single `JSONTools` entry point for flattening, unflattening, or pass-through transforms (`.normal()`)
- 🔧 **Builder Pattern**: Fluent, chainable API for easy configuration and method chaining
- ⚡ **High Performance**: SIMD-accelerated JSON parsing with FxHashMap and optimized memory allocations
- 🚄 **Parallel Processing**: Built-in Rayon-based parallelism for 3-5x speedup on batch operations (automatic, no configuration needed)
- 🎯 **Complete Roundtrip**: Flatten JSON and unflatten back to original structure with perfect fidelity
- 🧹 **Comprehensive Filtering**: Remove empty strings, nulls, empty objects, and empty arrays (works for both flatten and unflatten)
- 🔄 **Advanced Replacements**: Literal and regex-based key/value replacements using standard Rust regex syntax
- 🛡️ **Collision Handling**: Intelligent `.handle_key_collision(true)` to collect colliding values into arrays
- 🔀 **Automatic Type Conversion**: Convert strings to numbers and booleans with `.auto_convert_types(true)` - handles currency, thousands separators, scientific notation
- 📦 **Batch Processing**: Process single JSON or batches; Python also supports dicts and lists of dicts
- 🐍 **Python Bindings**: Full Python support with perfect type preservation (input type = output type)
- 🧰 **Robust Errors**: Comprehensive `JsonToolsError` enum with helpful suggestions for debugging
- 🔥 **Performance Optimizations**: FxHashMap (~15-30% faster), SIMD parsing, Cow-based string handling, and automatic parallel processing

## Table of Contents

- [Why JSON Tools RS?](#why-json-tools-rs)
- [Features](#features)
- [Quick Start](#quick-start)
  - [Rust Examples](#rust---unified-jsontools-api)
  - [Python Examples](#python---unified-jsontools-api)
- [Quick Reference](#quick-reference)
- [Installation](#installation)
- [Performance](#performance)
- [API Reference](#api-reference)
  - [Core Methods](#core-methods)
  - [Configuration Methods](#configuration-methods)
  - [Input/Output Types](#inputoutput-types)
- [Error Handling](#error-handling)
- [Common Use Cases](#common-use-cases)
- [Examples and Testing](#examples-and-testing)
- [Limitations and Known Issues](#limitations-and-known-issues)
- [FAQ](#frequently-asked-questions-faq)
- [Contributing](#contributing)
- [License](#license)
- [Changelog](#changelog)

## Quick Start

### Rust - Unified JSONTools API

The `JSONTools` struct provides a unified builder pattern API for all JSON manipulation operations. Simply call `.flatten()` or `.unflatten()` to set the operation mode, then chain configuration methods and call `.execute()`.

#### Basic Flattening

```rust
use json_tools_rs::{JSONTools, JsonOutput};

let json = r#"{"user": {"name": "John", "profile": {"age": 30, "city": "NYC"}}}"#;
let result = JSONTools::new()
    .flatten()
    .execute(json)?;

if let JsonOutput::Single(flattened) = result {
    println!("{}", flattened);
}
// Output: {"user.name": "John", "user.profile.age": 30, "user.profile.city": "NYC"}
```

#### Advanced Flattening with Filtering

```rust
use json_tools_rs::{JSONTools, JsonOutput};

let json = r#"{"user": {"name": "John", "details": {"age": null, "city": ""}}}"#;
let result = JSONTools::new()
    .flatten()
    .separator("::")
    .lowercase_keys(true)
    .key_replacement("(User|Admin)_", "")
    .value_replacement("@example.com", "@company.org")
    .remove_empty_strings(true)
    .remove_nulls(true)
    .remove_empty_objects(true)
    .remove_empty_arrays(true)
    .execute(json)?;

if let JsonOutput::Single(flattened) = result {
    println!("{}", flattened);
}
// Output: {"user::name": "John"}
```

#### Basic Unflattening

```rust
use json_tools_rs::{JSONTools, JsonOutput};

let flattened = r#"{"user.name": "John", "user.profile.age": 30}"#;
let result = JSONTools::new()
    .unflatten()
    .execute(flattened)?;

match result {
    JsonOutput::Single(unflattened) => println!("{}", unflattened),
    JsonOutput::Multiple(_) => unreachable!(),
}
// Output: {"user": {"name": "John", "profile": {"age": 30}}}
```

#### Advanced Unflattening with Configuration

```rust
use json_tools_rs::{JSONTools, JsonOutput};

let flattened = r#"{"user::name": "John", "user::age": 30, "user::email": ""}"#;
let result = JSONTools::new()
    .unflatten()
    .separator("::")
    .lowercase_keys(true)
    .remove_empty_strings(true)
    .remove_nulls(true)
    .execute(flattened)?;

match result {
    JsonOutput::Single(unflattened) => println!("{}", unflattened),
    JsonOutput::Multiple(_) => unreachable!(),
}
// Output: {"user": {"name": "John", "age": 30}}
```

#### Key Collision Handling

When transformations make different keys end up identical, enable collision handling to collect values into arrays.

```rust
use json_tools_rs::{JSONTools, JsonOutput};

let json = r#"{"user_name": "John", "admin_name": "Jane"}"#;
let result = JSONTools::new()
    .flatten()
    .key_replacement("(user|admin)_", "") // both become "name"
    .handle_key_collision(true)                    // collect colliding values
    .execute(json)?;

if let JsonOutput::Single(flattened) = result {
    println!("{}", flattened);
}
// Output: {"name": ["John", "Jane"]}
```

#### Automatic Type Conversion

Convert string values to numbers and booleans automatically for data cleaning and normalization.

```rust
use json_tools_rs::{JSONTools, JsonOutput};

let json = r#"{
    "id": "123",
    "price": "$1,234.56",
    "quantity": "1,000",
    "active": "true",
    "verified": "FALSE",
    "name": "Product"
}"#;

let result = JSONTools::new()
    .flatten()
    .auto_convert_types(true)
    .execute(json)?;

if let JsonOutput::Single(flattened) = result {
    println!("{}", flattened);
}
// Output: {
//   "id": 123,
//   "price": 1234.56,
//   "quantity": 1000,
//   "active": true,
//   "verified": false,
//   "name": "Product"  // Keeps as string (not a valid number or boolean)
// }
```

#### Perfect Roundtrip Support

```rust
use json_tools_rs::{JSONTools, JsonOutput};

let original = r#"{"user": {"name": "John", "age": 30}, "items": [1, 2, {"nested": "value"}]}"#;

// Flatten
let flattened = JSONTools::new().flatten().execute(original)?;
let flattened_str = match flattened { JsonOutput::Single(s) => s, _ => unreachable!() };

// Unflatten back to original structure
let restored = JSONTools::new().unflatten().execute(&flattened_str)?;
let restored_str = match restored { JsonOutput::Single(s) => s, _ => unreachable!() };

// Verify perfect roundtrip
assert_eq!(
    serde_json::from_str::<serde_json::Value>(original)?,
    serde_json::from_str::<serde_json::Value>(&restored_str)?
);
```


### Python - Unified JSONTools API

The Python bindings provide the same unified `JSONTools` API with **perfect type matching**: input type equals output type. This makes the API predictable and easy to use.

#### Type Preservation Examples

```python
import json_tools_rs as jt

# Example 1: dict input → dict output
result = jt.JSONTools().flatten().execute({"user": {"name": "John", "age": 30}})
print(result)  # {'user.name': 'John', 'user.age': 30}
print(type(result))  # <class 'dict'>

# Example 2: JSON string input → JSON string output
result = jt.JSONTools().flatten().execute('{"user": {"name": "John", "age": 30}}')
print(result)  # '{"user.name": "John", "user.age": 30}'
print(type(result))  # <class 'str'>

# Example 3: List[dict] input → List[dict] output
batch = [{"a": {"b": 1}}, {"c": {"d": 2}}]
result = jt.JSONTools().flatten().execute(batch)
print(result)  # [{'a.b': 1}, {'c.d': 2}]
print(type(result[0]))  # <class 'dict'>

# Example 4: List[str] input → List[str] output
batch = ['{"a": {"b": 1}}', '{"c": {"d": 2}}']
result = jt.JSONTools().flatten().execute(batch)
print(result)  # ['{"a.b": 1}', '{"c.d": 2}']
print(type(result[0]))  # <class 'str'>
```

#### Basic Usage

```python
import json_tools_rs as jt

# Basic flattening - dict input → dict output
result = jt.JSONTools().flatten().execute({"user": {"name": "John", "age": 30}})
print(result)  # {'user.name': 'John', 'user.age': 30}

# Basic unflattening - dict input → dict output
result = jt.JSONTools().unflatten().execute({"user.name": "John", "user.age": 30})
print(result)  # {'user': {'name': 'John', 'age': 30}}
```

#### Advanced Configuration

```python
import json_tools_rs as jt

# Advanced flattening with filtering and transformations
tools = (jt.JSONTools()
    .flatten()
    .separator("::")
    .lowercase_keys(True)
    .remove_empty_strings(True)
    .remove_nulls(True)
    .remove_empty_objects(True)
    .remove_empty_arrays(True)
    .key_replacement("(User|Admin)_", "")
    .value_replacement("@example.com", "@company.org"))

data = {"User_name": "John", "Admin_email": "john@example.com", "empty": "", "null_val": None}
result = tools.execute(data)
print(result)  # {'name': 'John', 'email': 'john@company.org'}

# Advanced unflattening with same configuration options
result = (jt.JSONTools()
    .unflatten()
    .separator("::")
    .lowercase_keys(True)
    .remove_empty_strings(True)
    .remove_nulls(True)
    .key_replacement("prefix_", "user_")
    .value_replacement("@company.org", "@example.com")
    .execute({"PREFIX_NAME": "john", "PREFIX_EMAIL": "john@company.org", "empty": ""}))
print(result)  # {'user': {'name': 'john', 'email': 'john@example.com'}}
```

#### Key Collision Handling

When transformations make different keys end up identical, enable collision handling to collect values into arrays.

```python
import json_tools_rs as jt

tools = (jt.JSONTools()
    .flatten()
    .key_replacement("(user|admin)_", "")  # both become "name"
    .handle_key_collision(True))                    # collect colliding values

data = {"user_name": "John", "admin_name": "Jane"}
print(tools.execute(data))  # {'name': ['John', 'Jane']}
```

#### Automatic Type Conversion

Convert string values to numbers and booleans automatically for data cleaning and normalization.

```python
import json_tools_rs as jt

# Type conversion with dict input
data = {
    "id": "123",
    "price": "$1,234.56",
    "quantity": "1,000",
    "active": "true",
    "verified": "FALSE",
    "name": "Product"
}

result = (jt.JSONTools()
    .flatten()
    .auto_convert_types(True)
    .execute(data))

print(result)
# Output: {
#   'id': 123,
#   'price': 1234.56,
#   'quantity': 1000,
#   'active': True,
#   'verified': False,
#   'name': 'Product'  # Keeps as string (not a valid number or boolean)
# }

# Works with JSON strings too
json_str = '{"id": "456", "enabled": "true", "amount": "€99.99"}'
result = jt.JSONTools().flatten().auto_convert_types(True).execute(json_str)
print(result)  # '{"id": 456, "enabled": true, "amount": 99.99}'
```

#### Batch Processing with Type Preservation

```python
import json_tools_rs as jt

tools = jt.JSONTools().flatten()

# List[str] input → List[str] output
str_batch = ['{"a": {"b": 1}}', '{"c": {"d": 2}}']
results = tools.execute(str_batch)
print(results)  # ['{"a.b": 1}', '{"c.d": 2}']

# List[dict] input → List[dict] output
dict_batch = [{"a": {"b": 1}}, {"c": {"d": 2}}]
results = tools.execute(dict_batch)
print(results)  # [{'a.b': 1}, {'c.d': 2}]

# Mixed types are handled automatically
mixed_batch = ['{"a": 1}', {"b": {"c": 2}}]
results = tools.execute(mixed_batch)
print(results)  # ['{"a": 1}', {'b.c': 2}]
```

#### Perfect Roundtrip Support

```python
import json_tools_rs

# Perfect roundtrip with Python dicts
original = {"user": {"name": "John", "age": 30}, "items": [1, 2, {"nested": "value"}]}

# Flatten
flattened = json_tools_rs.JSONTools().flatten().execute(original)
print(f"Flattened: {flattened}")

# Unflatten back to original structure
restored = json_tools_rs.JSONTools().unflatten().execute(flattened)
print(f"Restored: {restored}")

# Verify perfect roundtrip
assert original == restored  # Perfect roundtrip with dicts!
```

## Quick Reference

### Method Cheat Sheet

| Method | Description | Example |
|--------|-------------|---------|
| `.flatten()` | Set operation mode to flatten | `JSONTools::new().flatten()` |
| `.unflatten()` | Set operation mode to unflatten | `JSONTools::new().unflatten()` |
| `.separator(sep)` | Set key separator (default: `"."`) | `.separator("::")` |
| `.lowercase_keys(bool)` | Convert keys to lowercase | `.lowercase_keys(true)` |
| `.remove_empty_strings(bool)` | Remove empty string values | `.remove_empty_strings(true)` |
| `.remove_nulls(bool)` | Remove null values | `.remove_nulls(true)` |
| `.remove_empty_objects(bool)` | Remove empty objects `{}` | `.remove_empty_objects(true)` |
| `.remove_empty_arrays(bool)` | Remove empty arrays `[]` | `.remove_empty_arrays(true)` |
| `.key_replacement(find, replace)` | Replace key patterns (regex or literal) | `.key_replacement("user_", "")` |
| `.value_replacement(find, replace)` | Replace value patterns (regex or literal) | `.value_replacement("@old.com", "@new.com")` |
| `.handle_key_collision(bool)` | Collect colliding keys into arrays | `.handle_key_collision(true)` |
| `.execute(input)` | Execute the configured operation | `.execute(json_string)` |

### Common Patterns

**Flatten with filtering:**
```rust
JSONTools::new()
    .flatten()
    .remove_nulls(true)
    .remove_empty_strings(true)
    .execute(json)?
```

**Unflatten with custom separator:**
```rust
JSONTools::new()
    .unflatten()
    .separator("::")
    .execute(flattened_json)?
```

**Transform keys and values:**
```rust
JSONTools::new()
    .flatten()
    .lowercase_keys(true)
    .key_replacement("(user|admin)_", "")
    .value_replacement("@example.com", "@company.org")
    .execute(json)?
```

**Handle key collisions:**
```rust
JSONTools::new()
    .flatten()
    .key_replacement("prefix_", "")
    .handle_key_collision(true)  // Colliding values → arrays
    .execute(json)?
```

## Installation

### Rust

Add to your `Cargo.toml`:

```toml
[dependencies]
json-tools-rs = "0.7.0"
```

Or install via cargo:

```bash
cargo add json-tools-rs
```

**Note**: Parallel processing is built-in and automatic - no feature flags needed!

### Python

#### From PyPI (Recommended)

```bash
pip install json-tools-rs
```

#### Build from Source with Maturin

If you want to build from source or contribute to development:

```bash
# Clone the repository
git clone https://github.com/amaye15/JSON-Tools-rs.git
cd JSON-Tools-rs

# Install maturin if you haven't already
pip install maturin

# Build and install the Python package
maturin develop --features python

# Or build a wheel for distribution
maturin build --features python --release
```

#### Development Setup

```bash
# For development with automatic rebuilds
maturin develop --features python

# Run Python examples
python python/examples/basic_usage.py
python python/examples/examples.py
```

## Performance

JSON Tools RS delivers exceptional performance through multiple carefully implemented optimizations:

### Performance Optimizations

1. **FxHashMap** - ~15-30% faster string key operations compared to standard HashMap
   - Optimized hash function for string keys
   - Reduced collision overhead

2. **SIMD JSON Parsing** - Hardware-accelerated parsing and serialization via simd-json
   - Leverages CPU SIMD instructions for parallel processing
   - Significantly faster than standard serde_json for large payloads

3. **Reduced Allocations** - Minimized memory allocations using Cow (Copy-on-Write) and scoped buffers
   - ~50% reduction in string clones during key transformations
   - Efficient memory reuse across operations

4. **Smart Capacity Management** - Pre-sized maps and string builders to minimize rehashing
   - Reduces reallocation overhead
   - Improves cache locality

5. **Parallel Batch Processing** (built-in, always enabled) - Rayon-based parallelism for batch operations
   - **3-5x speedup** for batches of 10+ items on multi-core CPUs
   - Adaptive threshold prevents overhead for small batches
   - Zero per-item memory overhead
   - Thread-safe regex cache with Arc<Regex> for O(1) cloning

### Parallel Processing

Parallel processing is **built-in and automatic** - no feature flags or special configuration needed!

JSON-Tools-rs provides **two levels of parallelism**:

#### 1. Batch-Level Parallelism (Across Multiple Documents)

Process multiple JSON documents in parallel automatically.

**Performance Gains:**
- Batch size 10: **2.5x faster**
- Batch size 50: **3.3x faster**
- Batch size 100: **3.3x faster**
- Batch size 500: **5.3x faster**
- Batch size 1000: **5.4x faster**

**Configuration (Optional):**

```rust
use json_tools_rs::JSONTools;

// Default threshold (10 items) - optimal for most use cases
// Parallelism activates automatically for batches ≥ 10 items
let result = JSONTools::new()
    .flatten()
    .execute(batch)?;

// Custom threshold for fine-tuning
let result = JSONTools::new()
    .flatten()
    .parallel_threshold(50)  // Only parallelize batches ≥ 50 items
    .execute(batch)?;

// Custom thread count
let result = JSONTools::new()
    .flatten()
    .num_threads(Some(4))  // Use exactly 4 threads
    .execute(batch)?;

// Environment variables (runtime configuration)
// JSON_TOOLS_PARALLEL_THRESHOLD=20 cargo run
// JSON_TOOLS_NUM_THREADS=4 cargo run
```

**How it works:**
- Batches below threshold (default: 10): Sequential processing (no overhead)
- Batches 10-1000: Rayon work-stealing parallelism
- Batches > 1000: Chunked processing for optimal cache locality
- Each worker thread gets its own regex cache
- Zero per-item memory increase (only 8-16MB one-time thread pool)
- Thread count defaults to number of logical CPUs (configurable via `num_threads()` or `JSON_TOOLS_NUM_THREADS`)

#### 2. Nested Parallelism (Within Large Documents)

For large individual JSON documents, nested parallelism automatically parallelizes the processing of large objects and arrays **within** a single document.

**Performance Gains:**
- Large documents (20,000+ items): **7-12% faster**
- Very large documents (100,000+ items): **7-12% faster**
- Small/medium documents: No overhead (stays sequential)

**Configuration (Optional):**

```rust
use json_tools_rs::JSONTools;

// Default threshold (100 items) - optimal for most use cases
// Objects/arrays with 100+ keys/items are processed in parallel
let result = JSONTools::new()
    .flatten()
    .execute(large_json)?;

// Custom threshold for very large documents
let result = JSONTools::new()
    .flatten()
    .nested_parallel_threshold(50)  // More aggressive parallelism
    .execute(large_json)?;

// Disable nested parallelism (for small/medium documents)
let result = JSONTools::new()
    .flatten()
    .nested_parallel_threshold(usize::MAX)  // Disable
    .execute(json)?;

// Environment variable (runtime configuration)
// JSON_TOOLS_NESTED_PARALLEL_THRESHOLD=200 cargo run
```

**How it works:**
- Objects/arrays below threshold (default: 100): Sequential processing
- Objects/arrays above threshold: Parallel processing using Rayon
- Each parallel branch gets its own string builder
- Results are merged efficiently with minimal overhead
- Rayon's work-stealing automatically balances load across CPU cores
- Minimal memory overhead (< 1 MB for very large documents)

**When to use:**
- ✅ Large JSON documents (20,000+ items)
- ✅ Very large JSON documents (100,000+ items)
- ✅ Wide, flat structures (many keys at same level)
- ❌ Small documents (< 5,000 items) - no benefit
- ❌ Deeply nested but narrow structures - marginal benefit

### Benchmark Results

Performance varies by workload complexity, but typical results on modern hardware include:

- **Basic flattening**: 2,000+ operations/ms
- **Advanced configuration**: 1,300+ operations/ms (with filtering and transformations)
- **Regex replacements**: 1,800+ operations/ms (with pattern matching)
- **Batch processing**: 1,900+ operations/ms (for multiple JSON documents)
- **Roundtrip operations**: 1,000+ flatten→unflatten cycles/ms

*Note: Benchmarks run on typical development hardware. Your results may vary based on CPU, memory, and workload characteristics.*

### Running Benchmarks

```bash
# Run comprehensive benchmarks
cargo bench

# Run specific benchmark suites
cargo bench flatten
cargo bench unflatten
cargo bench roundtrip

# Generate HTML reports (available in target/criterion)
cargo bench --features html_reports
```

## API Reference

### JSONTools - Unified API

The `JSONTools` struct is the single entry point for all JSON manipulation operations. It provides a builder pattern API that works for both flattening and unflattening operations.

#### Core Methods

- **`JSONTools::new()`** - Create a new instance with default settings
- **`.flatten()`** - Configure for flattening operations (converts nested JSON to flat key-value pairs)
- **`.unflatten()`** - Configure for unflattening operations (converts flat key-value pairs back to nested JSON)
- **`.normal()`** - Configure for pass-through operations (apply transformations without flattening/unflattening)
- **`.execute(input)`** - Execute the configured operation on the provided input

#### Configuration Methods

All configuration methods are chainable and available for both flattening and unflattening operations:

##### Key/Value Transformation Methods

- **`.separator(sep: &str)`** - Set separator for nested keys (default: `"."`)
  - Example: `separator("::")` makes keys like `user::name::first`

- **`.lowercase_keys(value: bool)`** - Convert all keys to lowercase
  - Example: `UserName` becomes `username`

- **`.key_replacement(find: &str, replace: &str)`** - Add key replacement pattern
  - Supports standard Rust regex syntax (automatically detected)
  - Falls back to literal string replacement if regex compilation fails
  - Example: `key_replacement("(user|admin)_", "")` removes prefixes

- **`.value_replacement(find: &str, replace: &str)`** - Add value replacement pattern
  - Supports standard Rust regex syntax (automatically detected)
  - Falls back to literal string replacement if regex compilation fails
  - Example: `value_replacement("@example.com", "@company.org")` updates email domains

##### Filtering Methods

All filtering methods work for both flatten and unflatten operations:

- **`.remove_empty_strings(value: bool)`** - Remove keys with empty string values (`""`)
- **`.remove_nulls(value: bool)`** - Remove keys with null values
- **`.remove_empty_objects(value: bool)`** - Remove keys with empty object values (`{}`)
- **`.remove_empty_arrays(value: bool)`** - Remove keys with empty array values (`[]`)

##### Collision Handling Methods

- **`.handle_key_collision(value: bool)`** - When enabled, collects values with identical keys into arrays
  - Useful when transformations cause different keys to become identical
  - Example: After removing prefixes, `user_name` and `admin_name` both become `name`
  - With collision handling: `{"name": ["John", "Jane"]}`
  - Without collision handling: Last value wins

##### Type Conversion Methods

- **`.auto_convert_types(enable: bool)`** - Automatically convert string values to numbers and booleans
  - **Number conversion**: Handles various formats including:
    - Basic numbers: `"123"` → `123`, `"45.67"` → `45.67`, `"-10"` → `-10`
    - Thousands separators: `"1,234.56"` → `1234.56` (US), `"1.234,56"` → `1234.56` (EU)
    - Currency symbols: `"$123.45"` → `123.45`, `"€99.99"` → `99.99`
    - Scientific notation: `"1e5"` → `100000`, `"1.23e-4"` → `0.000123`
  - **Boolean conversion**: Only these exact variants:
    - `"true"`, `"TRUE"`, `"True"` → `true`
    - `"false"`, `"FALSE"`, `"False"` → `false`
  - **Lenient behavior**: If conversion fails, keeps the original string value (no errors thrown)
  - **Works for all modes**: `.flatten()`, `.unflatten()`, and `.normal()`
  - **Example**:
    ```rust
    let json = r#"{"id": "123", "price": "$1,234.56", "active": "true"}"#;
    let result = JSONTools::new()
        .flatten()
        .auto_convert_types(true)
        .execute(json)?;
    // Result: {"id": 123, "price": 1234.56, "active": true}
    ```

#### Input/Output Types

**Rust:**
- `&str` (JSON string) → `JsonOutput::Single(String)`
- `Vec<&str>` or `Vec<String>` → `JsonOutput::Multiple(Vec<String>)`

**Python (Perfect Type Preservation):**
- `str` → `str` (JSON string input → JSON string output)
- `dict` → `dict` (Python dict input → Python dict output)
- `List[str]` → `List[str]` (list of JSON strings → list of JSON strings)
- `List[dict]` → `List[dict]` (list of Python dicts → list of Python dicts)
- Mixed lists preserve original element types

### Error Handling

The library uses a comprehensive `JsonToolsError` enum that provides detailed error information and actionable suggestions for debugging:

#### Error Variants

- **`JsonParseError`** - JSON parsing failures with syntax suggestions
  - Triggered by: Invalid JSON syntax, malformed input
  - Suggestion: Verify JSON syntax, check for missing quotes, trailing commas, unescaped characters

- **`RegexError`** - Regex pattern compilation errors with pattern suggestions
  - Triggered by: Invalid regex patterns in `key_replacement()` or `value_replacement()`
  - Suggestion: Verify regex syntax using standard Rust regex patterns

- **`InvalidJsonStructure`** - Structure validation errors with format guidance
  - Triggered by: Incompatible JSON structure for the requested operation
  - Suggestion: Ensure input matches expected format (nested for flatten, flat for unflatten)

- **`ConfigurationError`** - API usage errors with correct usage examples
  - Triggered by: Calling `.execute()` without setting operation mode
  - Suggestion: Call `.flatten()` or `.unflatten()` before `.execute()`

- **`BatchProcessingError`** - Batch operation errors with item-specific details
  - Triggered by: Invalid item in batch processing
  - Includes: Index of failing item for easy debugging
  - Suggestion: Check the JSON at the specified index

- **`InputValidationError`** - Input validation errors with helpful guidance
  - Triggered by: Invalid input type or empty input
  - Suggestion: Ensure input is valid JSON string, dict, or list

- **`SerializationError`** - JSON serialization failures with debugging information
  - Triggered by: Internal serialization errors (rare)
  - Suggestion: Report as potential bug

#### Error Handling Examples

**Rust:**
```rust
use json_tools_rs::{JSONTools, JsonToolsError};

match JSONTools::new().flatten().execute(invalid_json) {
    Ok(result) => println!("Success: {:?}", result),
    Err(JsonToolsError::JsonParseError { message, suggestion, .. }) => {
        eprintln!("Parse error: {}", message);
        eprintln!("💡 {}", suggestion);
    }
    Err(e) => eprintln!("Error: {}", e),
}
```

**Python:**
```python
import json_tools_rs

try:
    result = json_tools_rs.JSONTools().flatten().execute(invalid_json)
except json_tools_rs.JsonToolsError as e:
    print(f"Error: {e}")
    # Error messages include helpful suggestions
```

## Common Use Cases

### 1. Data Pipeline Transformations

Flatten nested API responses for easier processing in data pipelines:

```rust
use json_tools_rs::{JSONTools, JsonOutput};

let api_response = r#"{
    "user": {
        "id": 123,
        "profile": {"name": "John", "email": "john@example.com"},
        "settings": {"theme": "dark", "notifications": true}
    }
}"#;

let flattened = JSONTools::new()
    .flatten()
    .execute(api_response)?;
// Result: {"user.id": 123, "user.profile.name": "John", ...}
// Perfect for CSV export, database insertion, or analytics
```

### 2. Data Cleaning and Normalization

Remove empty values and normalize keys for consistent data processing:

```python
import json_tools_rs as jt

# Clean messy data from external sources
messy_data = {
    "UserName": "Alice",
    "Email": "",           # Empty string
    "Age": None,           # Null value
    "Preferences": {},     # Empty object
    "Tags": []             # Empty array
}

cleaned = (jt.JSONTools()
    .flatten()
    .lowercase_keys(True)
    .remove_empty_strings(True)
    .remove_nulls(True)
    .remove_empty_objects(True)
    .remove_empty_arrays(True)
    .execute(messy_data))

# Result: {'username': 'Alice'}
# All empty/null values removed, keys normalized
```

### 3. Configuration File Processing

Transform between flat and nested configuration formats:

```rust
use json_tools_rs::{JSONTools, JsonOutput};

// Convert flat environment-style config to nested structure
let flat_config = r#"{
    "database.host": "localhost",
    "database.port": 5432,
    "database.name": "myapp",
    "cache.enabled": true,
    "cache.ttl": 3600,
    "cache.redis.host": "redis.local"
}"#;

let nested = JSONTools::new()
    .unflatten()
    .execute(flat_config)?;
// Result: {
//   "database": {"host": "localhost", "port": 5432, "name": "myapp"},
//   "cache": {"enabled": true, "ttl": 3600, "redis": {"host": "redis.local"}}
// }
```

### 4. Batch Data Processing

Process multiple JSON documents efficiently with type preservation:

```python
import json_tools_rs as jt

# Process batch of API responses
responses = [
    {"user": {"id": 1, "name": "Alice", "email": "alice@example.com"}},
    {"user": {"id": 2, "name": "Bob", "email": "bob@example.com"}},
    {"user": {"id": 3, "name": "Charlie", "email": "charlie@example.com"}}
]

# Flatten all responses in one call
flattened_batch = jt.JSONTools().flatten().execute(responses)
# Result: [
#   {'user.id': 1, 'user.name': 'Alice', 'user.email': 'alice@example.com'},
#   {'user.id': 2, 'user.name': 'Bob', 'user.email': 'bob@example.com'},
#   {'user.id': 3, 'user.name': 'Charlie', 'user.email': 'charlie@example.com'}
# ]
```

### 5. Multi-Source Data Aggregation

Aggregate data from multiple sources with key collision handling:

```python
import json_tools_rs as jt

# Data from different sources with overlapping keys
user_data = {"name": "John", "source": "database"}
admin_data = {"name": "Jane", "source": "ldap"}
guest_data = {"name": "Guest", "source": "default"}

# Combine with collision handling
combined = jt.JSONTools().flatten().handle_key_collision(True).execute([
    user_data, admin_data, guest_data
])

# With collision handling, duplicate keys become arrays
# Result: [
#   {'name': 'John', 'source': 'database'},
#   {'name': 'Jane', 'source': 'ldap'},
#   {'name': 'Guest', 'source': 'default'}
# ]
```

### 6. ETL Pipeline: Extract, Transform, Load

Complete ETL workflow with data transformation:

```rust
use json_tools_rs::{JSONTools, JsonOutput};

// Extract: Raw data from source
let raw_data = r#"{
    "USER_ID": 12345,
    "USER_PROFILE": {
        "FIRST_NAME": "John",
        "LAST_NAME": "Doe",
        "EMAIL_ADDRESS": "john.doe@oldcompany.com",
        "METADATA": {"created": "", "updated": null}
    }
}"#;

// Transform: Clean and normalize
let transformed = JSONTools::new()
    .flatten()
    .lowercase_keys(true)                              // Normalize keys
    .key_replacement("user_profile.", "")              // Remove prefix
    .value_replacement("@oldcompany.com", "@newcompany.com")  // Update domain
    .remove_empty_strings(true)                        // Clean empty values
    .remove_nulls(true)                                // Remove nulls
    .execute(raw_data)?;

// Load: Result ready for database insertion
// Result: {
//   "user_id": 12345,
//   "first_name": "John",
//   "last_name": "Doe",
//   "email_address": "john.doe@newcompany.com"
// }
```

## Examples and Testing

### Running Examples

**Rust Examples:**
```bash
# Basic usage examples
cargo run --example basic_usage

# View all available examples
ls examples/
```

**Python Examples:**
```bash
# Basic usage with type preservation
python python/examples/basic_usage.py

# Advanced features and collision handling
python python/examples/examples.py
```

### Running Tests

**Rust Tests:**
```bash
# Run all Rust tests
cargo test

# Run tests with verbose output
cargo test -- --nocapture

# Run tests with Python features enabled
cargo test --features python

# Run specific test module
cargo test test_module_name
```

**Python Tests:**
```bash
# Install test dependencies
pip install pytest

# Build the Python package first
maturin develop --features python

# Run all Python tests
python -m pytest python/tests/

# Run with verbose output
python -m pytest python/tests/ -v

# Run specific test file
python -m pytest python/tests/tests.py::TestClassName
```

## Limitations and Known Issues

### Current Limitations

1. **Array Index Notation**: Arrays are flattened using numeric indices (e.g., `array.0`, `array.1`). Custom array handling is not currently supported.

2. **Separator Constraints**: The separator cannot contain characters that are valid in JSON keys without escaping. Choose separators carefully to avoid conflicts.

3. **Regex Syntax**: Only standard Rust regex syntax is supported. Some advanced regex features may not be available.

4. **Memory Usage**: For very large JSON documents (>100MB), consider processing in smaller batches to optimize memory usage.

### Workarounds

**For custom array handling:**
```rust
// Pre-process arrays before flattening if custom handling is needed
// Or post-process the flattened result to transform array indices
```

**For separator conflicts:**
```rust
// Use a separator that won't appear in your keys
JSONTools::new().flatten().separator("::").execute(json)?
```

### Reporting Issues

If you encounter a bug or have a feature request, please [open an issue](https://github.com/amaye15/JSON-Tools-rs/issues) on GitHub with:
- A minimal reproducible example
- Expected vs. actual behavior
- Your environment (Rust version, OS, etc.)

## Frequently Asked Questions (FAQ)

### General Questions

**Q: What's the difference between `.flatten()` and `.unflatten()`?**

A: `.flatten()` converts nested JSON structures into flat key-value pairs with dot-separated keys. `.unflatten()` does the reverse, converting flat key-value pairs back into nested structures.

```rust
// Flatten: {"user": {"name": "John"}} → {"user.name": "John"}
// Unflatten: {"user.name": "John"} → {"user": {"name": "John"}}
```

**Q: Can I use the same configuration methods for both flatten and unflatten?**

A: Yes! All configuration methods (filtering, transformations, etc.) work for both operations. The library applies them intelligently based on the operation mode.

**Q: What happens if I don't call `.flatten()` or `.unflatten()` before `.execute()`?**

A: You'll get a `ConfigurationError` with a helpful message telling you to set the operation mode first.

### Python-Specific Questions

**Q: What input types does the Python API support?**

A: The Python API supports:
- `str` (JSON strings)
- `dict` (Python dictionaries)
- `List[str]` (lists of JSON strings)
- `List[dict]` (lists of Python dictionaries)
- Mixed lists (preserves original types)

**Q: Does the output type always match the input type?**

A: Yes! This is a key feature. `str` input → `str` output, `dict` input → `dict` output, etc. This makes the API predictable and easy to use.

### Performance Questions

**Q: How does performance compare to other JSON libraries?**

A: JSON Tools RS is optimized for high performance with SIMD-accelerated parsing, FxHashMap, and reduced allocations. Benchmarks show 2,000+ operations/ms for basic flattening. See the [Performance](#performance) section for details.

**Q: Is it safe to use in production?**

A: Yes! The library includes comprehensive error handling, extensive test coverage, and has been optimized for both correctness and performance.

### Feature Questions

**Q: How do I handle key collisions?**

A: Use `.handle_key_collision(true)` to collect colliding values into arrays. For example, if transformations cause `user_name` and `admin_name` to both become `name`, the result will be `{"name": ["John", "Jane"]}`.

**Q: Can I use regex patterns in replacements?**

A: Yes! Both `.key_replacement()` and `.value_replacement()` support standard Rust regex syntax. The library automatically detects regex patterns and falls back to literal replacement if the pattern is invalid.

**Q: What filtering options are available?**

A: You can remove:
- Empty strings: `.remove_empty_strings(true)`
- Null values: `.remove_nulls(true)`
- Empty objects: `.remove_empty_objects(true)`
- Empty arrays: `.remove_empty_arrays(true)`

All filtering methods work for both flatten and unflatten operations.

**Q: Can I process multiple JSON documents at once?**

A: Yes! Pass a `Vec<String>` in Rust or a `List[str]` or `List[dict]` in Python. The library will process them efficiently in batch mode.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/amaye15/JSON-Tools-rs.git
   cd JSON-Tools-rs
   ```

2. **Install Rust** (latest stable)
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

3. **Install Python 3.8+** and maturin for Python bindings
   ```bash
   pip install maturin pytest
   ```

4. **Run tests** to ensure everything works
   ```bash
   # Rust tests
   cargo test

   # Python tests
   maturin develop --features python
   python -m pytest python/tests/
   ```

5. **Run benchmarks** to verify performance
   ```bash
   cargo bench
   ```

### Contribution Guidelines

- Write tests for new features
- Update documentation for API changes
- Run `cargo fmt` and `cargo clippy` before submitting
- Ensure all tests pass before creating a PR
- Add examples for significant new features

## License

This project is licensed under either of

- Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE) or http://www.apache.org/licenses/LICENSE-2.0)
- MIT License ([LICENSE-MIT](LICENSE-MIT) or http://opensource.org/licenses/MIT)

at your option.

## Changelog

### v0.4.0 (Current)
- Comprehensive README documentation update
- Enhanced API reference with detailed method descriptions
- Improved error handling documentation with examples
- Updated installation instructions
- Added contribution guidelines
- Performance optimization details and benchmarking guide

### v0.3.0
- Performance optimizations (FxHashMap, SIMD parsing, reduced allocations)
- Enhanced error messages with actionable suggestions
- Improved Python bindings stability
- Bug fixes and code quality improvements

### v0.2.0
- Updated README with comprehensive documentation
- Improved API documentation and examples
- Enhanced Python bindings documentation
- Performance optimization details
- Complete error handling documentation

### v0.1.0
- Initial release with unified JSONTools API
- Complete flattening and unflattening support
- Advanced filtering and transformation capabilities
- Key collision handling with `.handle_key_collision()`
- Python bindings with perfect type matching
- Comprehensive error handling with detailed suggestions
