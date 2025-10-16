"""
Endpoint modules for the USF P1 Chatbot SDK
"""
from .chat import ChatEndpoints
from .ingestion import IngestionEndpoints
from .logs import LogsEndpoints
from .collections import CollectionsEndpoints
from .files import FilesEndpoints
from .patients import PatientsEndpoints

__all__ = [
    "ChatEndpoints",
    "IngestionEndpoints",
    "LogsEndpoints",
    "CollectionsEndpoints",
    "FilesEndpoints",
    "PatientsEndpoints",
]
