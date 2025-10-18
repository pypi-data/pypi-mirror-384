use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use json_tools_rs::{JSONTools, JsonOutput};
use std::fs;
use std::path::Path;
use std::time::Duration;

/// Load all test files from the test_assets directory
fn load_test_files() -> Vec<(String, String)> {
    let test_dir = Path::new("test_assets");
    let mut files = Vec::new();
    
    if test_dir.exists() {
        for entry in fs::read_dir(test_dir).expect("Failed to read test_assets directory") {
            let entry = entry.expect("Failed to read directory entry");
            let path = entry.path();
            
            if path.extension().and_then(|s| s.to_str()) == Some("json") {
                let filename = path.file_name()
                    .and_then(|s| s.to_str())
                    .unwrap_or("unknown")
                    .to_string();
                
                let content = fs::read_to_string(&path)
                    .expect(&format!("Failed to read file: {:?}", path));
                
                files.push((filename, content));
            }
        }
    }
    
    // Sort by filename for consistent ordering
    files.sort_by(|a, b| a.0.cmp(&b.0));
    files
}

/// Benchmark basic flattening operation
fn bench_flatten_basic(c: &mut Criterion) {
    let test_files = load_test_files();
    
    let mut group = c.benchmark_group("flatten_basic");
    group.measurement_time(Duration::from_secs(10));
    
    for (filename, content) in &test_files {
        group.bench_with_input(
            BenchmarkId::new("file", filename),
            content,
            |b, json_content| {
                b.iter(|| {
                    let result = JSONTools::new()
                        .flatten()
                        .execute(black_box(json_content))
                        .expect("Flatten failed");
                    black_box(result);
                });
            },
        );
    }
    group.finish();
}

/// Benchmark flattening with all transformations applied
fn bench_flatten_comprehensive(c: &mut Criterion) {
    let test_files = load_test_files();
    
    let mut group = c.benchmark_group("flatten_comprehensive");
    group.measurement_time(Duration::from_secs(15));
    
    for (filename, content) in &test_files {
        group.bench_with_input(
            BenchmarkId::new("file", filename),
            content,
            |b, json_content| {
                b.iter(|| {
                    let result = JSONTools::new()
                        .flatten()
                        .separator(black_box("::"))
                        .lowercase_keys(true)
                        .remove_empty_strings(true)
                        .remove_nulls(true)
                        .remove_empty_objects(true)
                        .remove_empty_arrays(true)
                        .key_replacement("Count", "Cnt")
                        .key_replacement("Amount", "Amt")
                        .key_replacement("Address", "Addr")
                        .value_replacement("^$", "N/A")
                        .value_replacement("null", "NULL")
                        .handle_key_collision(true)
                        .execute(black_box(json_content))
                        .expect("Comprehensive flatten failed");
                    black_box(result);
                });
            },
        );
    }
    group.finish();
}

/// Benchmark flattening with collision avoidance
fn bench_flatten_collision_avoidance(c: &mut Criterion) {
    let test_files = load_test_files();
    
    let mut group = c.benchmark_group("flatten_collision_handling");
    group.measurement_time(Duration::from_secs(10));

    for (filename, content) in &test_files {
        group.bench_with_input(
            BenchmarkId::new("file", filename),
            content,
            |b, json_content| {
                b.iter(|| {
                    let result = JSONTools::new()
                        .flatten()
                        .separator(black_box("_"))
                        .key_replacement("(customer|transaction|billing)", "data")
                        .handle_key_collision(true)
                        .execute(black_box(json_content))
                        .expect("Collision handling flatten failed");
                    black_box(result);
                });
            },
        );
    }
    group.finish();
}

/// Benchmark roundtrip operation (flatten then unflatten)
fn bench_roundtrip_basic(c: &mut Criterion) {
    let test_files = load_test_files();
    
    let mut group = c.benchmark_group("roundtrip_basic");
    group.measurement_time(Duration::from_secs(15));
    
    for (filename, content) in &test_files {
        group.bench_with_input(
            BenchmarkId::new("file", filename),
            content,
            |b, json_content| {
                b.iter(|| {
                    // Flatten
                    let flattened = JSONTools::new()
                        .flatten()
                        .execute(black_box(json_content))
                        .expect("Flatten failed");
                    
                    let flattened_str = match flattened {
                        JsonOutput::Single(s) => s,
                        JsonOutput::Multiple(_) => panic!("Unexpected multiple output"),
                    };
                    
                    // Unflatten
                    let result = JSONTools::new()
                        .unflatten()
                        .execute(black_box(&flattened_str))
                        .expect("Unflatten failed");
                    
                    black_box(result);
                });
            },
        );
    }
    group.finish();
}

