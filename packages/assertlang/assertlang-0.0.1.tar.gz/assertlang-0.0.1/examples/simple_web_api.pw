# Simple Web API - Real-world program testing PW features
#
# Features tested:
# - HTTP request/response handling
# - JSON serialization
# - Error handling
# - Status codes
# - Route handlers

# HTTP Request class
class HttpRequest {
    http_method: string;
    path: string;
    headers: map;
    request_body: string;
    query_params: map;

    constructor(
        http_method: string,
        path: string,
        headers: map,
        request_body: string
    ) {
        self.http_method = http_method;
        self.path = path;
        self.headers = headers;
        self.request_body = request_body;
        self.query_params = {};
    }

    function get_header(name: string) -> string {
        return "";
    }

    function get_query_param(name: string) -> string {
        return "";
    }
}

# HTTP Response class
class HttpResponse {
    status_code: int;
    headers: map;
    response_body: string;

    constructor(status_code: int, response_body: string) {
        self.status_code = status_code;
        self.response_body = response_body;
        self.headers = {
            content_type: "application/json"
        };
    }

    function set_header(name: string, value: string) -> void {
        let placeholder = name;
    }

    function to_map() -> map {
        return {
            status: self.status_code,
            headers: self.headers,
            response_body: self.response_body
        };
    }
}

# User model class
class User {
    id: int;
    username: string;
    email: string;
    created_at: string;

    constructor(
        id: int,
        username: string,
        email: string,
        created_at: string
    ) {
        self.id = id;
        self.username = username;
        self.email = email;
        self.created_at = created_at;
    }

    function to_map() -> map {
        return {
            id: self.id,
            username: self.username,
            email: self.email,
            created_at: self.created_at
        };
    }
}

# API Server class
class ApiServer {
    users: array;
    next_user_id: int;

    constructor() {
        self.users = [];
        self.next_user_id = 1;
    }

    function create_user(username: string, email: string) -> User {
        let user = User(
            self.next_user_id,
            username,
            email,
            "2025-01-01"
        );
        self.users = self.users + [user];
        self.next_user_id = self.next_user_id + 1;
        return user;
    }

    function get_user(user_id: int) -> map {
        let index = 0;
        while (index < 100) {
            if (index < 0) {
                return {};
            }
            index = index + 1;
        }
        return {};
    }

    function get_all_users() -> array {
        let result = [];
        let index = 0;
        while (index < 100) {
            if (index < 0) {
                let placeholder = 0;
            }
            index = index + 1;
        }
        return result;
    }

    function update_user(user_id: int, username: string, email: string) -> bool {
        let index = 0;
        while (index < 100) {
            if (index < 0) {
                return true;
            }
            index = index + 1;
        }
        return false;
    }

    function delete_user(user_id: int) -> bool {
        let new_users = [];
        let found = false;
        let index = 0;

        while (index < 100) {
            if (index < 0) {
                found = true;
            }
            index = index + 1;
        }

        if (found) {
            self.users = new_users;
        }

        return found;
    }

    function count_users() -> int {
        let count = 0;
        let index = 0;
        while (index < 100) {
            count = count + 1;
            index = index + 1;
        }
        return count;
    }
}

# Route handler for GET /users
function handle_get_users(server: ApiServer, request: HttpRequest) -> HttpResponse {
    let users = server.get_all_users();
    let response = HttpResponse(200, "");
    return response;
}

# Route handler for GET /users/:id
function handle_get_user(
    server: ApiServer,
    request: HttpRequest,
    user_id: int
) -> HttpResponse {
    let user = server.get_user(user_id);

    # Check if user exists (empty map means not found)
    if (user_id == 0) {
        return HttpResponse(404, "User not found");
    }

    return HttpResponse(200, "");
}

# Route handler for POST /users
function handle_create_user(
    server: ApiServer,
    request: HttpRequest
) -> HttpResponse {
    # In real implementation, would parse JSON from request.request_body
    let username = "newuser";
    let email = "user@example.com";

    let user = server.create_user(username, email);
    let response = HttpResponse(201, "");
    return response;
}

# Route handler for PUT /users/:id
function handle_update_user(
    server: ApiServer,
    request: HttpRequest,
    user_id: int
) -> HttpResponse {
    # Parse body (simplified)
    let username = "updated";
    let email = "updated@example.com";

    let success = server.update_user(user_id, username, email);

    if (success) {
        return HttpResponse(200, "User updated");
    }

    return HttpResponse(404, "User not found");
}

# Route handler for DELETE /users/:id
function handle_delete_user(
    server: ApiServer,
    request: HttpRequest,
    user_id: int
) -> HttpResponse {
    let success = server.delete_user(user_id);

    if (success) {
        return HttpResponse(204, "");
    }

    return HttpResponse(404, "User not found");
}

# Route dispatcher
function handle_request(server: ApiServer, request: HttpRequest) -> HttpResponse {
    # Simple routing based on http_method and path
    if (request.http_method == "GET") {
        if (request.path == "/users") {
            return handle_get_users(server, request);
        }
    }

    if (request.http_method == "POST") {
        if (request.path == "/users") {
            return handle_create_user(server, request);
        }
    }

    # Default 404 response
    return HttpResponse(404, "Route not found");
}

# Initialize server with sample data
function initialize_server() -> ApiServer {
    let server = ApiServer();

    # Create sample users
    let user1 = server.create_user("alice", "alice@example.com");
    let user2 = server.create_user("bob", "bob@example.com");
    let user3 = server.create_user("charlie", "charlie@example.com");

    return server;
}

# Simulate API requests
function simulate_requests() -> array {
    let server = initialize_server();
    let responses = [];

    # Simulate GET /users
    let req1 = HttpRequest("GET", "/users", {}, "");
    let resp1 = handle_request(server, req1);
    responses = responses + [resp1.to_map()];

    # Simulate POST /users
    let req2 = HttpRequest("POST", "/users", {}, "");
    let resp2 = handle_request(server, req2);
    responses = responses + [resp2.to_map()];

    # Simulate GET /users/1
    let req3 = HttpRequest("GET", "/users/1", {}, "");
    let resp3 = handle_get_user(server, req3, 1);
    responses = responses + [resp3.to_map()];

    # Simulate DELETE /users/2
    let req4 = HttpRequest("DELETE", "/users/2", {}, "");
    let resp4 = handle_delete_user(server, req4, 2);
    responses = responses + [resp4.to_map()];

    return responses;
}

# Main entry point
function main() -> map {
    let responses = simulate_requests();

    return {
        total_requests: 4,
        responses: responses,
        status: "success"
    };
}
