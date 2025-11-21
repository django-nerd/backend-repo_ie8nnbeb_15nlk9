"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Variant(BaseModel):
    """
    Variant option for a product (e.g., Shulker bundle)
    """
    name: str = Field(..., description="Variant display name")
    type: Literal["bundle", "option"] = Field("option", description="Type of variant")
    price: Optional[float] = Field(None, ge=0, description="Optional fixed price for this variant")
    bundle_qty: Optional[int] = Field(None, ge=1, description="If bundle, how many base units included")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category e.g. Spawners, Money, Ranks")
    image_url: Optional[str] = Field(None, description="Image URL for product card")
    sku: Optional[str] = Field(None, description="Stock keeping unit / unique id")
    tags: Optional[List[str]] = Field(default=None, description="Search tags")
    in_stock: bool = Field(True, description="Whether product is in stock")
    variants: Optional[List[Variant]] = Field(default=None, description="Optional list of purchasable variants")

class Feedback(BaseModel):
    """
    Player feedback with star rating and optional message
    Collection name: "feedback"
    """
    stars: int = Field(..., ge=1, le=5, description="Star rating 1-5")
    message: Optional[str] = Field(None, description="Optional feedback message")
    ign: Optional[str] = Field(None, description="Player IGN")

# Add your own schemas here:
# --------------------------------------------------

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
