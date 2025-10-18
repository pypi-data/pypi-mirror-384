"""
Pydantic Model Caching Examples
================================

This example demonstrates type-safe caching with Pydantic models.
"""
import time
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from redis_cache_toolkit import cached_model


# Example 1: Basic Pydantic model caching
print("=" * 60)
print("Example 1: Basic Pydantic Model Caching")
print("=" * 60)

class User(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool = True
    created_at: Optional[datetime] = None

@cached_model(User, timeout=300)
def get_user(user_id: int) -> dict:
    """Fetch user from database (simulated)."""
    print(f"  → Fetching user {user_id} from database...")
    time.sleep(1)
    return {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
        "is_active": True,
        "created_at": datetime.now()
    }

print("\nFirst call (from database):")
user1 = get_user(123)
print(f"  Type: {type(user1)}")
print(f"  User: {user1.name} <{user1.email}>")
print(f"  Active: {user1.is_active}")

print("\nSecond call (from cache):")
user2 = get_user(123)
print(f"  Type: {type(user2)}")
print(f"  User: {user2.name} <{user2.email}>")


# Example 2: Model with validation
print("\n" + "=" * 60)
print("Example 2: Model with Validation")
print("=" * 60)

class Product(BaseModel):
    id: int
    name: str
    price: float
    stock: int = 0
    
    @field_validator('price')
    @classmethod
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v
    
    @field_validator('stock')
    @classmethod
    def stock_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError('Stock cannot be negative')
        return v

@cached_model(Product, timeout=300)
def get_product(product_id: int) -> dict:
    """Fetch product with automatic validation."""
    print(f"  → Fetching product {product_id}...")
    return {
        "id": product_id,
        "name": f"Product {product_id}",
        "price": 99.99,
        "stock": 50
    }

print("\nFetching valid product:")
product = get_product(1)
print(f"  {product.name}: ${product.price} (Stock: {product.stock})")


# Example 3: Complex nested models
print("\n" + "=" * 60)
print("Example 3: Nested Pydantic Models")
print("=" * 60)

class Address(BaseModel):
    street: str
    city: str
    country: str
    postal_code: str

class Customer(BaseModel):
    id: int
    name: str
    email: str
    addresses: List[Address] = []
    premium: bool = False

@cached_model(Customer, timeout=300)
def get_customer(customer_id: int) -> dict:
    """Fetch customer with nested address data."""
    print(f"  → Fetching customer {customer_id}...")
    time.sleep(0.5)
    return {
        "id": customer_id,
        "name": f"Customer {customer_id}",
        "email": f"customer{customer_id}@example.com",
        "premium": True,
        "addresses": [
            {
                "street": "123 Main St",
                "city": "Istanbul",
                "country": "Turkey",
                "postal_code": "34000"
            },
            {
                "street": "456 Second Ave",
                "city": "Ankara",
                "country": "Turkey",
                "postal_code": "06000"
            }
        ]
    }

print("\nFetching customer with addresses:")
customer = get_customer(456)
print(f"  Customer: {customer.name} <{customer.email}>")
print(f"  Premium: {customer.premium}")
print(f"  Addresses:")
for addr in customer.addresses:
    print(f"    - {addr.street}, {addr.city}, {addr.country}")


# Example 4: Error handling with return_none_on_error
print("\n" + "=" * 60)
print("Example 4: Error Handling")
print("=" * 60)

class StrictProduct(BaseModel):
    id: int
    name: str
    price: float
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v

@cached_model(StrictProduct, timeout=60, return_none_on_error=True)
def get_product_with_error_handling(product_id: int) -> dict:
    """Gracefully handle validation errors."""
    if product_id == 999:
        # Simulate invalid data
        return {"id": 999, "name": "Invalid", "price": -10}
    return {"id": product_id, "name": "Valid Product", "price": 29.99}

print("\nFetching valid product:")
valid_product = get_product_with_error_handling(1)
print(f"  Result: {valid_product}")

print("\nFetching invalid product (returns None):")
invalid_product = get_product_with_error_handling(999)
print(f"  Result: {invalid_product}")


# Example 5: E-commerce order system
print("\n" + "=" * 60)
print("Example 5: E-commerce Order System")
print("=" * 60)

class OrderItem(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    
    @property
    def total_price(self) -> float:
        return self.quantity * self.unit_price

class Order(BaseModel):
    id: int
    customer_id: int
    items: List[OrderItem]
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)
    
    @property
    def total_amount(self) -> float:
        return sum(item.total_price for item in self.items)

@cached_model(Order, timeout=300)
def get_order(order_id: int) -> dict:
    """Fetch order with items."""
    print(f"  → Fetching order {order_id}...")
    time.sleep(0.5)
    return {
        "id": order_id,
        "customer_id": 123,
        "status": "completed",
        "items": [
            {
                "product_id": 1,
                "product_name": "Laptop",
                "quantity": 1,
                "unit_price": 999.99
            },
            {
                "product_id": 2,
                "product_name": "Mouse",
                "quantity": 2,
                "unit_price": 29.99
            }
        ]
    }

print("\nFetching order:")
order = get_order(789)
print(f"  Order #{order.id} - Status: {order.status}")
print(f"  Items:")
for item in order.items:
    print(f"    - {item.product_name} x{item.quantity}: ${item.total_price:.2f}")
print(f"  Total: ${order.total_amount:.2f}")


# Example 6: API response caching
print("\n" + "=" * 60)
print("Example 6: API Response Caching")
print("=" * 60)

class GitHubUser(BaseModel):
    login: str
    id: int
    name: Optional[str] = None
    company: Optional[str] = None
    blog: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    public_repos: int = 0
    followers: int = 0
    following: int = 0

@cached_model(GitHubUser, timeout=600)
def get_github_user(username: str) -> dict:
    """Simulate GitHub API call."""
    print(f"  → Fetching GitHub user: {username}")
    time.sleep(0.5)
    return {
        "login": username,
        "id": 12345,
        "name": "John Doe",
        "company": "Example Corp",
        "location": "San Francisco",
        "email": "john@example.com",
        "bio": "Software Developer",
        "public_repos": 50,
        "followers": 100,
        "following": 75
    }

print("\nFetching GitHub user:")
github_user = get_github_user("johndoe")
print(f"  {github_user.name} (@{github_user.login})")
print(f"  {github_user.bio}")
print(f"  📍 {github_user.location}")
print(f"  📦 {github_user.public_repos} repos")
print(f"  👥 {github_user.followers} followers, {github_user.following} following")


print("\n" + "=" * 60)
print("✅ All Pydantic examples completed!")
print("=" * 60)