/// Benchmark roundtrip with comprehensive transformations
fn bench_roundtrip_comprehensive(c: &mut Criterion) {
    let test_files = load_test_files();
    
    let mut group = c.benchmark_group("roundtrip_comprehensive");
    group.measurement_time(Duration::from_secs(20));
    
    for (filename, content) in &test_files {
        group.bench_with_input(
            BenchmarkId::new("file", filename),
            content,
            |b, json_content| {
                b.iter(|| {
                    // Flatten with transformations
                    let flattened = JSONTools::new()
                        .flatten()
                        .separator(black_box("__"))
                        .lowercase_keys(true)
                        .remove_empty_strings(true)
                        .remove_nulls(true)
                        .key_replacement("aggregation", "agg")
                        .key_replacement("transaction", "txn")
                        .value_replacement("^0$", "zero")
                        .handle_key_collision(true)
                        .execute(black_box(json_content))
                        .expect("Comprehensive flatten failed");
                    
                    let flattened_str = match flattened {
                        JsonOutput::Single(s) => s,
                        JsonOutput::Multiple(_) => panic!("Unexpected multiple output"),
                    };
                    
                    // Unflatten with reverse transformations
                    let result = JSONTools::new()
                        .unflatten()
                        .separator(black_box("__"))
                        .key_replacement("agg", "aggregation")
                        .key_replacement("txn", "transaction")
                        .value_replacement("zero", "0")
                        .handle_key_collision(true)
                        .execute(black_box(&flattened_str))
                        .expect("Comprehensive unflatten failed");
                    
                    black_box(result);
                });
            },
        );
    }
    group.finish();
}

/// Benchmark batch processing
fn bench_batch_processing(c: &mut Criterion) {
    let test_files = load_test_files();

    if test_files.is_empty() {
        println!("No test files found, skipping batch benchmark");
        return;
    }

    // Create batch of all test files as owned strings
    let batch: Vec<String> = test_files.iter().map(|(_, content)| content.clone()).collect();

    let mut group = c.benchmark_group("batch_processing");
    group.measurement_time(Duration::from_secs(10));

    group.bench_function("flatten_batch", |b| {
        b.iter(|| {
            // Convert to Vec<&str> for the API
            let batch_refs: Vec<&str> = batch.iter().map(|s| s.as_str()).collect();
            let result = JSONTools::new()
                .flatten()
                .separator(black_box("::"))
                .lowercase_keys(true)
                .remove_empty_strings(true)
                .handle_key_collision(true)
                .execute(black_box(batch_refs))
                .expect("Batch flatten failed");
            black_box(result);
        });
    });

    group.finish();
}

/// Benchmark parallel processing with different batch sizes
fn bench_parallel_processing(c: &mut Criterion) {
    let test_files = load_test_files();

    if test_files.is_empty() {
        println!("No test files found, skipping parallel benchmark");
        return;
    }

    // Create batches of different sizes
    let batch_sizes = vec![1, 5, 10, 20, 50, 100, 500, 1000];

    for &size in &batch_sizes {
        let mut group = c.benchmark_group(format!("parallel_batch_size_{}", size));
        group.measurement_time(Duration::from_secs(10));

        // Create batch by repeating test files
        let mut batch: Vec<String> = Vec::new();
        for i in 0..size {
            let file_idx = i % test_files.len();
            batch.push(test_files[file_idx].1.clone());
        }

        // Sequential (threshold = usize::MAX to disable parallel)
        group.bench_function("sequential", |b| {
            b.iter(|| {
                let batch_refs: Vec<&str> = batch.iter().map(|s| s.as_str()).collect();
                let result = JSONTools::new()
                    .flatten()
                    .parallel_threshold(usize::MAX) // Force sequential
                    .execute(black_box(batch_refs))
                    .expect("Sequential batch failed");
                black_box(result);
            });
        });

        // Parallel (threshold = 1 to always use parallel)
        group.bench_function("parallel", |b| {
            b.iter(|| {
                let batch_refs: Vec<&str> = batch.iter().map(|s| s.as_str()).collect();
                let result = JSONTools::new()
                    .flatten()
                    .parallel_threshold(1) // Force parallel
                    .execute(black_box(batch_refs))
                    .expect("Parallel batch failed");
                black_box(result);
            });
        });

        group.finish();
    }
}

