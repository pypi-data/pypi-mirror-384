# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2025-10-17

### Added
- **Parallel Processing Configuration**
  - `.parallel_threshold(usize)` - Configure minimum batch size for parallel processing (default: 10)
  - `.num_threads(Option<usize>)` - Configure number of threads for parallel processing (default: Rayon default)
  - `.nested_parallel_threshold(usize)` - Configure threshold for nested parallel processing within individual JSON documents (default: 100)
  - Environment variable support: `JSON_TOOLS_PARALLEL_THRESHOLD` and `JSON_TOOLS_NESTED_PARALLEL_THRESHOLD`
- **Enhanced Testing**
  - Added 671 new lines of comprehensive tests
  - Improved test coverage for parallel processing scenarios
  - Additional edge case testing for type conversion and filtering

### Performance Improvements
- **Optimized HashMap Initialization**
  - Pre-allocated FxHashMap with known capacity for better performance
  - Reduced memory allocations during regex caching
  - Improved thread-local regex cache initialization
  - Enhanced key deduplication cache performance

### Changed
- Improved parallel processing defaults for better out-of-the-box performance
- Enhanced documentation for parallel processing configuration
- Updated benchmarks to include parallel processing scenarios

## [0.6.0] - 2025-10-13

### Added
- **Python Bindings Performance Optimizations**
  - GIL (Global Interpreter Lock) release during compute-intensive operations
  - Enables true multi-threading in Python applications
  - `#[inline]` attributes on all builder methods for better optimization

### Performance Improvements
- **Python Bindings**: 5-13% performance improvement across most operations
  - Roundtrip operations: +13.2% (75K → 85K ops/sec)
  - Array flattening: +9.6% (8.3K → 9.1K ops/sec)
  - Batch string processing: +8.5% (54.7K → 59.3K ops/sec)
  - Large data processing: +7.7% (666 → 717 ops/sec)
  - Batch operations: +4.8% to +5.6% across all sizes
  - Complex configurations: +5.0% (90K → 95K ops/sec)
- **Multi-threading**: Python applications can now run other threads while Rust code executes
- **Rust Core**: Cumulative 32-60% improvement from previous optimizations (v0.4.0-0.5.0)
  - FxHashMap for 15-30% faster string key operations
  - SIMD JSON parsing optimizations
  - Reduced memory allocations (~50% fewer string clones)
  - Pre-allocated collections
  - Optimized hash lookups with entry() API
  - #[inline(always)] on hot path functions
  - #[cold] on error paths

### Changed
- Python bindings now release GIL during all execute operations
- All Python builder methods now have inline optimization hints

### Technical Details
- Added `py.allow_threads()` around compute operations in:
  - `execute()` method (3 locations: string, dict, list)
  - `execute_to_output()` method (3 locations: string, dict, list)
- Added `#[inline]` to 13 builder methods in Python bindings

## [0.5.0] - 2025-10-12

### Added
- **Rust Core Performance Optimizations (Phase 3)**
  - #[inline(always)] on 6 critical hot path functions
  - #[cold] + #[inline(never)] on 4 error path functions
  - Optimized compiler hints for better code generation

### Performance Improvements
- **Rust Core**: Additional 2-5% improvement on top of Phase 1-2 optimizations
  - Batch processing: ~2% faster
  - Roundtrip operations: ~2-5% faster
  - Total cumulative improvement: 32-60% from baseline

## [0.4.0] - 2025-10-11

### Added
- **Rust Core Performance Optimizations (Phase 1-2)**
  - Enhanced Cargo.toml with LTO "fat" for better cross-crate inlining
  - CPU-specific optimizations with target-cpu=native
  - FxHashMap replacing standard HashMap for 15-30% faster string operations
  - Reduced string clones in key transformations (~50% reduction)
  - Optimized SIMD JSON parsing for reduced memory allocations
  - Pre-allocated Vec and Map capacity
  - Entry API for faster hash lookups
  - Optimized struct field ordering for better memory alignment

### Performance Improvements
- **Rust Core**: 30-55% performance improvement across all operations
  - Basic flattening: 2,000+ ops/ms
  - Advanced configuration: 1,300+ ops/ms
  - Regex replacements: 1,800+ ops/ms
  - Batch processing: 1,900+ ops/ms
  - Roundtrip operations: 1,000+ cycles/ms

## [0.3.0] - 2025-10-10

### Added
- **Automatic Type Conversion** feature
  - Convert strings to numbers and booleans with `.auto_convert_types(true)`
  - Handles currency symbols ($, €, £, ¥)
  - Supports thousands separators (1,234.56 and 1.234,56)
  - Scientific notation support (1.23e10)
  - Boolean conversion (true/false, TRUE/FALSE, True/False)
  - Opportunistic conversion - keeps original value if conversion fails
