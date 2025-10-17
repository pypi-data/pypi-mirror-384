# SPDX-FileCopyrightText: 2025 Jeci <info@jeci.fr>
#
# SPDX-License-Identifier: Apache-2.0

from airflow.models.baseoperator import BaseOperator
from airflow.providers.http.hooks.http import HttpHook


class AlfrescoFetchMetadaOperator(BaseOperator):
    """
    Simple operator that query node metadata.
    :param node_id: (required) node id to fetch
    :param failed_not_found: (optional) failed if the node id is not found, else only log missing node.
    """

    def __init__(self, *, nodes, failed_not_found = True, **kwargs):
        super().__init__(**kwargs)
        self.http_hook = HttpHook(method="GET", http_conn_id="alfresco_api", )
        self.data = {"include": "path,aspectNames,properties"}
        self.nodes = nodes
        self.failed_not_found = failed_not_found

    def execute(self, context):
        self.log.debug(f"fetch_metadata type={self.nodes}")

        f_nodes = []
        if isinstance(self.nodes, list):
            for n in self.nodes:
                node = self.fetch_node(n)
                if node:
                    f_nodes.append(node)
        else:
            node = self.fetch_node(self.nodes)
            if node:
                f_nodes.append(node)

        return f_nodes

    def fetch_node(self, node_id):
        self.log.debug(f"fetch_node pid={node_id}")
        raw_resp = self.http_hook.run(
            endpoint=f"/alfresco/api/-default-/public/alfresco/versions/1/nodes/{node_id}",
            data=self.data,
        )

        if not self.failed_not_found and raw_resp.status_code != 200:
            self.log.info(f"Failed to fetch node metadata : {raw_resp.status_code}")
            return None

        resp_json = raw_resp.json()
        return resp_json['entry']
