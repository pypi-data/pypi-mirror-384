# How-To: Use with Pydantic

**Generate Pydantic models from AssertLang contracts for data validation in Python.**

---

## Overview

**What you'll learn:**
- Generate Pydantic models from PW type definitions
- Use generated models with FastAPI
- Validate data with Pydantic + PW contracts
- Integrate with CrewAI agent coordination

**Time:** 25 minutes
**Difficulty:** Intermediate
**Prerequisites:** [Write Your First Contract](../getting-started/first-contract.md)

---

## The Problem

You're building a Python API or agent system and need:
1. **Type-safe data validation** - Ensure inputs match expected schema
2. **Automatic JSON serialization** - API request/response bodies
3. **Schema documentation** - Auto-generate OpenAPI/Swagger docs
4. **Contract enforcement** - Validate business rules beyond just types

Pydantic is Python's standard for data validation, but writing duplicate validation logic (Pydantic + PW contracts) is tedious and error-prone.

---

## The Solution

AssertLang can generate Pydantic models directly from type definitions:

```promptware
# user.al
type User:
  name: String
  email: String
  age: Int
end
```

↓ **Generate with `asl build`** ↓

```python
# user.py
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str
    email: str
    age: int
```

This ensures your Pydantic models and PW contracts stay in sync.

---

## Step 1: Define Types in AssertLang

### Basic Type Definition

```promptware
# models.al
type User:
  name: String
  email: String
  age: Int
  is_active: Bool
end
```

### With Documentation

```promptware
type Product:
  # Product identifier
  id: String

  # Product display name
  name: String

  # Price in USD
  price: Float

  # Available quantity
  stock: Int
end
```

Documentation becomes Pydantic `Field(description=...)`.

### With Validation Contracts

```promptware
function create_user(name: String, email: String, age: Int) -> User
  requires:
    len(name) > 0
    "@" in email
    age >= 18
  do
    return User(name=name, email=email, age=age)
  end
end
```

---

## Step 2: Generate Pydantic Models

### Using CLI

```bash
# Generate Pydantic models from PW file
asl build models.al --lang pydantic -o models.py
```

**Output:** `models.py`
```python
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class User(BaseModel):
    name: str
    email: str
    age: int
    is_active: bool


class Product(BaseModel):
    id: str = Field(description="Product identifier")
    name: str = Field(description="Product display name")
    price: float = Field(description="Price in USD")
    stock: int = Field(description="Available quantity")
```

### Using Python API

```python
# generate_models.py
from dsl.parser import PWParser
from language.pydantic_generator import generate_pydantic

# Parse PW file
parser = PWParser()
module = parser.parse_file("models.al")

# Generate Pydantic code
pydantic_code = generate_pydantic(module)

# Write to file
with open("models.py", "w") as f:
    f.write(pydantic_code)

print("✅ Generated models.py")
```

---

## Step 3: Use with FastAPI

### Define API with PW Contracts

```promptware
# api_contracts.al
type CreateUserRequest:
  name: String
  email: String
  age: Int
end

type UserResponse:
  id: String
  name: String
  email: String
  age: Int
  created_at: String
end

function create_user(req: CreateUserRequest) -> UserResponse
  requires:
    len(req.name) > 0
    len(req.name) <= 100
    "@" in req.email
    len(req.email) <= 255
    req.age >= 18
    req.age <= 150
  ensures:
    len(result.id) > 0
    result.name == req.name
    result.email == req.email
    result.age == req.age
  do
    # Implementation here
  end
end
```

### Generate Pydantic Models

```bash
asl build api_contracts.al --lang pydantic -o models.py
```

### Use in FastAPI

```python
# main.py
from fastapi import FastAPI
from models import CreateUserRequest, UserResponse
from api_contracts import create_user  # Generated PW contract

app = FastAPI()

@app.post("/users", response_model=UserResponse)
def create_user_endpoint(req: CreateUserRequest):
    """
    Create a new user.

    - Pydantic validates types (name: str, email: str, age: int)
    - PW contract validates business rules (age >= 18, email has @, etc.)
    """
    # Call PW contract function (validates preconditions)
    user = create_user(req)

    # Contract ensures postconditions (id exists, fields match)
    return user
```

