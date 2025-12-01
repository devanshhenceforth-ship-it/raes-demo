from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from ..utils.pydantic_helpers import PyObjectId

class Room(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    property_id: str = Field(..., description="ID of the property this room belongs to")
    name: str = Field(..., description="Name of the room (e.g. Master Bedroom)")
    type: str = Field(..., description="Type of room (Bedroom, Kitchen, Bathroom, Living Room, etc.)")
    floor: Optional[int] = Field(None, description="Floor number")
    size_sqft: Optional[float] = Field(None, description="Size of the room in square feet")
    description: Optional[str] = Field(None, description="Additional details about the room")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "property_id": "prop-uuid-123",
                "name": "Master Bedroom",
                "type": "Bedroom",
                "floor": 2,
                "size_sqft": 250.5,
                "description": "Spacious bedroom with ensuite"
            }
        }
    }

class Item(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    room_id: str = Field(..., description="ID of the room this item belongs to")
    name: str = Field(..., description="Name of the item")
    category: str = Field(..., description="Category (Furniture, Appliance, Decor, Fixture, etc.)")
    condition: str = Field(..., description="Condition (New, Good, Fair, Poor, Damaged)")
    brand: Optional[str] = Field(None, description="Brand name")
    model: Optional[str] = Field(None, description="Model number")
    serial_number: Optional[str] = Field(None, description="Serial number")
    purchase_date: Optional[datetime] = Field(None, description="Date of purchase")
    purchase_price: Optional[float] = Field(None, description="Purchase price")
    current_value: Optional[float] = Field(None, description="Estimated current value")
    warranty_expiry: Optional[datetime] = Field(None, description="Warranty expiration date")
    images: List[str] = Field(default=[], description="List of image URLs")
    notes: Optional[str] = Field(None, description="Maintenance notes or other details")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "room_id": "room-uuid-456",
                "name": "Smart TV",
                "category": "Electronics",
                "condition": "Good",
                "brand": "Samsung",
                "model": "QLED-55",
                "purchase_price": 1200.00,
                "notes": "Mounted on wall"
            }
        }
    }
