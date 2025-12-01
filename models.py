from pydantic import BaseModel, Field, EmailStr, BeforeValidator
from typing import Optional, List
from typing_extensions import Annotated

# Helper for ObjectId
PyObjectId = Annotated[str, BeforeValidator(str)]

class Property(BaseModel):
    name: str = Field(..., description="Name of the property")
    address: str = Field(..., description="Address of the property")
    city: str = Field(..., description="City location")
    price: float = Field(..., description="Price of the property")

class Client(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(..., description="Client's full name")
    email: EmailStr = Field(..., description="Client's email address")
    phone: str = Field(..., description="Client's phone number")
    properties: List[Property] = Field(default=[], description="List of properties owned by the client")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "name": "Jane Doe",
                "email": "jane@example.com",
                "phone": "+1234567890",
                "properties": [
                    {
                        "name": "Sunset Villa",
                        "address": "123 Sunset Blvd",
                        "city": "Los Angeles",
                        "price": 1500000.0
                    }
                ]
            }
        }

class ClientCollection(BaseModel):
    clients: List[Client]