/// Benchmark type conversion feature
fn bench_type_conversion(c: &mut Criterion) {
    let mut group = c.benchmark_group("type_conversion");
    group.measurement_time(Duration::from_secs(10));

    // Test data with various string types that can be converted
    let json_with_convertible_strings = r#"{
        "user": {
            "id": "12345",
            "age": "30",
            "balance": "$1,234.56",
            "score": "98.5",
            "count": "1,000,000",
            "active": "true",
            "verified": "FALSE",
            "premium": "True",
            "ratio": "1.23e-4",
            "large": "1e6",
            "name": "John Doe",
            "email": "john@example.com",
            "code": "ABC123"
        },
        "products": [
            {
                "id": "101",
                "price": "€99.99",
                "quantity": "50",
                "available": "true",
                "name": "Widget"
            },
            {
                "id": "102",
                "price": "$1,499.00",
                "quantity": "25",
                "available": "false",
                "name": "Gadget"
            }
        ],
        "metadata": {
            "total": "1,234,567",
            "average": "456.78",
            "enabled": "TRUE"
        }
    }"#;

    // Benchmark with type conversion enabled
    group.bench_function("with_conversion", |b| {
        b.iter(|| {
            let result = JSONTools::new()
                .flatten()
                .auto_convert_types(true)
                .execute(black_box(json_with_convertible_strings))
                .expect("Type conversion flatten failed");
            black_box(result);
        });
    });

    // Benchmark without type conversion (baseline)
    group.bench_function("without_conversion", |b| {
        b.iter(|| {
            let result = JSONTools::new()
                .flatten()
                .execute(black_box(json_with_convertible_strings))
                .expect("Flatten failed");
            black_box(result);
        });
    });

    // Benchmark type conversion with comprehensive transformations
    group.bench_function("with_conversion_and_transformations", |b| {
        b.iter(|| {
            let result = JSONTools::new()
                .flatten()
                .auto_convert_types(true)
                .separator("::")
                .lowercase_keys(true)
                .remove_empty_strings(true)
                .remove_nulls(true)
                .execute(black_box(json_with_convertible_strings))
                .expect("Comprehensive with conversion failed");
            black_box(result);
        });
    });

    // Benchmark unflatten with type conversion
    let flattened_json = r#"{
        "user.id": "789",
        "user.age": "35",
        "user.balance": "$5,678.90",
        "user.active": "true",
        "user.name": "Jane Smith"
    }"#;

    group.bench_function("unflatten_with_conversion", |b| {
        b.iter(|| {
            let result = JSONTools::new()
                .unflatten()
                .auto_convert_types(true)
                .execute(black_box(flattened_json))
                .expect("Unflatten with conversion failed");
            black_box(result);
        });
    });

    group.finish();
}

/// Benchmark nested parallelism for large individual JSON documents
fn bench_nested_parallelism(c: &mut Criterion) {
    let mut group = c.benchmark_group("nested_parallelism");
    group.measurement_time(Duration::from_secs(15));

    // Create a large nested JSON document for testing
    // Structure: Large object with many keys, each containing nested arrays/objects
    let create_large_json = |num_keys: usize, array_size: usize| -> String {
        let mut json = String::from("{");
        for i in 0..num_keys {
            if i > 0 {
                json.push(',');
            }
            json.push_str(&format!(r#""key_{}": {{"nested": ["#, i));
            for j in 0..array_size {
                if j > 0 {
                    json.push(',');
                }
                json.push_str(&format!(r#"{{"id": {}, "value": "item_{}_{}"}}"#, j, i, j));
            }
            json.push_str("]}");
        }
        json.push('}');
        json
    };

    // Test different document sizes
    let test_cases = vec![
        ("small_50_keys_10_items", create_large_json(50, 10)),
        ("medium_100_keys_50_items", create_large_json(100, 50)),
        ("large_200_keys_100_items", create_large_json(200, 100)),
        ("xlarge_500_keys_200_items", create_large_json(500, 200)),
    ];

    for (name, json_content) in &test_cases {
        // Benchmark WITHOUT nested parallelism (threshold = usize::MAX)
        group.bench_with_input(
            BenchmarkId::new("sequential", name),
            json_content,
            |b, json| {
                b.iter(|| {
                    let result = JSONTools::new()
                        .flatten()
                        .nested_parallel_threshold(usize::MAX) // Disable nested parallelism
                        .execute(black_box(json))
                        .expect("Flatten failed");
                    black_box(result);
                });
            },
        );

        // Benchmark WITH nested parallelism (threshold = 50)
        group.bench_with_input(
            BenchmarkId::new("nested_parallel_50", name),
            json_content,
            |b, json| {
                b.iter(|| {
                    let result = JSONTools::new()
                        .flatten()
                        .nested_parallel_threshold(50) // Enable nested parallelism for objects/arrays > 50
                        .execute(black_box(json))
                        .expect("Flatten failed");
                    black_box(result);
                });
            },
        );

        // Benchmark WITH nested parallelism (threshold = 100)
        group.bench_with_input(
            BenchmarkId::new("nested_parallel_100", name),
            json_content,
            |b, json| {
                b.iter(|| {
                    let result = JSONTools::new()
                        .flatten()
                        .nested_parallel_threshold(100) // Enable nested parallelism for objects/arrays > 100
                        .execute(black_box(json))
                        .expect("Flatten failed");
                    black_box(result);
                });
            },
        );
    }

    group.finish();
}

criterion_group!(
    benches,
    bench_flatten_basic,
    bench_flatten_comprehensive,
    bench_flatten_collision_avoidance,
    bench_roundtrip_basic,
    bench_roundtrip_comprehensive,
    bench_batch_processing,
    bench_parallel_processing,
    bench_type_conversion,
    bench_nested_parallelism
);

criterion_main!(benches);
