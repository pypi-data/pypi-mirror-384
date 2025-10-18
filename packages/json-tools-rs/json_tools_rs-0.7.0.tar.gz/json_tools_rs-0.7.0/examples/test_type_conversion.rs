use json_tools_rs::{JSONTools, JsonOutput};
use serde_json::Value;

fn main() {
    println!("Testing Automatic Type Conversion Feature\n");
    println!("==========================================\n");

    // Test 1: Basic number conversion
    println!("Test 1: Basic Number Conversion");
    let json = r#"{"id": "123", "price": "45.67", "count": "-10"}"#;
    let result = JSONTools::new()
        .flatten()
        .auto_convert_types(true)
        .execute(json)
        .unwrap();
    
    if let JsonOutput::Single(output) = result {
        println!("Input:  {}", json);
        println!("Output: {}\n", output);
        
        let parsed: Value = serde_json::from_str(&output).unwrap();
        assert_eq!(parsed["id"], 123);
        assert_eq!(parsed["price"], 45.67);
        assert_eq!(parsed["count"], -10);
    }

    // Test 2: Currency and thousands separators
    println!("Test 2: Currency and Thousands Separators");
    let json = r#"{"usd": "$1,234.56", "eur": "€999.99", "large": "1,000,000"}"#;
    let result = JSONTools::new()
        .flatten()
        .auto_convert_types(true)
        .execute(json)
        .unwrap();
    
    if let JsonOutput::Single(output) = result {
        println!("Input:  {}", json);
        println!("Output: {}\n", output);
        
        let parsed: Value = serde_json::from_str(&output).unwrap();
        assert_eq!(parsed["usd"], 1234.56);
        assert_eq!(parsed["eur"], 999.99);
        assert_eq!(parsed["large"], 1000000);
    }

    // Test 3: Boolean conversion
    println!("Test 3: Boolean Conversion");
    let json = r#"{"a": "true", "b": "FALSE", "c": "True"}"#;
    let result = JSONTools::new()
        .flatten()
        .auto_convert_types(true)
        .execute(json)
        .unwrap();
    
    if let JsonOutput::Single(output) = result {
        println!("Input:  {}", json);
        println!("Output: {}\n", output);
        
        let parsed: Value = serde_json::from_str(&output).unwrap();
        assert_eq!(parsed["a"], true);
        assert_eq!(parsed["b"], false);
        assert_eq!(parsed["c"], true);
    }

    // Test 4: Mixed conversion with invalid strings
    println!("Test 4: Mixed Conversion (keeps invalid strings)");
    let json = r#"{"id": "123", "name": "Alice", "active": "true", "code": "ABC"}"#;
    let result = JSONTools::new()
        .flatten()
        .auto_convert_types(true)
        .execute(json)
        .unwrap();
    
    if let JsonOutput::Single(output) = result {
        println!("Input:  {}", json);
        println!("Output: {}\n", output);
        
        let parsed: Value = serde_json::from_str(&output).unwrap();
        assert_eq!(parsed["id"], 123);
        assert_eq!(parsed["name"], "Alice");
        assert_eq!(parsed["active"], true);
        assert_eq!(parsed["code"], "ABC");
    }

    // Test 5: Nested structures
    println!("Test 5: Nested Structures");
    let json = r#"{"user": {"id": "456", "age": "25", "verified": "true"}}"#;
    let result = JSONTools::new()
        .flatten()
        .auto_convert_types(true)
        .execute(json)
        .unwrap();
    
    if let JsonOutput::Single(output) = result {
        println!("Input:  {}", json);
        println!("Output: {}\n", output);
        
        let parsed: Value = serde_json::from_str(&output).unwrap();
        assert_eq!(parsed["user.id"], 456);
        assert_eq!(parsed["user.age"], 25);
        assert_eq!(parsed["user.verified"], true);
    }

    // Test 6: Conversion disabled (default)
    println!("Test 6: Conversion Disabled (default behavior)");
    let json = r#"{"id": "123", "active": "true"}"#;
    let result = JSONTools::new()
        .flatten()
        .execute(json)
        .unwrap();
    
    if let JsonOutput::Single(output) = result {
        println!("Input:  {}", json);
        println!("Output: {}\n", output);
        
        let parsed: Value = serde_json::from_str(&output).unwrap();
        assert_eq!(parsed["id"], "123");  // Still a string
        assert_eq!(parsed["active"], "true");  // Still a string
    }

    // Test 7: Scientific notation
    println!("Test 7: Scientific Notation");
    let json = r#"{"small": "1.23e-4", "large": "1e5"}"#;
    let result = JSONTools::new()
        .flatten()
        .auto_convert_types(true)
        .execute(json)
        .unwrap();
    
    if let JsonOutput::Single(output) = result {
        println!("Input:  {}", json);
        println!("Output: {}\n", output);
        
        let parsed: Value = serde_json::from_str(&output).unwrap();
        assert_eq!(parsed["small"], 0.000123);
        assert_eq!(parsed["large"], 100000.0);
    }

    println!("==========================================");
    println!("✅ All tests passed!");
}

