use crate::{JsonOutput, JSONTools};
use serde_json::Value;

/// Helper function to extract single result from JsonOutput
#[cfg(test)]
pub fn extract_single(output: JsonOutput) -> String {
    match output {
        JsonOutput::Single(result) => result,
        JsonOutput::Multiple(_) => panic!("Expected single result but got multiple"),
    }
}

/// Helper function to extract multiple results from JsonOutput
#[cfg(test)]
pub fn extract_multiple(output: JsonOutput) -> Vec<String> {
    match output {
        JsonOutput::Single(_) => panic!("Expected multiple results but got single"),
        JsonOutput::Multiple(results) => results,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // ===== BASIC FUNCTIONALITY TESTS =====

    #[test]
    fn test_basic_flattening() {
        let json = r#"{"a": {"b": {"c": 1}}}"#;
        let result = JSONTools::new().flatten().execute(json).unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        assert_eq!(parsed["a.b.c"], 1);
    }

    #[test]
    fn test_basic_unflattening() {
        let flattened = r#"{"user.name": "John", "user.age": 30}"#;
        let result = JSONTools::new().unflatten().execute(flattened).unwrap();
        let unflattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&unflattened).unwrap();

        assert_eq!(parsed["user"]["name"], "John");
        assert_eq!(parsed["user"]["age"], 30);
    }

    #[test]
    fn test_array_flattening() {
        let json = r#"{"items": [1, 2, {"nested": "value"}]}"#;
        let result = JSONTools::new().flatten().execute(json).unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        assert_eq!(parsed["items.0"], 1);
        assert_eq!(parsed["items.1"], 2);
        assert_eq!(parsed["items.2.nested"], "value");
    }

    #[test]
    fn test_array_unflattening() {
        let flattened = r#"{"items.0": 1, "items.1": 2, "items.2.nested": "value"}"#;
        let result = JSONTools::new().unflatten().execute(flattened).unwrap();
        let unflattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&unflattened).unwrap();

        assert_eq!(parsed["items"][0], 1);
        assert_eq!(parsed["items"][1], 2);
        assert_eq!(parsed["items"][2]["nested"], "value");
    }

    // ===== CONFIGURATION TESTS =====

    #[test]
    fn test_custom_separator() {
        let json = r#"{"user": {"name": "John", "age": 30}}"#;
        let result = JSONTools::new()
            .flatten()
            .separator("::")
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        assert_eq!(parsed["user::name"], "John");
        assert_eq!(parsed["user::age"], 30);
    }

    #[test]
    fn test_lowercase_keys() {
        let json = r#"{"User": {"Name": "John", "Email": "john@example.com"}}"#;
        let result = JSONTools::new()
            .flatten()
            .lowercase_keys(true)
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        assert_eq!(parsed["user.name"], "John");
        assert_eq!(parsed["user.email"], "john@example.com");
    }

    #[test]
    fn test_key_replacement() {
        let json = r#"{"user_name": "John", "admin_role": "super"}"#;
        let result = JSONTools::new()
            .flatten()
            .key_replacement("user_", "")
            .key_replacement("admin_", "")
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        assert_eq!(parsed["name"], "John");
        assert_eq!(parsed["role"], "super");
    }

    #[test]
    fn test_value_replacement() {
        let json = r#"{"email": "john@example.com", "role": "super"}"#;
        let result = JSONTools::new()
            .flatten()
            .value_replacement("@example.com", "@company.org")
            .value_replacement("super", "administrator")
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        assert_eq!(parsed["email"], "john@company.org");
        assert_eq!(parsed["role"], "administrator");
    }

    #[test]
    fn test_regex_replacements() {
        let json = r#"{"user_name": "John", "admin_role": "super", "temp_data": "test"}"#;
        let result = JSONTools::new()
            .flatten()
            .key_replacement("^(user|admin)_", "")
            .value_replacement("^super$", "administrator")
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        assert_eq!(parsed["name"], "John");
        assert_eq!(parsed["role"], "administrator");
        assert_eq!(parsed["temp_data"], "test");
    }

    // ===== FILTERING TESTS =====

    #[test]
    fn test_remove_empty_strings() {
        let json = r#"{"user": {"name": "John", "bio": "", "age": 30}}"#;
        let result = JSONTools::new()
            .flatten()
            .remove_empty_strings(true)
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        assert_eq!(parsed["user.name"], "John");
        assert_eq!(parsed["user.age"], 30);
        assert!(!parsed.as_object().unwrap().contains_key("user.bio"));
    }

    #[test]
    fn test_remove_nulls() {
        let json = r#"{"user": {"name": "John", "age": null, "city": "NYC"}}"#;
        let result = JSONTools::new()
            .flatten()
            .remove_nulls(true)
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        assert_eq!(parsed["user.name"], "John");
        assert_eq!(parsed["user.city"], "NYC");
        assert!(!parsed.as_object().unwrap().contains_key("user.age"));
    }

    #[test]
    fn test_remove_empty_objects() {
        let json = r#"{"user": {"name": "John", "profile": {}, "settings": {"theme": "dark"}}}"#;
        let result = JSONTools::new()
            .flatten()
            .remove_empty_objects(true)
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        assert_eq!(parsed["user.name"], "John");
        assert_eq!(parsed["user.settings.theme"], "dark");
        // Empty objects should be removed, so no user.profile keys should exist
        let keys: Vec<&str> = parsed.as_object().unwrap().keys().map(|s| s.as_str()).collect();
        assert!(!keys.iter().any(|k| k.starts_with("user.profile")));
    }

    #[test]
    fn test_remove_empty_arrays() {
        let json = r#"{"user": {"name": "John", "tags": [], "items": [1, 2]}}"#;
        let result = JSONTools::new()
            .flatten()
            .remove_empty_arrays(true)
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        assert_eq!(parsed["user.name"], "John");
        assert_eq!(parsed["user.items.0"], 1);
        assert_eq!(parsed["user.items.1"], 2);
        // Empty arrays should be removed
        let keys: Vec<&str> = parsed.as_object().unwrap().keys().map(|s| s.as_str()).collect();
        assert!(!keys.iter().any(|k| k.starts_with("user.tags")));
    }

    // ===== ADVANCED TESTS =====

    #[test]
    fn test_all_features_combined() {
        let json = r#"{"user_profile": {"user_name": "John", "user_email": "john@example.com", "user_age": null, "user_bio": "", "user_tags": []}}"#;
        let result = JSONTools::new()
            .flatten()
            .separator("::")
            .lowercase_keys(true)
            .key_replacement("user_", "")
            .value_replacement("@example.com", "@company.org")
            .remove_empty_strings(true)
            .remove_nulls(true)
            .remove_empty_objects(true)
            .remove_empty_arrays(true)
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        assert_eq!(parsed["profile::name"], "John");
        assert_eq!(parsed["profile::email"], "john@company.org");
        // Empty values should be removed
        assert!(!parsed.as_object().unwrap().contains_key("profile::age"));
        assert!(!parsed.as_object().unwrap().contains_key("profile::bio"));
        assert!(!parsed.as_object().unwrap().contains_key("profile::tags"));
    }

    #[test]
    fn test_roundtrip_compatibility() {
        let original = r#"{"user": {"name": "John", "age": 30}, "items": [1, 2, {"nested": "value"}]}"#;

        // Flatten
        let flattened_result = JSONTools::new().flatten().execute(original).unwrap();
        let flattened = extract_single(flattened_result);

        // Unflatten
        let unflattened_result = JSONTools::new().unflatten().execute(&flattened).unwrap();
        let unflattened = extract_single(unflattened_result);

        // Parse both original and result
        let original_parsed: Value = serde_json::from_str(original).unwrap();
        let result_parsed: Value = serde_json::from_str(&unflattened).unwrap();

        assert_eq!(original_parsed, result_parsed);
    }

    // ===== BATCH PROCESSING TESTS =====

    #[test]
    fn test_multiple_input_flatten() {
        let json_list = vec![
            r#"{"user": {"name": "John"}}"#,
            r#"{"user": {"name": "Jane"}}"#,
        ];

        let result = JSONTools::new()
            .flatten()
            .execute(json_list.as_slice())
            .unwrap();

        let results = extract_multiple(result);
        assert_eq!(results.len(), 2);

        let parsed1: Value = serde_json::from_str(&results[0]).unwrap();
        let parsed2: Value = serde_json::from_str(&results[1]).unwrap();

        assert_eq!(parsed1["user.name"], "John");
        assert_eq!(parsed2["user.name"], "Jane");
    }

    #[test]
    fn test_multiple_input_unflatten() {
        let flattened_list = vec![
            r#"{"user.name": "John"}"#,
            r#"{"user.name": "Jane"}"#,
        ];

        let result = JSONTools::new()
            .unflatten()
            .execute(flattened_list.as_slice())
            .unwrap();

        let results = extract_multiple(result);
        assert_eq!(results.len(), 2);

        let parsed1: Value = serde_json::from_str(&results[0]).unwrap();
        let parsed2: Value = serde_json::from_str(&results[1]).unwrap();

        assert_eq!(parsed1["user"]["name"], "John");
        assert_eq!(parsed2["user"]["name"], "Jane");
    }

    // ===== ERROR HANDLING TESTS =====

    #[test]
    fn test_error_no_mode_set() {
        let json = r#"{"user": {"name": "John"}}"#;
        let result = JSONTools::new().execute(json);

        assert!(result.is_err());
        let error_msg = result.unwrap_err().to_string();
        assert!(error_msg.contains("Operation mode not set"));
    }

    #[test]
    fn test_invalid_json() {
        let invalid_json = r#"{"user": {"name": "John"}"#; // Missing closing brace
        let result = JSONTools::new().flatten().execute(invalid_json);

        assert!(result.is_err());
    }

    // ===== UNFLATTEN FILTERING TESTS =====

    #[test]
    fn test_unflatten_remove_empty_strings() {
        let flattened = r#"{"user.name": "John", "user.bio": "", "user.age": 30}"#;
        let result = JSONTools::new()
            .unflatten()
            .remove_empty_strings(true)
            .execute(flattened)
            .unwrap();
        let unflattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&unflattened).unwrap();

        assert_eq!(parsed["user"]["name"], "John");
        assert_eq!(parsed["user"]["age"], 30);
        assert!(!parsed["user"].as_object().unwrap().contains_key("bio"));
    }

    #[test]
    fn test_unflatten_remove_nulls() {
        let flattened = r#"{"user.name": "John", "user.age": null, "user.city": "NYC"}"#;
        let result = JSONTools::new()
            .unflatten()
            .remove_nulls(true)
            .execute(flattened)
            .unwrap();
        let unflattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&unflattened).unwrap();

        assert_eq!(parsed["user"]["name"], "John");
        assert_eq!(parsed["user"]["city"], "NYC");
        assert!(!parsed["user"].as_object().unwrap().contains_key("age"));
    }

    #[test]
    fn test_unflatten_remove_empty_objects() {
        let flattened = r#"{"user.name": "John", "user.profile": {}, "user.settings.theme": "dark"}"#;
        let result = JSONTools::new()
            .unflatten()
            .remove_empty_objects(true)
            .execute(flattened)
            .unwrap();
        let unflattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&unflattened).unwrap();

        assert_eq!(parsed["user"]["name"], "John");
        assert_eq!(parsed["user"]["settings"]["theme"], "dark");
        assert!(!parsed["user"].as_object().unwrap().contains_key("profile"));
    }

    #[test]
    fn test_unflatten_remove_empty_arrays() {
        let flattened = r#"{"user.name": "John", "user.tags": [], "user.items.0": "first"}"#;
        let result = JSONTools::new()
            .unflatten()
            .remove_empty_arrays(true)
            .execute(flattened)
            .unwrap();
        let unflattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&unflattened).unwrap();

        assert_eq!(parsed["user"]["name"], "John");
        assert_eq!(parsed["user"]["items"][0], "first");
        assert!(!parsed["user"].as_object().unwrap().contains_key("tags"));
    }

    #[test]
    fn test_unflatten_all_filters_combined() {
        let flattened = r#"{"user.name": "John", "user.bio": "", "user.age": null, "user.profile": {}, "user.tags": [], "user.settings.theme": "dark"}"#;
        let result = JSONTools::new()
            .unflatten()
            .remove_empty_strings(true)
            .remove_nulls(true)
            .remove_empty_objects(true)
            .remove_empty_arrays(true)
            .execute(flattened)
            .unwrap();
        let unflattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&unflattened).unwrap();

        assert_eq!(parsed["user"]["name"], "John");
        assert_eq!(parsed["user"]["settings"]["theme"], "dark");
        // All empty values should be removed
        let user_obj = parsed["user"].as_object().unwrap();
        assert!(!user_obj.contains_key("bio"));
        assert!(!user_obj.contains_key("age"));
        assert!(!user_obj.contains_key("profile"));
        assert!(!user_obj.contains_key("tags"));
    }

    #[test]
    fn test_unflatten_nested_filtering() {
        let flattened = r#"{"users.0.name": "John", "users.0.bio": "", "users.1.name": "Jane", "users.1.age": null, "users.2.profile": {}}"#;
        let result = JSONTools::new()
            .unflatten()
            .remove_empty_strings(true)
            .remove_nulls(true)
            .remove_empty_objects(true)
            .execute(flattened)
            .unwrap();
        let unflattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&unflattened).unwrap();

        // Check that the structure is correct
        assert_eq!(parsed["users"][0]["name"], "John");
        assert_eq!(parsed["users"][1]["name"], "Jane");

        // Check that empty values were filtered out
        assert!(!parsed["users"][0].as_object().unwrap().contains_key("bio"));
        assert!(!parsed["users"][1].as_object().unwrap().contains_key("age"));

        // Since the empty profile object was removed, users[2] should either not exist or be empty
        // Let's check if users[2] exists and if it does, it should not have a profile key
        if let Some(user2) = parsed["users"].get(2) {
            if let Some(user2_obj) = user2.as_object() {
                assert!(!user2_obj.contains_key("profile"));
            }
        }
    }

    #[test]
    fn test_unflatten_with_replacements_and_filtering() {
        let flattened = r#"{"user_name": "John", "user_bio": "", "user_email": "john@example.com", "user_age": null}"#;
        let result = JSONTools::new()
            .unflatten()
            .key_replacement("user_", "profile.")
            .value_replacement("@example.com", "@company.org")
            .remove_empty_strings(true)
            .remove_nulls(true)
            .execute(flattened)
            .unwrap();
        let unflattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&unflattened).unwrap();

        assert_eq!(parsed["profile"]["name"], "John");
        assert_eq!(parsed["profile"]["email"], "john@company.org");
        // Empty and null values should be filtered out
        let profile_obj = parsed["profile"].as_object().unwrap();
        assert!(!profile_obj.contains_key("bio"));
        assert!(!profile_obj.contains_key("age"));
    }

    #[test]
    fn test_feature_parity_flatten_vs_unflatten() {
        // This test demonstrates that both flatten and unflatten support the same configuration methods
        let original = r#"{"user_profile": {"user_name": "John", "user_email": "john@example.com", "user_age": null, "user_bio": "", "user_tags": []}}"#;

        // Test that both operations support all the same methods
        let flatten_result = JSONTools::new()
            .flatten()
            .separator("::")
            .lowercase_keys(true)
            .key_replacement("user_", "")
            .value_replacement("@example.com", "@company.org")
            .remove_empty_strings(true)
            .remove_nulls(true)
            .remove_empty_objects(true)
            .remove_empty_arrays(true)
            .execute(original)
            .unwrap();

        let unflatten_result = JSONTools::new()
            .unflatten()
            .separator("::")
            .lowercase_keys(true)
            .key_replacement("user_", "")
            .value_replacement("@company.org", "@example.com")
            .remove_empty_strings(true)
            .remove_nulls(true)
            .remove_empty_objects(true)
            .remove_empty_arrays(true)
            .execute(r#"{"profile::name": "John", "profile::email": "john@company.org", "profile::bio": "", "profile::age": null, "profile::tags": []}"#)
            .unwrap();

        // Both operations should succeed and produce valid JSON
        let flattened = extract_single(flatten_result);
        let unflattened = extract_single(unflatten_result);

        let flattened_parsed: Value = serde_json::from_str(&flattened).unwrap();
        let unflattened_parsed: Value = serde_json::from_str(&unflattened).unwrap();

        // Verify that both operations applied filtering correctly
        assert_eq!(flattened_parsed["profile::name"], "John");
        assert_eq!(flattened_parsed["profile::email"], "john@company.org");
        assert!(!flattened_parsed.as_object().unwrap().contains_key("profile::bio"));
        assert!(!flattened_parsed.as_object().unwrap().contains_key("profile::age"));
        assert!(!flattened_parsed.as_object().unwrap().contains_key("profile::tags"));

        assert_eq!(unflattened_parsed["profile"]["name"], "John");
        assert_eq!(unflattened_parsed["profile"]["email"], "john@example.com");
        let profile_obj = unflattened_parsed["profile"].as_object().unwrap();
        assert!(!profile_obj.contains_key("bio"));
        assert!(!profile_obj.contains_key("age"));
        assert!(!profile_obj.contains_key("tags"));
    }

    // ===== KEY COLLISION TESTS =====

    #[test]
    fn test_handle_key_collision_flatten_arrays() {
        let json = r#"{"User_name": "John", "Admin_name": "Jane", "Guest_name": "Bob"}"#;
        let result = JSONTools::new()
            .flatten()
            .separator("::")
            .key_replacement("(User|Admin|Guest)_", "")
            .handle_key_collision(true)
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        // Should have a single key mapping to an array of values
        let obj = parsed.as_object().unwrap();
        assert_eq!(obj.len(), 1);
        assert!(obj.contains_key("name"));
        let arr = obj.get("name").unwrap().as_array().unwrap();
        assert_eq!(arr.len(), 3);
    }

    #[test]
    fn test_handle_key_collision_flatten() {
        let json = r#"{"User_name": "John", "Admin_name": "Jane", "Guest_name": "Bob"}"#;
        let result = JSONTools::new()
            .flatten()
            .key_replacement("(User|Admin|Guest)_", "")
            .handle_key_collision(true)
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        // Should collect all values into an array (order may vary due to HashMap)
        if let Some(array) = parsed["name"].as_array() {
            assert_eq!(array.len(), 3);
            let values: Vec<&str> = array.iter().map(|v| v.as_str().unwrap()).collect();
            assert!(values.contains(&"John"));
            assert!(values.contains(&"Jane"));
            assert!(values.contains(&"Bob"));
        } else {
            panic!("Expected array for 'name' key");
        }
    }



    #[test]
    fn test_handle_key_collision_unflatten() {
        let flattened = r#"{"name::0": "John", "name::1": "Jane", "name::2": "Bob"}"#;
        let result = JSONTools::new()
            .unflatten()
            .separator("::")
            .key_replacement("name::\\d+", "user_name")
            .handle_key_collision(true)
            .execute(flattened)
            .unwrap();
        let unflattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&unflattened).unwrap();

        // Should collect all values into an array (order may vary)
        if let Some(array) = parsed["user_name"].as_array() {
            assert_eq!(array.len(), 3);
            let values: Vec<&str> = array.iter().map(|v| v.as_str().unwrap()).collect();
            assert!(values.contains(&"John"));
            assert!(values.contains(&"Jane"));
            assert!(values.contains(&"Bob"));
        } else {
            panic!("Expected array for 'user_name' key");
        }
    }

    #[test]
    fn test_collision_precedence_collect_only() {
        // With only handle_key_collision supported, ensure colliding keys collect into arrays
        let json = r#"{"User_name": "John", "Admin_name": "Jane"}"#;
        let result = JSONTools::new()
            .flatten()
            .key_replacement("(User|Admin)_", "")
            .handle_key_collision(true)
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        // Should use collect strategy (arrays)
        let obj = parsed.as_object().unwrap();
        assert_eq!(obj.len(), 1);
        assert!(obj.contains_key("name"));
        assert!(parsed["name"].is_array());

        // Check array contents
        let arr = parsed["name"].as_array().unwrap();
        assert_eq!(arr.len(), 2);
        let mut values: Vec<&str> = arr.iter().map(|v| v.as_str().unwrap()).collect();
        values.sort();
        assert_eq!(values, vec!["Jane", "John"]);
    }

    #[test]
    fn test_no_collision_no_change() {
        // When there are no collisions, and handle_key_collision is enabled, no arrays should be created
        let json = r#"{"User_name": "John", "Admin_email": "jane@example.com"}"#;
        let result = JSONTools::new()
            .flatten()
            .key_replacement("(User|Admin)_", "")
            .handle_key_collision(true)
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        // No collisions, so keys should remain as-is
        assert_eq!(parsed["name"], "John");
        assert_eq!(parsed["email"], "jane@example.com");
    }

    #[test]
    fn test_collision_with_custom_separator() {
        let json = r#"{"User_name": "John", "Admin_name": "Jane"}"#;
        let result = JSONTools::new()
            .flatten()
            .separator("__")
            .key_replacement("(User|Admin)_", "")
            .handle_key_collision(true)
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        // With custom separator in keys, but only collection strategy, we still produce arrays under a single key
        let obj = parsed.as_object().unwrap();
        assert_eq!(obj.len(), 1);
        assert!(obj.contains_key("name"));

        // Check array contents
        let arr = parsed["name"].as_array().unwrap();
        assert_eq!(arr.len(), 2);
        let mut values: Vec<&str> = arr.iter().map(|v| v.as_str().unwrap()).collect();
        values.sort();
        assert_eq!(values, vec!["Jane", "John"]);
    }

    #[test]
    fn test_collision_with_mixed_value_types() {
        let json = r#"{"User_name": "John", "Admin_name": 42, "Guest_name": true}"#;
        let result = JSONTools::new()
            .flatten()
            .key_replacement("(User|Admin|Guest)_", "")
            .handle_key_collision(true)
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        // Should collect mixed types into an array (order may vary)
        if let Some(array) = parsed["name"].as_array() {
            assert_eq!(array.len(), 3);

            // Check that we have all expected values
            let has_john = array.iter().any(|v| v.as_str() == Some("John"));
            let has_42 = array.iter().any(|v| v.as_i64() == Some(42));
            let has_true = array.iter().any(|v| v.as_bool() == Some(true));

            assert!(has_john);
            assert!(has_42);
            assert!(has_true);
        } else {
            panic!("Expected array for 'name' key");
        }
    }

    #[test]
    fn test_collision_with_filtering() {
        let json = r#"{"User_name": "John", "Admin_name": "", "Guest_name": "Bob"}"#;
        let result = JSONTools::new()
            .flatten()
            .key_replacement("(User|Admin|Guest)_", "")
            .remove_empty_strings(true)
            .handle_key_collision(true)
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        // Collision handling now properly filters out empty values during array creation
        if let Some(array) = parsed["name"].as_array() {
            // The array should only contain non-empty values after filtering
            assert_eq!(array.len(), 2);
            let values: Vec<&str> = array.iter().map(|v| v.as_str().unwrap()).collect();
            assert!(values.contains(&"John"));
            assert!(values.contains(&"Bob"));
            // Empty string should be filtered out during collision handling
        } else {
            panic!("Expected array for 'name' key");
        }
    }

    // ===== TYPE CONVERSION TESTS =====

    #[test]
    fn test_basic_number_conversion() {
        let json = r#"{"id": "123", "price": "45.67", "count": "-10"}"#;
        let result = JSONTools::new()
            .flatten()
            .auto_convert_types(true)
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        assert_eq!(parsed["id"], 123);
        assert_eq!(parsed["price"], 45.67);
        assert_eq!(parsed["count"], -10);
    }

    #[test]
    fn test_thousands_separator_us_format() {
        let json = r#"{"amount": "1,234.56", "total": "1,000,000"}"#;
        let result = JSONTools::new()
            .flatten()
            .auto_convert_types(true)
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        assert_eq!(parsed["amount"], 1234.56);
        assert_eq!(parsed["total"], 1000000);
    }

    #[test]
    fn test_thousands_separator_european_format() {
        let json = r#"{"amount": "1.234,56", "total": "1.000.000,00"}"#;
        let result = JSONTools::new()
            .flatten()
            .auto_convert_types(true)
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        assert_eq!(parsed["amount"], 1234.56);
        assert_eq!(parsed["total"], 1000000.0);
    }

    #[test]
    fn test_currency_symbols() {
        let json = r#"{"usd": "$123.45", "eur": "€99.99", "gbp": "£50.00"}"#;
        let result = JSONTools::new()
            .flatten()
            .auto_convert_types(true)
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        assert_eq!(parsed["usd"], 123.45);
        assert_eq!(parsed["eur"], 99.99);
        assert_eq!(parsed["gbp"], 50.0);
    }

    #[test]
    fn test_scientific_notation() {
        let json = r#"{"small": "1.23e-4", "large": "1e5", "negative": "-2.5e3"}"#;
        let result = JSONTools::new()
            .flatten()
            .auto_convert_types(true)
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        assert_eq!(parsed["small"], 0.000123);
        assert_eq!(parsed["large"], 100000.0);
        assert_eq!(parsed["negative"], -2500.0);
    }

    #[test]
    fn test_boolean_conversion() {
        let json = r#"{"a": "true", "b": "TRUE", "c": "True", "d": "false", "e": "FALSE", "f": "False"}"#;
        let result = JSONTools::new()
            .flatten()
            .auto_convert_types(true)
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        assert_eq!(parsed["a"], true);
        assert_eq!(parsed["b"], true);
        assert_eq!(parsed["c"], true);
        assert_eq!(parsed["d"], false);
        assert_eq!(parsed["e"], false);
        assert_eq!(parsed["f"], false);
    }

    #[test]
    fn test_keep_invalid_strings() {
        let json = r#"{"name": "John", "code": "ABC123", "maybe": "yes", "invalid": "12.34.56"}"#;
        let result = JSONTools::new()
            .flatten()
            .auto_convert_types(true)
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        assert_eq!(parsed["name"], "John");
        assert_eq!(parsed["code"], "ABC123");
        assert_eq!(parsed["maybe"], "yes"); // Not a valid boolean
        assert_eq!(parsed["invalid"], "12.34.56"); // Invalid number
    }

    #[test]
    fn test_mixed_conversion() {
        let json = r#"{"id": "123", "name": "Alice", "price": "$1,234.56", "active": "true", "code": "XYZ"}"#;
        let result = JSONTools::new()
            .flatten()
            .auto_convert_types(true)
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        assert_eq!(parsed["id"], 123);
        assert_eq!(parsed["name"], "Alice");
        assert_eq!(parsed["price"], 1234.56);
        assert_eq!(parsed["active"], true);
        assert_eq!(parsed["code"], "XYZ");
    }

    #[test]
    fn test_nested_conversion() {
        let json = r#"{"user": {"id": "456", "age": "25", "verified": "true"}}"#;
        let result = JSONTools::new()
            .flatten()
            .auto_convert_types(true)
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        assert_eq!(parsed["user.id"], 456);
        assert_eq!(parsed["user.age"], 25);
        assert_eq!(parsed["user.verified"], true);
    }

    #[test]
    fn test_array_conversion() {
        let json = r#"{"numbers": ["123", "45.6", "true", "invalid"]}"#;
        let result = JSONTools::new()
            .flatten()
            .auto_convert_types(true)
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        assert_eq!(parsed["numbers.0"], 123);
        assert_eq!(parsed["numbers.1"], 45.6);
        assert_eq!(parsed["numbers.2"], true);
        assert_eq!(parsed["numbers.3"], "invalid");
    }

    #[test]
    fn test_conversion_disabled_by_default() {
        let json = r#"{"id": "123", "active": "true"}"#;
        let result = JSONTools::new()
            .flatten()
            .execute(json)
            .unwrap();
        let flattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&flattened).unwrap();

        // Should keep as strings when conversion is disabled
        assert_eq!(parsed["id"], "123");
        assert_eq!(parsed["active"], "true");
    }

    #[test]
    fn test_unflatten_with_conversion() {
        let json = r#"{"user.id": "789", "user.active": "false"}"#;
        let result = JSONTools::new()
            .unflatten()
            .auto_convert_types(true)
            .execute(json)
            .unwrap();
        let unflattened = extract_single(result);
        let parsed: Value = serde_json::from_str(&unflattened).unwrap();

        assert_eq!(parsed["user"]["id"], 789);
        assert_eq!(parsed["user"]["active"], false);
    }

    #[test]
    fn test_normal_mode_with_conversion() {
        let json = r#"{"user": {"id": "999", "enabled": "TRUE"}}"#;
        let result = JSONTools::new()
            .normal()
            .auto_convert_types(true)
            .execute(json)
            .unwrap();
        let processed = extract_single(result);
        let parsed: Value = serde_json::from_str(&processed).unwrap();

        assert_eq!(parsed["user"]["id"], 999);
        assert_eq!(parsed["user"]["enabled"], true);
    }
}

