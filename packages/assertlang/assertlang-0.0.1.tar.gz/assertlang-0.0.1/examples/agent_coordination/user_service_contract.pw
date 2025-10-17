// PW Contract: User Service
// This contract defines EXACTLY what both agents must do
// Any agent implementing this will have identical behavior

// Data structures
class User {
    id: int;
    name: string;
    email: string;
    created_at: string;
}

class ValidationError {
    field: string;
    message: string;
}

// Contract: Create User
// This is executable - defines exact logic, not just types
function createUser(name: string, email: string) -> User {
    @requires name_not_empty: str.length(name) >= 1
    @requires name_length_valid: str.length(name) <= 100
    @requires email_has_at: str.contains(email, "@")

    if (str.length(name) < 1) {
        let error = ValidationError {
            field: "name",
            message: "Name cannot be empty"
        };
        return error;
    }

    if (str.length(name) > 100) {
        let error = ValidationError {
            field: "name",
            message: "Name too long (max 100 chars)"
        };
        return error;
    }

    if (!str.contains(email, "@")) {
        let error = ValidationError {
            field: "email",
            message: "Invalid email format"
        };
        return error;
    }

    let id = str.length(name) + str.length(email);
    let timestamp = "2025-01-15T10:30:00Z";

    let user = User {
        id: id,
        name: name,
        email: email,
        created_at: timestamp
    };

    return user;
}

// Contract: Validate Email Format
function isValidEmail(email: string) -> bool {
    @requires email_not_empty: str.length(email) >= 1

    if (!str.contains(email, "@")) {
        return false;
    }
    if (!str.contains(email, ".")) {
        return false;
    }
    return true;
}

// Contract: Format User for Display
function formatUser(user: User) -> string {
    @requires valid_user_id: user.id > 0

    let formatted = "User #" + str.from_int(user.id) + ": " +
                    user.name + " <" + user.email + ">";
    return formatted;
}

// Main coordination function
// Both agents will execute this
function main() -> int {
    print("=== PW Contract: User Service ===");
    print("");

    // Test 1: Valid user
    print("Test 1: Creating valid user");
    let user1 = createUser("Alice Smith", "alice@example.com");
    print("Result:", formatUser(user1));
    print("");

    // Test 2: Invalid name (empty)
    print("Test 2: Invalid user (empty name)");
    let user2 = createUser("", "bob@example.com");
    print("Expected: Validation error");
    print("");

    // Test 3: Invalid email
    print("Test 3: Invalid email format");
    let valid = isValidEmail("notanemail");
    if (valid) {
        print("Email is valid");
    } else {
        print("Email is INVALID (expected)");
    }
    print("");

    print("=== Contract execution complete ===");
    return 0;
}
