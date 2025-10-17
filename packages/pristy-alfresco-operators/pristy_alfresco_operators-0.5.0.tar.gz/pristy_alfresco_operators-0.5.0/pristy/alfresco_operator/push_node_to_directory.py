# SPDX-FileCopyrightText: 2025 Jeci <info@jeci.fr>
#
# SPDX-License-Identifier: Apache-2.0

from typing import Any

from airflow.models.baseoperator import BaseOperator

class PushToDirectoryOperator(BaseOperator):
    """
    Simple operator that query children api.
    """
    def __init__(self, *, node, **kwargs):
        super().__init__(**kwargs)
        self.node = node

    def execute(self, context):
        from importlib.resources import files
        import jsonschema
        import json
        import pathlib

        def _load_schema() -> dict[str, Any]:
            schema_path = files("pristy.schema").joinpath("node_injector.schema.json")
            with schema_path.open("r") as schema_file:
                content = json.load(schema_file)
            return content

        schema = _load_schema()
        node = self.node.resolve(context)
        node_json = json.dumps(node)
        try:
            jsonschema.validate(json.loads(node_json), schema=schema)
        except jsonschema.ValidationError as ex:
            msg = f"Fail to validate export. Original error {type(ex).__name__}: {ex}"
            raise RuntimeError(msg)
        out_dir = f"/usr/local/airflow/output{node['path']['short']}"
        out_file = f"{out_dir}/{node['name']}.json"
        self.log.debug(out_file)
        pathlib.Path(out_dir).mkdir(parents=True, exist_ok=True)
        pathlib.Path(out_file).write_text(node_json)
