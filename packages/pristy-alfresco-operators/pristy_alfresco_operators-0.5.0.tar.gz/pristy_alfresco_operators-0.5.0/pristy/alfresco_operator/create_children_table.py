# SPDX-FileCopyrightText: 2025 Jeci <info@jeci.fr>
#
# SPDX-License-Identifier: Apache-2.0

from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.models.baseoperator import BaseOperator


class CreateChildrenTableOperator(BaseOperator):
    """
    Create PostgreSQL table for tracking Alfresco folder children migration.

    :param table_name: Name of the table to create (default: export_alfresco_folder_children)
    """

    def __init__(self, *, table_name: str = "export_alfresco_folder_children", **kwargs):
        super().__init__(**kwargs)
        self.table_name = table_name

    def execute(self, context):
        from psycopg2 import sql

        postgres_hook = PostgresHook(postgres_conn_id="local_pg")
        conn = postgres_hook.get_conn()
        cur = conn.cursor()
        try:
            # Drop table if exists
            drop_query = sql.SQL("DROP TABLE IF EXISTS {table}").format(
                table=sql.Identifier(self.table_name)
            )
            cur.execute(drop_query)

            # Create table with proper identifier
            create_query = sql.SQL("""
                CREATE TABLE {table} (
                id SERIAL PRIMARY KEY,
                parentid varchar,
                uuid varchar,
                state varchar DEFAULT 'new'
                )
            """).format(table=sql.Identifier(self.table_name))
            cur.execute(create_query)

            conn.commit()
        finally:
            cur.close()
            conn.close()
