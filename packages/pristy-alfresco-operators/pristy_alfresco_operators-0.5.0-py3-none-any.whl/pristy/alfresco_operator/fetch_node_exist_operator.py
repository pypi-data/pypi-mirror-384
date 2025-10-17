# SPDX-FileCopyrightText: 2025 Jeci <info@jeci.fr>
#
# SPDX-License-Identifier: Apache-2.0

from airflow.exceptions import AirflowException
from airflow.providers.http.hooks.http import HttpHook
from airflow.models.baseoperator import BaseOperator


class AlfrescoFetchNodeExistOperator(BaseOperator):
    """
    Simple operator that fetch a node from Alfresco and return True if the node exists.
    :param node_id: (required)  node id to fetch
    """

    def __init__(self, *, node_id, **kwargs):
        super().__init__(**kwargs)
        self.alf_node_id = node_id
        self.http_hook = HttpHook(method="GET", http_conn_id="alfresco_api", )

    def execute(self, context):
        node_id = self.alf_node_id.resolve(context)
        raw_resp = self.http_hook.run(
            endpoint=f"/alfresco/api/-default-/public/alfresco/versions/1/nodes/{node_id}",
            data={"include": "path"},
        )
        if raw_resp.status_code == 200:
            return True
        elif raw_resp.status_code == 404:
            return False
        else:
            raise AirflowException(raw_resp.content)