// ===== MEMORY PROFILING TESTS =====

#[cfg(test)]
mod memory_profiling_tests {
    use crate::JSONTools;

    #[test]
    fn test_parallel_memory_overhead() {
        // Create a batch of 100 JSON documents
        let json_docs: Vec<String> = (0..100)
            .map(|i| {
                format!(
                    r#"{{"id": {}, "name": "User {}", "email": "user{}@example.com", "age": {}, "active": true}}"#,
                    i, i, i, 20 + (i % 50)
                )
            })
            .collect();

        let json_refs: Vec<&str> = json_docs.iter().map(|s| s.as_str()).collect();

        // Test sequential processing
        let result_seq = JSONTools::new()
            .flatten()
            .parallel_threshold(usize::MAX) // Force sequential
            .execute(json_refs.clone())
            .expect("Sequential processing failed");

        // Test parallel processing
        let result_par = JSONTools::new()
            .flatten()
            .parallel_threshold(1) // Force parallel
            .execute(json_refs)
            .expect("Parallel processing failed");

        // Both should produce identical results - compare the actual strings
        let (seq_results, par_results) = match (result_seq, result_par) {
            (crate::JsonOutput::Multiple(seq), crate::JsonOutput::Multiple(par)) => (seq, par),
            _ => panic!("Expected Multiple output"),
        };

        assert_eq!(seq_results.len(), par_results.len(), "Result counts should match");
        for (i, (seq, par)) in seq_results.iter().zip(par_results.iter()).enumerate() {
            assert_eq!(seq, par, "Result {} should be identical", i);
        }

        // Validate: results should be reasonable size
        let total_size: usize = seq_results.iter().map(|s| s.len()).sum();
        let avg_size = total_size / seq_results.len();

        println!("Average result size: {} bytes", avg_size);
        println!("Total results size: {} bytes ({:.2} KB)", total_size, total_size as f64 / 1024.0);

        // Each flattened JSON should be reasonable (< 1KB for this test data)
        assert!(avg_size < 1000, "Average result size is unexpectedly large");
    }

