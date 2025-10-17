# FastAPI Endpoints with Contracts

**Build type-safe FastAPI endpoints with automatic validation using AssertLang contracts.**

---

## Problem

FastAPI endpoints need validation for:
- Request body parameters
- Query parameters
- Path parameters
- Response data
- Business logic rules

**Basic FastAPI:**
```python
@app.post("/users")
def create_user(name: str, email: str, age: int):
    # Pydantic validates types, but not business rules
    # No validation for: age > 0, email format, name length, etc.
    user = User(name=name, email=email, age=age)
    return user
```

---

## Solution

Combine Pydantic (type validation) + PW contracts (business rules):

```promptware
function create_user(name: String, email: String, age: Int) -> User
  requires:
    len(name) > 0
    len(name) <= 100
    "@" in email
    age >= 18
    age <= 150
  ensures:
    result.name == name
    result.email == email
    result.age == age
  do
    return User(name=name, email=email, age=age)
  end
end
```

---

## Basic FastAPI Integration

### Generate Models and Contracts

**Step 1: Define in AssertLang**
```promptware
# api_types.al
type User:
  id: String
  name: String
  email: String
  age: Int
end

type CreateUserRequest:
  name: String
  email: String
  age: Int
end
```

**Step 2: Generate Pydantic models**
```bash
asl build api_types.al --lang pydantic -o models.py
```

**Step 3: Write contracts**
```promptware
# user_service.al
function create_user_validated(req: CreateUserRequest) -> Result<User, String>
  requires:
    len(req.name) > 0
    len(req.name) <= 100
    "@" in req.email
    req.age >= 18
  do
    # Generate unique ID
    let user_id = generate_id()

    return Ok(User(
      id=user_id,
      name=req.name,
      email=req.email,
      age=req.age
    ))
  end
end
```

**Step 4: Generate Python contracts**
```bash
asl build user_service.al --lang python -o user_service.py
```

**Step 5: FastAPI endpoint**
```python
# main.py
from fastapi import FastAPI, HTTPException
from models import User, CreateUserRequest
from user_service import create_user_validated, Ok, Err

app = FastAPI()

@app.post("/users", response_model=User)
def create_user_endpoint(req: CreateUserRequest):
    """
    Create a new user.

    - Pydantic validates types (name: str, age: int)
    - PW contract validates business rules (age >= 18, email format)
    """
    result = create_user_validated(req)

    if isinstance(result, Err):
        raise HTTPException(
            status_code=400,
            detail=f"Validation failed: {result.error}"
        )

    return result.value
```

---

## CRUD Operations

### Complete User API

```promptware
# user_crud.al
type User:
  id: String
  name: String
  email: String
  age: Int
end

# Create
function create_user(name: String, email: String, age: Int) -> Result<User, String>
  requires:
    len(name) > 0
    "@" in email
    age >= 18
  do
    let id = generate_id()
    return Ok(User(id=id, name=name, email=email, age=age))
  end
end

# Read
function get_user(user_id: String) -> Result<User, String>
  requires:
    len(user_id) > 0
  do
    # Fetch from database
    let user = db_find_user(user_id)

    if user is Some(u):
      return Ok(u)
    else:
      return Err("User not found")
    end
  end
end

# Update
function update_user(
    user_id: String,
    name: Option<String>,
    email: Option<String>,
    age: Option<Int>
) -> Result<User, String>
  requires:
    len(user_id) > 0
  do
    let user_result = get_user(user_id)

    if user_result is Err(msg):
      return Err(msg)
    end

    if user_result is Ok(user):
      # Update fields if provided
      let new_name = if name is Some(n): n else: user.name
      let new_email = if email is Some(e): e else: user.email
      let new_age = if age is Some(a): a else: user.age

      # Validate updated fields
      if len(new_name) == 0:
        return Err("Name cannot be empty")
      end

      if new_age < 18:
        return Err("Age must be >= 18")
      end

      return Ok(User(
        id=user_id,
        name=new_name,
        email=new_email,
        age=new_age
      ))
    end

    return Err("Update failed")
  end
end

# Delete
function delete_user(user_id: String) -> Result<Bool, String>
  requires:
    len(user_id) > 0
  do
    let user_result = get_user(user_id)

    if user_result is Err(msg):
      return Err(msg)
    end

    # Delete from database
    db_delete_user(user_id)
    return Ok(true)
  end
end
```

### FastAPI Endpoints

```python
# main.py
from fastapi import FastAPI, HTTPException
from typing import Optional
from pydantic import BaseModel
from user_crud import *

app = FastAPI()

# Request models
class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None

# CREATE
@app.post("/users", response_model=User, status_code=201)
def create_user_endpoint(name: str, email: str, age: int):
    result = create_user(name, email, age)

    if isinstance(result, Err):
        raise HTTPException(status_code=400, detail=result.error)

    return result.value

# READ
@app.get("/users/{user_id}", response_model=User)
def get_user_endpoint(user_id: str):
    result = get_user(user_id)

    if isinstance(result, Err):
        raise HTTPException(status_code=404, detail=result.error)

    return result.value

# UPDATE
@app.put("/users/{user_id}", response_model=User)
def update_user_endpoint(user_id: str, req: UpdateUserRequest):
    # Convert Optional[T] to Option<T>
    name = Some(req.name) if req.name else None_()
    email = Some(req.email) if req.email else None_()
    age = Some(req.age) if req.age else None_()

    result = update_user(user_id, name, email, age)

    if isinstance(result, Err):
        raise HTTPException(status_code=400, detail=result.error)

    return result.value

# DELETE
@app.delete("/users/{user_id}")
def delete_user_endpoint(user_id: str):
    result = delete_user(user_id)

    if isinstance(result, Err):
        raise HTTPException(status_code=404, detail=result.error)

    return {"message": "User deleted", "success": result.value}

# LIST
@app.get("/users", response_model=list[User])
def list_users_endpoint(skip: int = 0, limit: int = 100):
    # List with pagination
    if limit > 1000:
        raise HTTPException(status_code=400, detail="Limit too high (max 1000)")

    users = db_list_users(skip, limit)
    return users
```

