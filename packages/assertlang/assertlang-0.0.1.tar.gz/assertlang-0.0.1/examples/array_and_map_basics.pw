// Array and Map Basics - Demonstrates .length and safe map access

// Array length example
function count_items(items: array) -> int {
    return items.length;  // Works in all 5 languages
}

// Array iteration with length
function sum_array(numbers: array) -> int {
    let total = 0;
    let i = 0;
    while (i < numbers.length) {
        total = total + numbers[i];
        i = i + 1;
    }
    return total;
}

// Safe map key checking
function has_user(users: map, username: string) -> bool {
    // Safe: returns null/None for missing keys
    if (users[username] != null) {
        return true;
    }
    return false;
}

// Safe map operations
function add_user(users: map, username: string, email: string) -> bool {
    // Check if user already exists (safe)
    if (users[username] != null) {
        return false;  // User exists
    }
    
    // Add new user
    users[username] = email;
    return true;
}

// Map with string literals (also safe)
function get_config(config: map) -> string {
    // Safe: returns null if key missing
    if (config["api_key"] != null) {
        return config["api_key"];
    }
    return "default_key";
}

// Array bounds checking
function safe_get(arr: array, index: int) -> int {
    if (index >= 0 && index < arr.length) {
        return arr[index];
    }
    return 0;
}