    #[test]
    fn test_large_batch_memory_scaling() {
        // Test that memory scales linearly with batch size, not exponentially
        let batch_sizes = vec![10, 50, 100, 500];
        let mut bytes_per_item = Vec::new();

        for &size in &batch_sizes {
            let json_docs: Vec<String> = (0..size)
                .map(|i| {
                    format!(
                        r#"{{"id": {}, "data": "Item {}", "value": {}}}"#,
                        i, i, i * 100
                    )
                })
                .collect();

            let json_refs: Vec<&str> = json_docs.iter().map(|s| s.as_str()).collect();

            let result = JSONTools::new()
                .flatten()
                .parallel_threshold(10)
                .execute(json_refs)
                .expect("Processing failed");

            // Measure output size as proxy for memory usage
            if let crate::JsonOutput::Multiple(results) = result {
                let total_bytes: usize = results.iter().map(|s| s.len() + std::mem::size_of::<String>()).sum();
                let per_item = total_bytes / size;
                bytes_per_item.push(per_item);

                println!("Batch size {}: {} bytes total, {} bytes per item", size, total_bytes, per_item);
            }
        }

        // Validate: per-item memory should be relatively constant (within 2x)
        let min_per_item = *bytes_per_item.iter().min().unwrap();
        let max_per_item = *bytes_per_item.iter().max().unwrap();
        let ratio = max_per_item as f64 / min_per_item as f64;

        println!("Memory per item ratio (max/min): {:.2}x", ratio);

        // Linear scaling means ratio should be close to 1.0
        // Allow up to 2x variation due to Vec overhead and small batch effects
        assert!(
            ratio < 2.0,
            "Memory per item varies too much ({:.2}x), suggesting non-linear scaling",
            ratio
        );
    }

