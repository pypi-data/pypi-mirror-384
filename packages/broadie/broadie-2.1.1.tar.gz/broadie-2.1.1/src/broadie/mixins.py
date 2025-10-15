# src/broadie/persistence.py
# Import the new SQLAlchemy-backed PersistenceMixin
from .persistence.mixins import PersistenceMixin

# Keep this file for backward compatibility - all existing imports will work
__all__ = ["PersistenceMixin"]
