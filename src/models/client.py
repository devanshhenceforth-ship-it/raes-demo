# app/models/client.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from ..utils.pydantic_helpers import PyObjectId

import uuid

class Property(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID of the property")
    name: str = Field(..., description="Name of the property")
    address: str = Field(..., description="Address of the property")
    city: str = Field(..., description="City location")
    rent_price: float = Field(..., description="Price of the property")

class Client(BaseModel):
    name: str = Field(..., description="Client's full name")
    email: EmailStr = Field(..., description="Client's email address")
    phone: str = Field(..., description="Client's phone number")
    properties: List[Property] = Field(default=[], description="List of properties owned by the client")

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "name": "Jane Doe",
                "email": "jane@example.com",
                "phone": "+1234567890",
                "properties": [
                    {
                        "name": "Sunset Villa",
                        "address": "123 Sunset Blvd",
                        "city": "Los Angeles",
                        "rent_price": 1500000.0
                    }
                ]
            }
        }
    }



class ResponseClient(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(..., description="Client's full name")
    email: EmailStr = Field(..., description="Client's email address")
    phone: str = Field(..., description="Client's phone number")
    properties: List[Property] = Field(default=[], description="List of properties owned by the client")