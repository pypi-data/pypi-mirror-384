# SPDX-FileCopyrightText: 2025 Jeci <info@jeci.fr>
#
# SPDX-License-Identifier: Apache-2.0

"""
Utility functions for Alfresco operators.

This module provides common functionality shared across multiple operators
to avoid code duplication.
"""

from requests import Response


def parse_alfresco_pagination(response: Response, page_size: int) -> dict | None:
    """
    Parse Alfresco API pagination response and return next page parameters.

    :param response: HTTP response from Alfresco API
    :param page_size: Number of items per page
    :return: Dictionary with skipCount for next page, or None if no more pages
    """
    content = response.json()
    pagination = content['list']['pagination']

    if pagination['hasMoreItems']:
        skip_count = pagination['skipCount'] + page_size
        return {"skipCount": skip_count}
    return None


def create_base_node(src_node: dict) -> dict:
    """
    Create base node structure from Alfresco source node.

    This function extracts common metadata fields and creates a standardized
    node structure in Pristy pivot format.

    :param src_node: Source node from Alfresco API
    :return: Base node structure with common properties
    """
    created_at = src_node['createdAt'].replace("+0000", "Z")
    modified_at = src_node['modifiedAt'].replace("+0000", "Z")

    return {
        "name": src_node['name'],
        "type": src_node['nodeType'],
        "dateCreated": created_at,
        "owner": src_node['createdByUser']['id'],
        "path": {},
        "properties": {
            "cm:created": created_at,
            "cm:creator": src_node['createdByUser']['id'],
            "cm:modified": modified_at,
            "cm:modifier": src_node['modifiedByUser']['id']
        }
    }
