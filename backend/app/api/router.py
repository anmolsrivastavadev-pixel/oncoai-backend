"""APIRouter that serves collection routes both with and without a trailing slash.

The contract writes collection paths as ``/lesions/`` in some places and
``/dermatologists`` in others; serving both avoids 307 redirects, which break CORS
preflights from the Capacitor WebView.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter


class SlashRouter(APIRouter):
    def add_api_route(self, path: str, endpoint: Callable[..., Any], **kwargs: Any) -> None:
        if path == "/" and self.prefix:
            include = kwargs.pop("include_in_schema", True)
            super().add_api_route("", endpoint, include_in_schema=include, **kwargs)
            super().add_api_route("/", endpoint, include_in_schema=False, **kwargs)
            return
        super().add_api_route(path, endpoint, **kwargs)
