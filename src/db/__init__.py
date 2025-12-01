# app/db/__init__.py
from .connection import connect, close, db, MONGO_URI, DB_NAME
from .collections import clients_collection

__all__ = ["connect", "close", "db", "MONGO_URI", "DB_NAME", "clients_collection"]
