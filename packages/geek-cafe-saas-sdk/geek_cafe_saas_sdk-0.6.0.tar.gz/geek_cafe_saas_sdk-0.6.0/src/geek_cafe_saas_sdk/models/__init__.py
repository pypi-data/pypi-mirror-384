"""
Copyright 2024-2025 Geek Cafe, LLC
MIT License. See Project Root for the license information.

Geek Cafe SaaS SDK Models

NOTE: Models have been reorganized into domain-driven structure.
Import models directly from their domain modules:
  - geek_cafe_saas_sdk.domains.auth.models
  - geek_cafe_saas_sdk.domains.tenancy.models
  - geek_cafe_saas_sdk.domains.communities.models
  - geek_cafe_saas_sdk.domains.events.models
  - geek_cafe_saas_sdk.domains.messaging.models
  - geek_cafe_saas_sdk.domains.voting.models
  - geek_cafe_saas_sdk.domains.analytics.models
"""

from geek_cafe_saas_sdk.models.base_model import BaseModel

__all__ = ["BaseModel"]
