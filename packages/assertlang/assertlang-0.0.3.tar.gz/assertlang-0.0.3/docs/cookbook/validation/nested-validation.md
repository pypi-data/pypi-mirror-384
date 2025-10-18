# Nested Object Validation

**Validate complex data structures with nested objects, arrays, and deeply nested fields.**

---

## Problem

Real-world data is rarely flat:
- User profiles with nested address objects
- Orders with arrays of line items
- API responses with multiple nested levels
- Configuration files with hierarchical structure
- Form data with repeated sections

**Bad approach:**
```python
# Python: Manual validation at every level
def create_order(order_data: dict):
    # Validate top level
    if not order_data.get('customer'):
        raise ValueError("Missing customer")

    # Validate nested customer
    customer = order_data['customer']
    if not customer.get('address'):
        raise ValueError("Missing address")

    # Validate nested address
    address = customer['address']
    if not address.get('zip_code'):
        raise ValueError("Missing zip code")

    # ... endless nested checks ...
```

**Issues:**
- Verbose and repetitive
- Error-prone
- Hard to maintain
- Inconsistent validation

---

## Solution

Use AssertLang contracts for hierarchical validation:

```promptware
type Address:
  street: String
  city: String
  state: String
  zip_code: String
end

type Customer:
  name: String
  email: String
  address: Address
end

function validate_customer(customer: Customer) -> Result<Customer, String>
  requires:
    len(customer.name) > 0
    "@" in customer.email
    len(customer.address.street) > 0
    len(customer.address.zip_code) == 5
  do
    return Ok(customer)
  end
end
```

---

## Basic Nested Validation

### Two-Level Nesting

```promptware
type Address:
  street: String
  city: String
  zip_code: String
end

type User:
  name: String
  email: String
  address: Address
end

function validate_address(address: Address) -> Result<Address, String>
  do
    if len(address.street) == 0:
      return Err("Street cannot be empty")
    end

    if len(address.city) == 0:
      return Err("City cannot be empty")
    end

    if len(address.zip_code) != 5:
      return Err("ZIP code must be 5 digits")
    end

    return Ok(address)
  end
end

function validate_user(user: User) -> Result<User, List<String>>
  do
    let errors = []

    # Validate top-level fields
    if len(user.name) == 0:
      errors = errors + ["Name cannot be empty"]
    end

    if not ("@" in user.email):
      errors = errors + ["Invalid email format"]
    end

    # Validate nested address
    let address_result = validate_address(user.address)
    if address_result is Err(msg):
      errors = errors + ["Address: " + msg]
    end

    if len(errors) > 0:
      return Err(errors)
    end

    return Ok(user)
  end
end
```

---

## Array Validation

### Validate Array of Objects

```promptware
type LineItem:
  product_id: String
  quantity: Int
  price: Float
end

type Order:
  order_id: String
  items: List<LineItem>
  total: Float
end

function validate_line_item(item: LineItem) -> Result<LineItem, String>
  do
    if len(item.product_id) == 0:
      return Err("Product ID cannot be empty")
    end

    if item.quantity <= 0:
      return Err("Quantity must be positive")
    end

    if item.price <= 0.0:
      return Err("Price must be positive")
    end

    return Ok(item)
  end
end

function validate_order(order: Order) -> Result<Order, List<String>>
  do
    let errors = []

    # Validate order ID
    if len(order.order_id) == 0:
      errors = errors + ["Order ID cannot be empty"]
    end

    # Validate items array
    if len(order.items) == 0:
      errors = errors + ["Order must have at least one item"]
    end

    # Validate each line item
    let item_index = 0
    for item in order.items:
      let item_result = validate_line_item(item)
      if item_result is Err(msg):
        errors = errors + ["Item " + String(item_index) + ": " + msg]
      end
      item_index = item_index + 1
    end

    # Validate total matches sum of items
    let calculated_total = 0.0
    for item in order.items:
      calculated_total = calculated_total + (Float(item.quantity) * item.price)
    end

    if order.total != calculated_total:
      errors = errors + ["Total mismatch: expected " + String(calculated_total) + ", got " + String(order.total)]
    end

    if len(errors) > 0:
      return Err(errors)
    end

    return Ok(order)
  end
end
```

---

## Deep Nesting

### Three-Level Hierarchy

