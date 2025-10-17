# SPDX-FileCopyrightText: 2025 Jeci <info@jeci.fr>
#
# SPDX-License-Identifier: Apache-2.0

from airflow.models import Variable


def update_node_path(src_node, new_node):
    """
    Update node path with root and short path definitions.

    Behavior differs depending on whether the target is a site or a folder.

    Currently only the "documentLibrary" container is properly migrated.
    Content from other containers (links, dataLists, wiki, discussions, surf-config)
    is copied for archival purposes but may not be usable in Alfresco Share.

    Note: Future enhancement could include proper migration of other site containers.

    :param src_node: Source node from Alfresco with path information
    :param new_node: Target node to update with new path structure
    """
    import re
    short_path = src_node['path']['name']
    target_site = Variable.get("alfresco_export_target_site", default_var=None)
    target_root_uuid = Variable.get("alfresco_target_root_uuid", default_var=None)
    if target_site is not None:
        # Priority: inject into site if target_site variable is set
        new_node['path']['root'] = f"site:{target_site}"

        # If documentLibrary, remove all path before documentLibrary
        re_prefix_path = re.compile(r"/(Company Home|Espace racine)/Sites/[\w-]*/documentLibrary")
        if re_prefix_path.match(src_node['path']['name']):
            short_path = re_prefix_path.sub("", src_node['path']['name'])
            if len(short_path) < 1:
                short_path = "/"

        # If other container, keep only the container name
        re_prefix_path = re.compile(
            r"/(Company Home|Espace racine)/Sites/[\w-]*/(links|dataLists|wiki|discussions|surf-config)")
        if re_prefix_path.fullmatch(src_node['path']['name']):
            re_prefix_path = re.compile(r"/(Company Home|Espace racine)/Sites/[\w-]*")
            short_path = re_prefix_path.sub("", src_node['path']['name'])

    elif target_root_uuid is not None:
        # Inject into specific folder if target_root_uuid variable is set
        new_node['path']['root'] = f"node:{target_root_uuid}"
    else:
        # Default: inject at root
        new_node['path']['root'] = "root"

    # Optional: remove custom path prefix
    short_path_remove = Variable.get("short_path_remove", default_var=None)
    if short_path_remove is not None:
        new_node['path']['short'] = short_path.replace(short_path_remove, "")
    else:
        new_node['path']['short'] = short_path
