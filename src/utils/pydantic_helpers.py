# app/utils/pydantic_helpers.py
from pydantic import BeforeValidator
from typing_extensions import Annotated
from bson import ObjectId

# Use Pydantic v2 BeforeValidator pattern: store as string externally
PyObjectId = Annotated[str, BeforeValidator(lambda v: str(v) if v is not None else v)]