```promptware
type ContactInfo:
  phone: String
  email: String
end

type Address:
  street: String
  city: String
  state: String
  zip_code: String
end

type Person:
  name: String
  contact: ContactInfo
  address: Address
end

type Company:
  name: String
  employees: List<Person>
  headquarters: Address
end

function validate_contact_info(contact: ContactInfo) -> Result<ContactInfo, String>
  do
    if len(contact.phone) != 10:
      return Err("Phone must be 10 digits")
    end

    if not ("@" in contact.email):
      return Err("Invalid email")
    end

    return Ok(contact)
  end
end

function validate_person(person: Person) -> Result<Person, List<String>>
  do
    let errors = []

    if len(person.name) == 0:
      errors = errors + ["Name cannot be empty"]
    end

    # Validate nested contact
    let contact_result = validate_contact_info(person.contact)
    if contact_result is Err(msg):
      errors = errors + ["Contact: " + msg]
    end

    # Validate nested address
    let address_result = validate_address(person.address)
    if address_result is Err(msg):
      errors = errors + ["Address: " + msg]
    end

    if len(errors) > 0:
      return Err(errors)
    end

    return Ok(person)
  end
end

function validate_company(company: Company) -> Result<Company, List<String>>
  do
    let errors = []

    if len(company.name) == 0:
      errors = errors + ["Company name cannot be empty"]
    end

    # Validate headquarters address
    let hq_result = validate_address(company.headquarters)
    if hq_result is Err(msg):
      errors = errors + ["Headquarters: " + msg]
    end

    # Validate employees array
    if len(company.employees) == 0:
      errors = errors + ["Company must have at least one employee"]
    end

    let emp_index = 0
    for employee in company.employees:
      let emp_result = validate_person(employee)
      if emp_result is Err(emp_errors):
        for err in emp_errors:
          errors = errors + ["Employee " + String(emp_index) + ": " + err]
        end
      end
      emp_index = emp_index + 1
    end

    if len(errors) > 0:
      return Err(errors)
    end

    return Ok(company)
  end
end
```

---

## Optional Nested Fields

### Handling Option Types

```promptware
type ShippingAddress:
  street: String
  city: String
  zip_code: String
end

type BillingInfo:
  card_number: String
  expiry: String
end

type Customer:
  name: String
  email: String
  shipping_address: Option<ShippingAddress>
  billing_info: Option<BillingInfo>
end

function validate_customer_with_optionals(
    customer: Customer
) -> Result<Customer, List<String>>
  do
    let errors = []

    # Validate required fields
    if len(customer.name) == 0:
      errors = errors + ["Name required"]
    end

    if not ("@" in customer.email):
      errors = errors + ["Invalid email"]
    end

    # Validate optional shipping address
    if customer.shipping_address is Some(addr):
      let addr_result = validate_address(addr)
      if addr_result is Err(msg):
        errors = errors + ["Shipping: " + msg]
      end
    end

    # Validate optional billing info
    if customer.billing_info is Some(billing):
      if len(billing.card_number) != 16:
        errors = errors + ["Billing: Card number must be 16 digits"]
      end
    end

    if len(errors) > 0:
      return Err(errors)
    end

    return Ok(customer)
  end
end
```

---

## Real-World Examples

### E-Commerce Order Validation

```python
# Python
from nested_validation import validate_order, Err
from typing import List, Dict

def process_order(order_data: dict) -> dict:
    """Process order with nested validation."""

    # Convert dict to Order object
    order = Order(
        order_id=order_data['order_id'],
        items=[
            LineItem(
                product_id=item['product_id'],
                quantity=item['quantity'],
                price=item['price']
            )
            for item in order_data['items']
        ],
        total=order_data['total']
    )

    # Validate entire order (including all nested items)
    result = validate_order(order)

    if isinstance(result, Err):
        return {
            "success": False,
            "errors": result.error
        }

    # Process order
    order_id = save_order_to_db(result.value)

    return {
        "success": True,
        "order_id": order_id
    }

# Usage
order_data = {
    "order_id": "ORD-12345",
    "items": [
        {"product_id": "PROD-1", "quantity": 2, "price": 29.99},
        {"product_id": "PROD-2", "quantity": 1, "price": 49.99}
    ],
    "total": 109.97
}

response = process_order(order_data)
if response["success"]:
    print(f"Order processed: {response['order_id']}")
else:
    print(f"Validation errors: {response['errors']}")
```

### Company Directory API

```python
# Python (FastAPI)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from nested_validation import validate_company, Err

app = FastAPI()

class ContactInfoModel(BaseModel):
    phone: str
    email: str

class AddressModel(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str

class PersonModel(BaseModel):
    name: str
    contact: ContactInfoModel
    address: AddressModel

class CompanyModel(BaseModel):
    name: str
    employees: List[PersonModel]
    headquarters: AddressModel

@app.post("/companies")
def create_company(company: CompanyModel):
    """Create company with nested validation."""

    # Convert Pydantic model to PW types
    company_obj = to_pw_company(company)

    # Validate with contracts
    result = validate_company(company_obj)

    if isinstance(result, Err):
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Validation failed",
                "errors": result.error
            }
        )

    # Save to database
    company_id = save_company(result.value)

    return {
        "success": True,
        "company_id": company_id,
        "employees_count": len(result.value.employees)
    }
```

