# SPDX-FileCopyrightText: 2025 Jeci <info@jeci.fr>
#
# SPDX-License-Identifier: Apache-2.0

from airflow.models.baseoperator import BaseOperator
from pristy.alfresco_operator.utils import parse_alfresco_pagination


class AlfrescoSearchOperator(BaseOperator):
    """
    Operator that uses the Alfresco Search API.

    Supports pagination, sorting, and filtering of search results.

    :param query: Alfresco FTS query string
    :param http_conn_id: Airflow connection ID for Alfresco API
    :param page_size: Number of items per page
    :param max_items: Maximum number of items to retrieve
    :param sort_field: Field to sort by (default: cm:created)
    :param sort_ascending: Sort order (default: False for descending)
    """

    def __init__(
            self,
            *,
            query: str,
            http_conn_id: str = "alfresco_api",
            page_size: int = 3,
            max_items: int = 2000,
            sort_field: str = "cm:created",
            sort_ascending: bool = False,
            **kwargs):
        super().__init__(**kwargs)

        from airflow.providers.http.hooks.http import HttpHook
        self.http_hook = HttpHook(method="POST", http_conn_id=http_conn_id)
        self.query = query
        self.page_size = page_size
        self.max_items = max_items
        self.sort_field = sort_field
        self.sort_ascending = sort_ascending

    def execute(self, context):
        self.log.debug(f"search query={self.query}")

        self.data = {
            "query": {
                "query": self.query,
            },
            "paging": {
                "maxItems": self.page_size,
                "skipCount": 0
            },
            "include": ["path", "aspectNames", "properties"],
            "sort": [{"type": "FIELD", "field": self.sort_field, "ascending": self.sort_ascending}]
        }

        results = self.fetch_results(self.query)

        self.log.debug("--search results--")
        for result in results:
            self.log.debug(result)

        return results

    def fetch_results(self, query):
        entries = []

        response = self.http_hook.run(
            endpoint="/alfresco/api/-default-/public/search/versions/1/search",
            json=self.data,
        )
        all_responses = [response]

        # Extract entries from first response
        resp_json = response.json()
        for e in resp_json["list"]["entries"]:
            entries.append(e["entry"])
        total_items = len(entries)

        # Continue fetching while we haven't reached max_items
        while total_items < self.max_items:
            next_page_params = parse_alfresco_pagination(response, self.page_size)
            if not next_page_params:
                break

            self.log.info(f"Load next page with skipCount={next_page_params['skipCount']}")
            self.data["paging"]["skipCount"] = next_page_params["skipCount"]

            # Adjust page size for last request if needed
            remaining = self.max_items - total_items
            if remaining < self.page_size:
                self.data["paging"]["maxItems"] = remaining

            response = self.http_hook.run(
                endpoint="/alfresco/api/-default-/public/search/versions/1/search",
                json=self.data,
            )
            all_responses.append(response)

            # Extract entries from this response
            resp_json = response.json()
            for e in resp_json["list"]["entries"]:
                entries.append(e["entry"])
                total_items += 1
                if total_items >= self.max_items:
                    break

        return entries
