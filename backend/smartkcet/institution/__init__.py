"""Institution management module.

This module handles institution registration, invitation flows, and student
management for the subscription platform upgrade.
"""

from .routes import router
from .service import InstitutionService

__all__ = ["InstitutionService", "router"]