---

## Common Pitfalls

### ❌ Validating Only Top Level

```python
# Bad: Only checks top-level fields
def validate_bad(order: dict) -> bool:
    if 'order_id' not in order:
        return False
    if 'items' not in order:
        return False
    # Missing: validation of nested items!
    return True
```

### ✅ Validate All Levels

```promptware
# Good: Validate entire hierarchy
function validate_good(order: Order) -> Result<Order, List<String>>
  do
    let errors = []

    # Top level
    if len(order.order_id) == 0:
      errors = errors + ["Order ID required"]
    end

    # Nested items
    for item in order.items:
      let item_result = validate_line_item(item)
      if item_result is Err(msg):
        errors = errors + [msg]
      end
    end

    if len(errors) > 0:
      return Err(errors)
    end

    return Ok(order)
  end
end
```

### ❌ Losing Error Context

```python
# Bad: Generic error, no context about which field failed
def validate_bad(company: Company) -> bool:
    for employee in company.employees:
        if not is_valid(employee):
            return False  # Which employee? What failed?
    return True
```

### ✅ Preserve Error Context

```promptware
# Good: Include path to failed field
function validate_good(company: Company) -> Result<Company, List<String>>
  do
    let errors = []
    let emp_index = 0

    for employee in company.employees:
      let emp_result = validate_person(employee)
      if emp_result is Err(emp_errors):
        for err in emp_errors:
          errors = errors + ["Employee " + String(emp_index) + ": " + err]
        end
      end
      emp_index = emp_index + 1
    end

    if len(errors) > 0:
      return Err(errors)
    end

    return Ok(company)
  end
end
```

---

## Performance Optimization

### Early Exit on Critical Errors

```promptware
function validate_fast(order: Order) -> Result<Order, String>
  do
    # Check critical fields first
    if len(order.order_id) == 0:
      return Err("Order ID required")  # Exit immediately
    end

    # Expensive nested validation only if critical checks pass
    for item in order.items:
      let item_result = validate_line_item(item)
      if item_result is Err(msg):
        return Err(msg)  # First error stops validation
      end
    end

    return Ok(order)
  end
end
```

### Parallel Validation

```python
# Python: Validate independent nested objects in parallel
from concurrent.futures import ThreadPoolExecutor

def validate_company_parallel(company: Company) -> Result:
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Validate employees in parallel
        employee_results = list(executor.map(
            validate_person,
            company.employees
        ))

    # Collect errors
    errors = []
    for i, result in enumerate(employee_results):
        if isinstance(result, Err):
            errors.extend([f"Employee {i}: {e}" for e in result.error])

    if errors:
        return Err(errors)

    return Ok(company)
```

---

## Testing

```python
# Python (pytest)
import pytest
from nested_validation import *

def test_validate_user_valid():
    user = User(
        name="John Doe",
        email="john@example.com",
        address=Address(
            street="123 Main St",
            city="Springfield",
            zip_code="12345"
        )
    )

    result = validate_user(user)
    assert isinstance(result, Ok)

def test_validate_user_invalid_nested():
    user = User(
        name="John Doe",
        email="john@example.com",
        address=Address(
            street="",  # Invalid: empty street
            city="Springfield",
            zip_code="12345"
        )
    )

    result = validate_user(user)
    assert isinstance(result, Err)
    assert any("Street" in err for err in result.error)

def test_validate_order_items():
    order = Order(
        order_id="ORD-123",
        items=[
            LineItem("PROD-1", 2, 10.00),
            LineItem("PROD-2", -1, 20.00),  # Invalid: negative quantity
        ],
        total=30.00
    )

    result = validate_order(order)
    assert isinstance(result, Err)
    assert any("Item 1" in err for err in result.error)
    assert any("Quantity" in err for err in result.error)

def test_validate_company_deep_nesting():
    company = Company(
        name="Acme Corp",
        employees=[
            Person(
                name="Alice",
                contact=ContactInfo("5551234567", "alice@example.com"),
                address=Address("1 Main St", "City", "ST", "12345")
            )
        ],
        headquarters=Address("100 HQ Blvd", "City", "ST", "12345")
    )

    result = validate_company(company)
    assert isinstance(result, Ok)
```

---

## See Also

- [Custom Validators](custom-validators.md) - Build reusable validators
- [Conditional Validation](conditional-validation.md) - Field dependencies
- [Multi-Field Constraints](multi-field-constraints.md) - Cross-field rules
- [Array Bounds](array-bounds.md) - Array validation patterns

---

**Difficulty:** Intermediate
**Time:** 15 minutes
**Category:** Validation
**Last Updated:** 2025-10-15