- **Python Bindings** with full feature parity
  - Type preservation: str→str, dict→dict, list[str]→list[str], list[dict]→list[dict]
  - Batch processing support
  - All Rust features available in Python
  - Comprehensive test suite (107 tests)

### Changed
- Unified API with `JSONTools` as single entry point
- Builder pattern for all operations
- Consistent API across Rust and Python

## [0.2.0] - 2025-10-09

### Added
- **Collision Handling** with `.handle_key_collision(true)`
  - Collects duplicate keys into arrays
  - Filtering applied during collision resolution
- **Comprehensive Filtering** for both flatten and unflatten
  - `.remove_empty_strings(true)`
  - `.remove_nulls(true)`
  - `.remove_empty_objects(true)`
  - `.remove_empty_arrays(true)`
- **Advanced Replacements**
  - Literal and regex-based key/value replacements
  - Standard Rust regex syntax
  - Automatic fallback to literal matching for invalid regex
- **Batch Processing**
  - Process single JSON or Vec<String>
  - Efficient batch operations

### Changed
- Improved error handling with `JsonToolsError` enum
- Better error messages with suggestions

## [0.1.0] - 2025-10-08

### Added
- Initial release
- **Basic Flattening** - Convert nested JSON to flat structure
- **Basic Unflattening** - Reconstruct nested JSON from flat structure
- **Roundtrip Support** - Perfect fidelity for flatten→unflatten
- **Custom Separators** - Configure key separator (default: ".")
- **Lowercase Keys** - Convert all keys to lowercase
- **SIMD JSON Parsing** - Hardware-accelerated parsing via simd-json
- **Comprehensive Error Handling** - Detailed error messages
- **Extensive Test Coverage** - 48 unit tests + 17 doc tests

### Technical Details
- Rust 2021 edition
- SIMD-accelerated JSON parsing
- Zero-copy optimizations where possible
- Comprehensive documentation

---

## Version History Summary

| Version | Release Date | Key Features | Performance |
|---------|--------------|--------------|-------------|
| **0.7.0** | 2025-10-17 | Parallel processing config, optimizations | HashMap improvements |
| **0.6.0** | 2025-10-13 | Python GIL release, inline hints | +5-13% Python |
| **0.5.0** | 2025-10-12 | Rust inline optimizations | +2-5% Rust |
| **0.4.0** | 2025-10-11 | FxHashMap, SIMD, allocations | +30-55% Rust |
| **0.3.0** | 2025-10-10 | Type conversion, Python bindings | Feature release |
| **0.2.0** | 2025-10-09 | Collision handling, filtering | Feature release |
| **0.1.0** | 2025-10-08 | Initial release | Baseline |

---

## Migration Guide

### Upgrading from 0.6.0 to 0.7.0

**No breaking changes!** This is a feature enhancement and performance improvement release.

**What's New**:
- New parallel processing configuration methods
- Better control over thread usage and parallelism thresholds
- Optimized HashMap initialization for better performance
- Enhanced test coverage

**Action Required**: None - just update your dependency version. Optionally, you can configure parallel processing settings for your specific workload.

### Upgrading from 0.5.0 to 0.6.0

**No breaking changes!** This is a pure performance improvement release.

**What's New**:
- Python applications automatically benefit from GIL release
- Better multi-threading support in Python
- 5-13% faster Python operations

**Action Required**: None - just update your dependency version

### Upgrading from 0.4.0 to 0.5.0

**No breaking changes!** Pure performance improvements.

### Upgrading from 0.3.0 to 0.4.0

**No breaking changes!** Pure performance improvements.

### Upgrading from 0.2.0 to 0.3.0

**API Changes**:
- Removed separate `JsonFlattener` and `JsonUnflattener` APIs
- Use unified `JSONTools` API instead
- All functionality preserved, just cleaner API

**Migration Example**:
```rust
// Old (0.2.0)
use json_tools_rs::JsonFlattener;
let result = JsonFlattener::new()
    .flatten()
    .execute(json)?;

// New (0.3.0+)
use json_tools_rs::JSONTools;
let result = JSONTools::new()
    .flatten()
    .execute(json)?;
```

---

## Links

- [Repository](https://github.com/amaye15/JSON-Tools-rs)
- [Crates.io](https://crates.io/crates/json-tools-rs)
- [Documentation](https://docs.rs/json-tools-rs)
- [Issues](https://github.com/amaye15/JSON-Tools-rs/issues)

