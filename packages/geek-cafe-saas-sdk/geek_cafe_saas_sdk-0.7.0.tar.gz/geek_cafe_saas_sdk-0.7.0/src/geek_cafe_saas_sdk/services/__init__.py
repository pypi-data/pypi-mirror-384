"""
Services Package
Contains all service classes for Geek Cafe Services

NOTE: Services have been reorganized into domain-driven structure.
Import services directly from their domain modules:
  - geek_cafe_saas_sdk.domains.auth.services
  - geek_cafe_saas_sdk.domains.tenancy.services
  - geek_cafe_saas_sdk.domains.communities.services
  - geek_cafe_saas_sdk.domains.events.services
  - geek_cafe_saas_sdk.domains.messaging.services
  - geek_cafe_saas_sdk.domains.voting.services
  - geek_cafe_saas_sdk.domains.analytics.services
"""

from .database_service import DatabaseService

__all__ = ['DatabaseService']
