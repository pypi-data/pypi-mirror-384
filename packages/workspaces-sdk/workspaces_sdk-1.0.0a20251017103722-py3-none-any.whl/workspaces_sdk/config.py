"""
Configuration module for Workspaces SDK

Handles environment variables and authentication headers.
"""

import os
from typing import Any, Dict

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_default_headers() -> Dict[str, Any]:
    """
    Get default headers for API requests including product ID.

    Returns:
        Dict[str, Any]: Dictionary containing default headers
    """
    headers = {}

    # Add product ID header if available in environment
    product_id = os.getenv("VITE_PRODUCT_ID")
    if product_id:
        headers["x-product-id"] = product_id

    return headers


def get_product_id() -> str:
    """
    Get the product ID from environment variables.

    Returns:
        str: Product ID or empty string if not found
    """
    return os.getenv("VITE_PRODUCT_ID", "")
