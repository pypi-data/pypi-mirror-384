# SPDX-FileCopyrightText: 2025 Jeci <info@jeci.fr>
#
# SPDX-License-Identifier: Apache-2.0

from airflow.exceptions import AirflowSkipException
from airflow.models import Variable
from airflow.models.baseoperator import BaseOperator


class TransformFileOperator(BaseOperator):
    """
    Operator that transforms Alfresco file nodes to Pristy pivot format.

    For each file node, creates a `node` object in `node_injector` format.

    The node is enriched by calling `pristy.alfresco_operator.update_node_path.update_node_path`
    and the optional `mapping_func` function.

    :param child: List of child nodes to transform
    :param mapping_func: Optional function to bind metadata or aspects.
                         Receives 2 parameters: src_node, new_node
    """

    def __init__(self, *, child, mapping_func=None, **kwargs):
        super().__init__(**kwargs)
        self.child = child
        self.mapping_func = mapping_func

    def execute(self, context):
        """
        Execute the transformation of file nodes.

        :param context: Airflow context
        :return: List of transformed nodes in pivot format
        """
        from pristy.alfresco_operator.update_node_path import update_node_path
        from pristy.alfresco_operator.utils import create_base_node

        nodes = []
        for c in self.child:
            if not c['isFile']:
                continue
            self.log.info(f"transform {c['id']} ({c['name']})")
            source_server = Variable.get('alfresco_source_server')

            if c['nodeType'] == 'app:filelink':
                source = {
                    "type": "alfresco",
                    "server": source_server,
                    "uuid": c['id']
                }
            elif 'content' not in c or c['content'] is None:
                self.log.warning(f"No content for {c['id']}")
                continue
            else:
                source = {
                    "type": "alfresco",
                    "server": source_server,
                    "uuid": c['id'],
                    "mimetype": c['content']['mimeType'],
                    "size": c['content']['sizeInBytes']
                }

            node = create_base_node(c)
            node["source"] = source

            update_node_path(c, node)
            if self.mapping_func is not None:
                self.mapping_func(c, node)
            nodes.append(node)

        if len(nodes) == 0:
            raise AirflowSkipException('No file transformed, mark as skip')
        return nodes
