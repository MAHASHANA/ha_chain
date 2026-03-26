"""Re-export from app.db.base for backward compatibility.

All models should import from ``app.db.base`` directly, but this module
keeps any existing ``from app.models.base import ...`` statements working.
"""

from app.db.base import Base, TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin

__all__ = ["Base", "TimestampMixin", "SoftDeleteMixin", "UUIDPrimaryKeyMixin"]
