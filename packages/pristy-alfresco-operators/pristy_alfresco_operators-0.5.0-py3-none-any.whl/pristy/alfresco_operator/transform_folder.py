# SPDX-FileCopyrightText: 2025 Jeci <info@jeci.fr>
#
# SPDX-License-Identifier: Apache-2.0

from airflow.exceptions import AirflowSkipException
from airflow.models.baseoperator import BaseOperator


class TransformFolderOperator(BaseOperator):
    """
    Operator that transforms Alfresco folder nodes to Pristy pivot format.

    For each folder node, creates a `node` object in `node_injector` format.

    The node is enriched by calling `pristy.alfresco_operator.update_node_path.update_node_path`
    and the optional `mapping_func` function.

    Standard Alfresco folders (Data Dictionary, Sites, etc.) are automatically skipped.

    :param child: List of child nodes to transform
    :param mapping_func: Optional function to bind metadata or aspects.
                         Receives 2 parameters: src_node, new_node
    """

    def __init__(self, *, child, mapping_func=None, **kwargs):
        super().__init__(**kwargs)
        self.child = child
        self.mapping_func = mapping_func

    def execute(self, context):
        import re
        from pristy.alfresco_operator.update_node_path import update_node_path
        from pristy.alfresco_operator.utils import create_base_node

        nodes = []
        for c in self.child:
            self.log.debug(c)
            if not c['isFolder']:
                continue

            re_prefix_path = re.compile(r"/(Company Home|Espace racine)")
            if re_prefix_path.fullmatch(c['path']['name']):
                # Skip standard Alfresco system folders in Company Home
                if (c['name'] == 'Dictionnaire de données'
                        or c['name'] == 'Espace invité'
                        or c['name'] == 'Espaces Utilisateurs'
                        or c['name'] == 'Partagé'
                        or c['name'] == 'Pièces jointes IMAP'
                        or c['name'] == 'Racine IMAP'
                        or c['name'] == 'Sites'):
                    self.log.info(f"skip {c['path']['name']}/{c['name']}")
                    continue

            re_prefix_path = re.compile(r"/(Company Home|Espace racine)/Sites/[\w-]*")
            if re_prefix_path.fullmatch(c['path']['name']):
                # Skip site containers (documentLibrary, etc.)
                self.log.info(f"skip {c['path']['name']}/{c['name']}")
                continue

            self.log.debug(f"transform {c['id']} ({c['name']})")

            node = create_base_node(c)
            update_node_path(c, node)
            if self.mapping_func is not None:
                self.mapping_func(c, node)
            nodes.append(node)

        if len(nodes) == 0:
            raise AirflowSkipException('No folder transformed, mark as skip')
        return nodes