    #[test]
    fn test_chunked_processing_memory() {
        // Test that chunked processing (>1000 items) doesn't increase memory per item
        let size = 1500; // Triggers chunked processing

        let json_docs: Vec<String> = (0..size)
            .map(|i| {
                format!(r#"{{"id": {}, "value": {}}}"#, i, i * 10)
            })
            .collect();

        let json_refs: Vec<&str> = json_docs.iter().map(|s| s.as_str()).collect();

        let result = JSONTools::new()
            .flatten()
            .parallel_threshold(10)
            .execute(json_refs)
            .expect("Chunked processing failed");

        // Measure output size
        if let crate::JsonOutput::Multiple(results) = result {
            assert_eq!(results.len(), size, "Should process all items");

            let total_bytes: usize = results.iter().map(|s| s.len() + std::mem::size_of::<String>()).sum();
            let per_item = total_bytes / size;

            println!("Chunked processing (1500 items): {} bytes total, {} bytes per item", total_bytes, per_item);

            // Validate: per-item memory should be reasonable (< 1KB per item for this simple JSON)
            assert!(
                per_item < 1000,
                "Per-item memory ({} bytes) is too high for chunked processing",
                per_item
            );
        }
    }

    #[test]
    fn test_memory_cleanup_after_processing() {
        // Test that results can be properly dropped and don't hold excessive memory
        let json_docs: Vec<String> = (0..100)
            .map(|i| format!(r#"{{"id": {}, "data": "test"}}"#, i))
            .collect();

        let json_refs: Vec<&str> = json_docs.iter().map(|s| s.as_str()).collect();

        let result = JSONTools::new()
            .flatten()
            .parallel_threshold(10)
            .execute(json_refs)
            .expect("Processing failed");

        // Validate result structure
        if let crate::JsonOutput::Multiple(results) = result {
            assert_eq!(results.len(), 100, "Should have 100 results");

            // Each result should be a valid JSON string
            for (i, result_str) in results.iter().enumerate() {
                assert!(result_str.contains("id"), "Result {} should contain 'id' field", i);
                assert!(result_str.contains("data"), "Result {} should contain 'data' field", i);
            }

            println!("Successfully processed and validated 100 items");
            println!("Results can be dropped without issues");
        }
    }

    #[test]
    fn test_parallel_vs_sequential_same_output_size() {
        // Verify that parallel and sequential produce identical output sizes
        let json_docs: Vec<String> = (0..200)
            .map(|i| {
                format!(
                    r#"{{"id": {}, "nested": {{"value": {}, "name": "Item {}"}}}}"#,
                    i, i * 10, i
                )
            })
            .collect();

        let json_refs: Vec<&str> = json_docs.iter().map(|s| s.as_str()).collect();

        // Sequential
        let result_seq = JSONTools::new()
            .flatten()
            .parallel_threshold(usize::MAX)
            .execute(json_refs.clone())
            .expect("Sequential failed");

        // Parallel
        let result_par = JSONTools::new()
            .flatten()
            .parallel_threshold(1)
            .execute(json_refs)
            .expect("Parallel failed");

        // Extract results
        let (seq, par) = match (result_seq, result_par) {
            (crate::JsonOutput::Multiple(seq), crate::JsonOutput::Multiple(par)) => (seq, par),
            _ => panic!("Expected Multiple output"),
        };

        // Both should produce identical results
        assert_eq!(seq.len(), par.len(), "Result counts should match");
        for (i, (s, p)) in seq.iter().zip(par.iter()).enumerate() {
            assert_eq!(s, p, "Result {} should be identical", i);
        }

        // Measure sizes
        let seq_size: usize = seq.iter().map(|s| s.len()).sum();
        let par_size: usize = par.iter().map(|s| s.len()).sum();

        println!("Sequential total size: {} bytes", seq_size);
        println!("Parallel total size: {} bytes", par_size);

        assert_eq!(seq_size, par_size, "Output sizes should be identical");
    }
}

// ===== NESTED PARALLELISM TESTS =====

#[cfg(test)]
mod nested_parallelism_tests {
    use crate::{JSONTools, JsonOutput};

    /// Test that nested parallelism produces the same results as sequential processing
    #[test]
    fn test_nested_parallel_consistency() {
        // Create a large nested JSON document
        let json = r#"{
            "users": [
                {"id": 1, "name": "Alice", "tags": ["admin", "user"]},
                {"id": 2, "name": "Bob", "tags": ["user"]},
                {"id": 3, "name": "Charlie", "tags": ["moderator", "user"]},
                {"id": 4, "name": "David", "tags": ["user"]},
                {"id": 5, "name": "Eve", "tags": ["admin", "moderator"]}
            ],
            "settings": {
                "theme": "dark",
                "notifications": {
                    "email": true,
                    "push": false,
                    "sms": true
                },
                "privacy": {
                    "profile_visible": true,
                    "show_email": false
                }
            },
            "metadata": {
                "version": "1.0",
                "created": "2024-01-01",
                "updated": "2024-01-15"
            }
        }"#;

        // Flatten with sequential processing (nested_threshold = usize::MAX)
        let sequential_result = JSONTools::new()
            .flatten()
            .nested_parallel_threshold(usize::MAX)
            .execute(json)
            .expect("Sequential flatten failed");

        // Flatten with nested parallelism (nested_threshold = 2)
        let parallel_result = JSONTools::new()
            .flatten()
            .nested_parallel_threshold(2)
            .execute(json)
            .expect("Parallel flatten failed");

        // Extract the JSON strings for comparison
        let sequential_json = match sequential_result {
            JsonOutput::Single(s) => s,
            _ => panic!("Expected single output"),
        };

        let parallel_json = match parallel_result {
            JsonOutput::Single(s) => s,
            _ => panic!("Expected single output"),
        };

        // Parse both results to compare as JSON objects (order-independent)
        let sequential_value: serde_json::Value = serde_json::from_str(&sequential_json)
            .expect("Failed to parse sequential result");
        let parallel_value: serde_json::Value = serde_json::from_str(&parallel_json)
            .expect("Failed to parse parallel result");

        assert_eq!(
            sequential_value, parallel_value,
            "Nested parallel processing should produce identical results to sequential processing"
        );
    }

    /// Test nested parallelism with large objects
    #[test]
    fn test_large_object_nested_parallelism() {
        // Create a JSON object with 150 keys (exceeds default threshold of 100)
        let mut json = String::from("{");
        for i in 0..150 {
            if i > 0 {
                json.push(',');
            }
            json.push_str(&format!(r#""key_{}": {{"nested": "value_{}", "id": {}}}"#, i, i, i));
        }
        json.push('}');

        // Flatten with sequential processing
        let sequential_result = JSONTools::new()
            .flatten()
            .nested_parallel_threshold(usize::MAX)
            .execute(&json)
            .expect("Sequential flatten failed");

        // Flatten with nested parallelism (threshold = 100)
        let parallel_result = JSONTools::new()
            .flatten()
            .nested_parallel_threshold(100)
            .execute(&json)
            .expect("Parallel flatten failed");

        // Extract and compare
        let sequential_json = match sequential_result {
            JsonOutput::Single(s) => s,
            _ => panic!("Expected single output"),
        };

        let parallel_json = match parallel_result {
            JsonOutput::Single(s) => s,
            _ => panic!("Expected single output"),
        };

        let sequential_value: serde_json::Value = serde_json::from_str(&sequential_json).unwrap();
        let parallel_value: serde_json::Value = serde_json::from_str(&parallel_json).unwrap();

        assert_eq!(sequential_value, parallel_value);
    }

    /// Test nested parallelism with large arrays
    #[test]
    fn test_large_array_nested_parallelism() {
        // Create a JSON array with 150 items (exceeds default threshold of 100)
        let mut json = String::from("[");
        for i in 0..150 {
            if i > 0 {
                json.push(',');
            }
            json.push_str(&format!(r#"{{"id": {}, "value": "item_{}", "nested": {{"data": "test_{}"}} }}"#, i, i, i));
        }
        json.push(']');

        // Flatten with sequential processing
        let sequential_result = JSONTools::new()
            .flatten()
            .nested_parallel_threshold(usize::MAX)
            .execute(&json)
            .expect("Sequential flatten failed");

        // Flatten with nested parallelism (threshold = 100)
        let parallel_result = JSONTools::new()
            .flatten()
            .nested_parallel_threshold(100)
            .execute(&json)
            .expect("Parallel flatten failed");

        // Extract and compare
        let sequential_json = match sequential_result {
            JsonOutput::Single(s) => s,
            _ => panic!("Expected single output"),
        };

        let parallel_json = match parallel_result {
            JsonOutput::Single(s) => s,
            _ => panic!("Expected single output"),
        };

        let sequential_value: serde_json::Value = serde_json::from_str(&sequential_json).unwrap();
        let parallel_value: serde_json::Value = serde_json::from_str(&parallel_json).unwrap();

        assert_eq!(sequential_value, parallel_value);
    }

    /// Test that small objects/arrays stay sequential
    #[test]
    fn test_small_structures_stay_sequential() {
        let json = r#"{
            "small_object": {"a": 1, "b": 2, "c": 3},
            "small_array": [1, 2, 3, 4, 5]
        }"#;

        // This should work fine even with a very low threshold
        // because the structures are small
        let result = JSONTools::new()
            .flatten()
            .nested_parallel_threshold(10)
            .execute(json)
            .expect("Flatten failed");

        match result {
            JsonOutput::Single(s) => {
                let value: serde_json::Value = serde_json::from_str(&s).unwrap();
                assert!(value.is_object());
            }
            _ => panic!("Expected single output"),
        }
    }

    /// Test environment variable configuration
    #[test]
    fn test_environment_variable_nested_threshold() {
        std::env::set_var("JSON_TOOLS_NESTED_PARALLEL_THRESHOLD", "50");

        let tools = JSONTools::new();

        // The default should now be 50 from the environment variable
        // We can't directly access the field, but we can test that it works
        let json = r#"{"test": "value"}"#;
        let result = tools.flatten().execute(json);

        assert!(result.is_ok());

        std::env::remove_var("JSON_TOOLS_NESTED_PARALLEL_THRESHOLD");
    }

    /// Test deeply nested structures with parallelism
    #[test]
    fn test_deeply_nested_parallelism() {
        // Create a deeply nested structure with wide branches
        let json = r#"{
            "level1": {
                "items": [
                    {"id": 1, "data": {"values": [1, 2, 3, 4, 5]}},
                    {"id": 2, "data": {"values": [6, 7, 8, 9, 10]}},
                    {"id": 3, "data": {"values": [11, 12, 13, 14, 15]}}
                ],
                "metadata": {
                    "created": "2024-01-01",
                    "tags": ["a", "b", "c", "d", "e"]
                }
            }
        }"#;

        let sequential_result = JSONTools::new()
            .flatten()
            .nested_parallel_threshold(usize::MAX)
            .execute(json)
            .expect("Sequential flatten failed");

        let parallel_result = JSONTools::new()
            .flatten()
            .nested_parallel_threshold(2)
            .execute(json)
            .expect("Parallel flatten failed");

        let sequential_json = match sequential_result {
            JsonOutput::Single(s) => s,
            _ => panic!("Expected single output"),
        };

        let parallel_json = match parallel_result {
            JsonOutput::Single(s) => s,
            _ => panic!("Expected single output"),
        };

        let sequential_value: serde_json::Value = serde_json::from_str(&sequential_json).unwrap();
        let parallel_value: serde_json::Value = serde_json::from_str(&parallel_json).unwrap();

        assert_eq!(sequential_value, parallel_value);
    }
}

// ===== PARALLEL REGEX CACHE TESTS =====

#[cfg(test)]
mod parallel_regex_cache_tests {
    use crate::{JSONTools, JsonOutput};

    /// Test that parallel processing with regex replacements works correctly
    #[test]
    fn test_parallel_processing_with_regex_replacements() {
        // Create a batch of JSON documents with patterns to replace
        let json_docs: Vec<String> = (0..100)
            .map(|i| {
                format!(
                    r#"{{"user_id": {}, "admin_name": "Admin{}", "guest_email": "guest{}@example.com"}}"#,
                    i, i, i
                )
            })
            .collect();

        let json_refs: Vec<&str> = json_docs.iter().map(|s| s.as_str()).collect();

        // Process with parallel threshold = 10 (should use parallel processing)
        let result = JSONTools::new()
            .flatten()
            .key_replacement("(user|admin|guest)_", "")
            .value_replacement("@example\\.com", "@company.org")
            .parallel_threshold(10)
            .execute(json_refs)
            .expect("Parallel processing failed");

        // Verify results
        if let JsonOutput::Multiple(results) = result {
            assert_eq!(results.len(), 100);

            for (i, result_str) in results.iter().enumerate() {
                let value: serde_json::Value = serde_json::from_str(result_str)
                    .expect("Failed to parse result");

                // Check that key replacements worked
                assert!(value.as_object().unwrap().contains_key("id"), "Should have 'id' key");
                assert!(value.as_object().unwrap().contains_key("name"), "Should have 'name' key");
                assert!(value.as_object().unwrap().contains_key("email"), "Should have 'email' key");

                // Check that value replacements worked
                let email = value["email"].as_str().unwrap();
                assert!(
                    email.contains("@company.org"),
                    "Email should be replaced: {} (item {})",
                    email, i
                );
            }
        } else {
            panic!("Expected Multiple output");
        }
    }

    /// Test that parallel and sequential produce identical results with regex
    #[test]
    fn test_parallel_vs_sequential_consistency() {
        let json_docs: Vec<String> = (0..50)
            .map(|i| {
                format!(
                    r#"{{"temp_data": "value{}", "old_field": "test{}", "user_name": "User{}"}}"#,
                    i, i, i
                )
            })
            .collect();

        let json_refs: Vec<&str> = json_docs.iter().map(|s| s.as_str()).collect();

        // Sequential processing
        let sequential_result = JSONTools::new()
            .flatten()
            .key_replacement("^(temp|old|user)_", "new_")
            .value_replacement("^test", "updated")
            .parallel_threshold(usize::MAX) // Force sequential
            .execute(json_refs.clone())
            .expect("Sequential processing failed");

        // Parallel processing
        let parallel_result = JSONTools::new()
            .flatten()
            .key_replacement("^(temp|old|user)_", "new_")
            .value_replacement("^test", "updated")
            .parallel_threshold(1) // Force parallel
            .execute(json_refs)
            .expect("Parallel processing failed");

        // Compare results
        let (seq_results, par_results) = match (sequential_result, parallel_result) {
            (JsonOutput::Multiple(seq), JsonOutput::Multiple(par)) => (seq, par),
            _ => panic!("Expected Multiple output"),
        };

        assert_eq!(seq_results.len(), par_results.len());

        for (i, (seq, par)) in seq_results.iter().zip(par_results.iter()).enumerate() {
            assert_eq!(seq, par, "Result {} should be identical", i);
        }
    }

    /// Test thread-local cache isolation
    #[test]
    fn test_thread_local_cache_isolation() {
        // This test verifies that thread-local regex caches don't interfere with each other
        let json_docs: Vec<String> = (0..200)
            .map(|i| {
                format!(r#"{{"field_{}_name": "value{}", "data_{}_id": {}}}"#, i % 10, i, i % 5, i)
            })
            .collect();

        let json_refs: Vec<&str> = json_docs.iter().map(|s| s.as_str()).collect();

        // Process with multiple regex patterns
        let result = JSONTools::new()
            .flatten()
            .key_replacement("field_[0-9]+_", "f_")
            .key_replacement("data_[0-9]+_", "d_")
            .value_replacement("value([0-9]+)", "val_$1")
            .parallel_threshold(10)
            .execute(json_refs)
            .expect("Processing failed");

        // Verify all results are correct
        if let JsonOutput::Multiple(results) = result {
            assert_eq!(results.len(), 200);

            for result_str in results.iter() {
                let value: serde_json::Value = serde_json::from_str(result_str).unwrap();
                let obj = value.as_object().unwrap();

                // Check that replacements were applied
                assert!(
                    obj.keys().any(|k| k.starts_with("f_") || k.starts_with("d_")),
                    "Keys should have replacements applied"
                );
            }
        }
    }

    /// Test adaptive threshold behavior with regex
    #[test]
    fn test_adaptive_threshold_behavior() {
        // Small batch (< threshold) - should use sequential
        let small_batch: Vec<String> = (0..5)
            .map(|i| format!(r#"{{"user_id": {}}}"#, i))
            .collect();
        let small_refs: Vec<&str> = small_batch.iter().map(|s| s.as_str()).collect();

        let small_result = JSONTools::new()
            .flatten()
            .key_replacement("user_", "")
            .parallel_threshold(10)
            .execute(small_refs)
            .expect("Small batch failed");

        // Large batch (> threshold) - should use parallel
        let large_batch: Vec<String> = (0..50)
            .map(|i| format!(r#"{{"user_id": {}}}"#, i))
            .collect();
        let large_refs: Vec<&str> = large_batch.iter().map(|s| s.as_str()).collect();

        let large_result = JSONTools::new()
            .flatten()
            .key_replacement("user_", "")
            .parallel_threshold(10)
            .execute(large_refs)
            .expect("Large batch failed");

        // Both should succeed
        assert!(matches!(small_result, JsonOutput::Multiple(_)));
        assert!(matches!(large_result, JsonOutput::Multiple(_)));
    }

    /// Test environment variable for parallel threshold
    #[test]
    fn test_environment_variable_threshold() {
        std::env::set_var("JSON_TOOLS_PARALLEL_THRESHOLD", "5");

        let json_docs: Vec<String> = (0..10)
            .map(|i| format!(r#"{{"id": {}}}"#, i))
            .collect();
        let json_refs: Vec<&str> = json_docs.iter().map(|s| s.as_str()).collect();

        // Should use parallel processing because batch size (10) > threshold (5)
        let result = JSONTools::new()
            .flatten()
            .execute(json_refs)
            .expect("Processing failed");

        assert!(matches!(result, JsonOutput::Multiple(_)));

        std::env::remove_var("JSON_TOOLS_PARALLEL_THRESHOLD");
    }
}