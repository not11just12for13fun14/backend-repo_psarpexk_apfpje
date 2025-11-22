"""
Database Schemas for Photo Catalog

Each Pydantic model maps to a MongoDB collection with the lowercase class name.
- User -> "user"
- Photo -> "photo"
- Purchase -> "purchase"
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class User(BaseModel):
    name: str = Field(..., description="Display name")
    email: str = Field(..., description="Email address")
    role: Literal["seller", "customer"] = Field(..., description="User role")
    api_key: Optional[str] = Field(None, description="Simple API key for auth")
    avatar_url: Optional[str] = Field(None, description="Optional avatar URL")

class Photo(BaseModel):
    title: str = Field(..., description="Photo title")
    description: Optional[str] = Field(None, description="Short description")
    url: str = Field(..., description="Full-size image URL")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL")
    themes: List[str] = Field(default_factory=list, description="List of themes/categories")
    tags: List[str] = Field(default_factory=list, description="Search tags")
    orientation: Literal["landscape", "portrait", "square"] = Field("landscape", description="Orientation")
    color_palette: Optional[List[str]] = Field(default=None, description="Dominant colors (hex)")
    price: float = Field(0.0, ge=0, description="Price in USD")
    seller_id: Optional[str] = Field(None, description="Owning seller user id (string)")
    is_public: bool = Field(True, description="Visible in public catalog")

class Purchase(BaseModel):
    user_id: str = Field(..., description="Purchasing customer id")
    photo_id: str = Field(..., description="Purchased photo id")
    price: float = Field(..., ge=0, description="Price at purchase time")
    license: Literal["standard", "extended"] = Field("standard", description="License type")
