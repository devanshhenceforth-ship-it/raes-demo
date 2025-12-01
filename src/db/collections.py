# app/db/collections.py
from ..db import connection

def clients_collection():
    return connection.db["clients"]

def inspections_collection():
    return connection.db["inspections"]

def rooms_collection():
    return connection.db["rooms"]

def items_collection():
    return connection.db["items"]

def item_comparisons_collection():
    return connection.db["item_comparisons"]