**Benefits:**
- **Pydantic** handles JSON parsing, type validation, OpenAPI schema
- **PW contracts** handle business logic validation (age >= 18, email format)
- **Single source of truth** - Types and validation defined once in PW

---

## Step 4: Complex Types

### Optional Fields

```promptware
type UserProfile:
  user_id: String
  bio: Option<String>
  avatar_url: Option<String>
end
```

↓ Generates ↓

```python
class UserProfile(BaseModel):
    user_id: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
```

### Lists and Maps

```promptware
type Order:
  order_id: String
  items: List<String>
  quantities: Map<String, Int>
  tags: List<String>
end
```

↓ Generates ↓

```python
class Order(BaseModel):
    order_id: str
    items: List[str]
    quantities: Dict[str, int]
    tags: List[str]
```

### Nested Types

```promptware
type Address:
  street: String
  city: String
  zip_code: String
end

type Customer:
  name: String
  email: String
  address: Address
  billing_address: Option<Address>
end
```

↓ Generates ↓

```python
class Address(BaseModel):
    street: str
    city: str
    zip_code: str


class Customer(BaseModel):
    name: str
    email: str
    address: Address
    billing_address: Optional[Address] = None
```

---

## Step 5: Integration with CrewAI

### Define Agent Input/Output Contracts

```promptware
# agents/research_agent.al
type ResearchQuery:
  topic: String
  max_results: Int
  sources: List<String>
end

type ResearchResult:
  topic: String
  summary: String
  sources: List<String>
  confidence: Float
end

function research(query: ResearchQuery) -> ResearchResult
  requires:
    len(query.topic) > 0
    query.max_results > 0
    query.max_results <= 100
  ensures:
    result.topic == query.topic
    len(result.summary) > 0
    result.confidence >= 0.0
    result.confidence <= 1.0
  do
    # Implementation
  end
end
```

### Generate Pydantic Models

```bash
asl build agents/research_agent.al --lang pydantic -o agents/models.py
```

### Use with CrewAI

```python
# agents/research_agent.py
from crewai import Agent, Task
from agents.models import ResearchQuery, ResearchResult
from agents.research_agent import research  # PW contract

# Define agent
researcher = Agent(
    role="Research Analyst",
    goal="Find accurate information on given topics",
    backstory="Expert researcher with access to multiple sources"
)

# Task with type-safe input
def create_research_task(query: ResearchQuery) -> Task:
    """
    Type-safe task creation.
    - Pydantic validates query structure
    - PW contract validates business rules
    """
    return Task(
        description=f"Research: {query.topic}",
        agent=researcher,
        expected_output=ResearchResult,
    )

# Execute with validation
query = ResearchQuery(
    topic="AI Agent Frameworks",
    max_results=10,
    sources=["arxiv", "github"]
)

# PW contract validates preconditions
result = research(query)

# Contract ensures result.confidence is valid (0.0-1.0)
print(f"Confidence: {result.confidence}")
```

---

## Step 6: TypedDict for LangGraph

LangGraph uses TypedDict for state machines. Generate TypedDict instead of Pydantic:

```promptware
# workflow_state.al
type WorkflowState:
  current_step: String
  data: Map<String, Any>
  completed_steps: List<String>
  errors: List<String>
end
```

### Generate TypedDict

```bash
asl build workflow_state.al --lang typeddict -o state.py
```

**Output:**
```python
from __future__ import annotations
from typing import TypedDict, List, Dict, Any

class WorkflowState(TypedDict):
    current_step: str
    data: Dict[str, Any]
    completed_steps: List[str]
    errors: List[str]
```

### Use with LangGraph