---

## Query Parameter Validation

### Search with Validation

```promptware
function search_users(
    query: String,
    min_age: Int,
    max_age: Int,
    limit: Int
) -> Result<List<User>, String>
  requires:
    len(query) >= 3
    min_age >= 0
    max_age >= min_age
    limit > 0
    limit <= 1000
  ensures:
    len(result) <= limit if result is Ok
  do
    # Search database
    let users = db_search_users(query, min_age, max_age, limit)
    return Ok(users)
  end
end
```

**FastAPI:**
```python
@app.get("/users/search", response_model=list[User])
def search_users_endpoint(
    q: str,
    min_age: int = 0,
    max_age: int = 150,
    limit: int = 100
):
    result = search_users(q, min_age, max_age, limit)

    if isinstance(result, Err):
        raise HTTPException(status_code=400, detail=result.error)

    return result.value
```

---

## Nested Resources

### Posts for Users

```promptware
type Post:
  id: String
  user_id: String
  title: String
  content: String
  created_at: String
end

function create_post(
    user_id: String,
    title: String,
    content: String
) -> Result<Post, String>
  requires:
    len(user_id) > 0
    len(title) > 0
    len(title) <= 200
    len(content) > 0
    len(content) <= 10000
  do
    # Verify user exists
    let user_result = get_user(user_id)

    if user_result is Err(msg):
      return Err("User not found: " + user_id)
    end

    let post_id = generate_id()
    let timestamp = current_timestamp()

    return Ok(Post(
      id=post_id,
      user_id=user_id,
      title=title,
      content=content,
      created_at=timestamp
    ))
  end
end

function get_user_posts(user_id: String) -> Result<List<Post>, String>
  requires:
    len(user_id) > 0
  do
    # Verify user exists
    let user_result = get_user(user_id)

    if user_result is Err(msg):
      return Err(msg)
    end

    let posts = db_get_posts_by_user(user_id)
    return Ok(posts)
  end
end
```

**FastAPI:**
```python
@app.post("/users/{user_id}/posts", response_model=Post, status_code=201)
def create_post_endpoint(user_id: str, title: str, content: str):
    result = create_post(user_id, title, content)

    if isinstance(result, Err):
        raise HTTPException(status_code=400, detail=result.error)

    return result.value

@app.get("/users/{user_id}/posts", response_model=list[Post])
def get_user_posts_endpoint(user_id: str):
    result = get_user_posts(user_id)

    if isinstance(result, Err):
        raise HTTPException(status_code=404, detail=result.error)

    return result.value
```

---

## Error Handling

### Custom Error Responses

```python
# errors.py
from fastapi import HTTPException
from typing import Dict, Any

class ValidationError(HTTPException):
    def __init__(self, detail: str, field: str = None):
        super().__init__(
            status_code=400,
            detail={
                "error": "validation_error",
                "message": detail,
                "field": field
            }
        )

class NotFoundError(HTTPException):
    def __init__(self, resource: str, id: str):
        super().__init__(
            status_code=404,
            detail={
                "error": "not_found",
                "message": f"{resource} not found",
                "id": id
            }
        )

# Usage in endpoint
@app.post("/users")
def create_user_endpoint(req: CreateUserRequest):
    result = create_user_validated(req)

    if isinstance(result, Err):
        raise ValidationError(result.error, field="request")

    return result.value
```

---

## Testing FastAPI with Contracts

```python
# test_api.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_user_valid():
    response = client.post("/users", json={
        "name": "John Doe",
        "email": "john@example.com",
        "age": 25
    })

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"
    assert data["age"] == 25

def test_create_user_invalid_age():
    response = client.post("/users", json={
        "name": "John Doe",
        "email": "john@example.com",
        "age": 15  # Contract requires >= 18
    })

    assert response.status_code == 400
    assert "age" in response.json()["detail"].lower()

def test_create_user_invalid_email():
    response = client.post("/users", json={
        "name": "John Doe",
        "email": "invalid-email",  # Missing @
        "age": 25
    })

    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()

def test_get_user_not_found():
    response = client.get("/users/nonexistent")

    assert response.status_code == 404
```

---

## See Also

- [Use with Pydantic](../../how-to/integration/pydantic.md) - Generate Pydantic models
- [CrewAI Agent Contracts](crewai-agent-contracts.md) - Multi-agent validation
- [API Rate Limiting](../../how-to/advanced/performance.md) - Rate limiting patterns

---

**Difficulty:** Intermediate
**Time:** 30 minutes
**Category:** Framework Integration
**Last Updated:** 2025-10-15
