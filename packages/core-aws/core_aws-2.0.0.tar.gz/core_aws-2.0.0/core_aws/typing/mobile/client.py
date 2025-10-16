# -*- coding: utf-8 -*-

from dataclasses import dataclass


@dataclass(frozen=True)
class MobileClient:
    """
    Mobile Client context that is provided by the
    client application.
    """

    installation_id: str
    """Unique identifier for the app installation."""

    app_title: str
    """Application title/name."""

    app_version_name: str
    """Human-readable version (e.g., '1.2.3')."""

    app_version_code: str
    """Build/version code (numeric identifier)."""

    app_package_name: str
    """Package identifier (e.g., 'com.example.app')."""