```python
# workflow.py
from langgraph.graph import StateGraph
from state import WorkflowState

# Define graph with typed state
workflow = StateGraph(WorkflowState)

def process_step(state: WorkflowState) -> WorkflowState:
    """Type-safe state transition."""
    return {
        **state,
        "current_step": "processing",
        "completed_steps": state["completed_steps"] + ["input_validation"]
    }

workflow.add_node("process", process_step)
```

---

## Real-World Example: E-commerce API

### Define Types and Contracts

```promptware
# ecommerce.al
type Product:
  id: String
  name: String
  price: Float
  stock: Int
end

type CartItem:
  product_id: String
  quantity: Int
end

type Cart:
  user_id: String
  items: List<CartItem>
  total: Float
end

function add_to_cart(
    cart: Cart,
    product: Product,
    quantity: Int
) -> Cart
  requires:
    quantity > 0
    quantity <= product.stock
    product.price >= 0.0
  ensures:
    result.total >= cart.total
  do
    # Implementation
  end
end

function checkout(cart: Cart, payment_method: String) -> String
  requires:
    len(cart.items) > 0
    cart.total > 0.0
    len(payment_method) > 0
  ensures:
    len(result) > 0  # Order ID
  do
    # Implementation
  end
end
```

### Generate Pydantic + Contracts

```bash
# Generate Pydantic models
asl build ecommerce.al --lang pydantic -o models.py

# Generate Python contracts
asl build ecommerce.al --lang python -o contracts.py
```

### FastAPI Implementation

```python
# api.py
from fastapi import FastAPI, HTTPException
from models import Product, Cart, CartItem
from contracts import add_to_cart, checkout

app = FastAPI()

# In-memory storage (use real DB in production)
products = {}
carts = {}

@app.post("/cart/{user_id}/add")
def add_item(user_id: str, product_id: str, quantity: int):
    """
    Add item to cart with validation.
    - Pydantic validates types
    - PW contract validates stock, quantity > 0, etc.
    """
    product = products.get(product_id)
    if not product:
        raise HTTPException(404, "Product not found")

    cart = carts.get(user_id, Cart(user_id=user_id, items=[], total=0.0))

    try:
        # Contract validates preconditions (quantity <= stock, etc.)
        updated_cart = add_to_cart(cart, product, quantity)
        carts[user_id] = updated_cart
        return updated_cart

    except ContractViolation as e:
        # User-friendly error from contract
        raise HTTPException(400, str(e))


@app.post("/cart/{user_id}/checkout")
def checkout_cart(user_id: str, payment_method: str):
    """
    Checkout with validation.
    - Contract ensures cart not empty
    - Contract validates payment method
    """
    cart = carts.get(user_id)
    if not cart:
        raise HTTPException(404, "Cart not found")

    try:
        # Contract validates preconditions
        order_id = checkout(cart, payment_method)
        return {"order_id": order_id, "total": cart.total}

    except ContractViolation as e:
        raise HTTPException(400, str(e))
```

**Benefits:**
- **Type safety** - Pydantic validates JSON structure
- **Business logic** - PW contracts validate stock, totals, etc.
- **Auto-generated docs** - OpenAPI schema from Pydantic models
- **Single source of truth** - Types and validation defined once

---

## Tips & Best Practices

### 1. Keep Types Simple

Pydantic models should be data containers, not behavior:

```promptware
# Good: Simple data types
type User:
  name: String
  email: String
  age: Int
end

# Avoid: Complex methods in types (use functions instead)
```

### 2. Use Contracts for Validation

Let Pydantic handle types, PW contracts handle business rules:

```promptware
function create_order(items: List<CartItem>, total: Float) -> Order
  requires:
    len(items) > 0       # Business rule
    total > 0.0          # Business rule
    forall item in items: item.quantity > 0  # Business rule
  do
    # Implementation
  end
end
```

### 3. Document Fields

Documentation becomes Pydantic `Field(description=...)`:

```promptware
type Order:
  # Unique order identifier (UUID format)
  order_id: String

  # Order total in USD (tax included)
  total: Float

  # ISO 8601 timestamp
  created_at: String
end
```

### 4. Regenerate on Changes

After updating PW types, regenerate Pydantic models:

```bash
# Watch for changes and auto-regenerate
watch -n 1 asl build models.al --lang pydantic -o models.py
```

### 5. Version Your Schemas

Track schema versions for API compatibility:

```promptware
type UserV1:
  name: String
  email: String
end

type UserV2:
  name: String
  email: String
  age: Int          # New field in v2
end
```

---

## Comparison: Pydantic vs PW Contracts

| Feature | Pydantic | PW Contracts |
|---------|----------|--------------|
| **Type validation** | ✅ Excellent | ✅ Excellent |
| **JSON parsing** | ✅ Automatic | ❌ Manual |
| **OpenAPI schema** | ✅ Auto-generated | ❌ N/A |
| **Business rules** | ⚠️ Custom validators | ✅ Built-in (requires/ensures) |
| **Multi-language** | ❌ Python only | ✅ Python, JS, Go, Rust, C# |
| **Runtime performance** | ⚠️ Slower | ✅ Fast |

**Best approach:** Use both together
- **Pydantic** for API layer (JSON, OpenAPI, FastAPI integration)
- **PW contracts** for business logic (validation, rules, guarantees)

---

## Troubleshooting

### Issue: "Cannot generate Pydantic for generic types"

**Problem:**
```promptware
type Container<T>:
  value: T
end
```

**Error:**
```
# Generic type - implement as needed
```

**Solution:** Use concrete types:
```promptware
type StringContainer:
  value: String
end

type IntContainer:
  value: Int
end
```

---

### Issue: "Field types don't match"

**Problem:**
```python
# PW generates: age: int
# But you want: age: Optional[int]
```

**Solution:** Use Option in PW:
```promptware
type User:
  name: String
  age: Option<Int>  # Generates Optional[int]
end
```

---

### Issue: "Need custom Pydantic validators"

**Problem:** Pydantic's `@validator` not supported in generated code.

**Solution:** Extend generated models:
```python
# models.py (generated)
class User(BaseModel):
    name: str
    email: str

# custom_models.py (manual)
from models import User as BaseUser
from pydantic import validator

class User(BaseUser):
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email')
        return v.lower()
```

---

## Summary

**Workflow:**
1. Define types in PW (single source of truth)
2. Generate Pydantic models with `asl build`
3. Use models in FastAPI, CrewAI, or other Python frameworks
4. Combine with PW contracts for validation

**Benefits:**
- Type-safe data models
- Auto-generated from PW definitions
- Compatible with FastAPI, CrewAI, LangGraph
- Single source of truth for types
- Contracts enforce business rules

**Commands:**
```bash
# Generate Pydantic models
asl build types.al --lang pydantic -o models.py

# Generate TypedDict (for LangGraph)
asl build types.al --lang typeddict -o state.py

# Generate Python contracts + Pydantic
asl build contracts.al --lang python -o contracts.py
asl build contracts.al --lang pydantic -o models.py
```

---

## Next Steps

- **[Integrate with CrewAI](crewai.md)** - Multi-agent coordination with contracts
- **[Integrate with LangGraph](langgraph.md)** - State machines with TypedDict
- **[Handle Complex Types](../../advanced/complex-types.md)** - Option, Result, generics
- **[Deploy to Production](../../deployment/production.md)** - Production-ready APIs

---

## See Also

- **[API Reference: Runtime](../../reference/runtime-api.md)** - Python/JavaScript APIs
- **[Cookbook: CrewAI Agents](../../cookbook/framework-integration/crewai-agent-contracts.md)** - Agent validation patterns
- **[Example: User Service](../../../examples/agent_coordination/user_service_contract.al)** - Full agent example

---

**Difficulty:** Intermediate
**Time:** 25 minutes
**Last Updated:** 2025-10-15
