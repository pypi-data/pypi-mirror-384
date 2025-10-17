# SPDX-FileCopyrightText: 2025 Jeci <info@jeci.fr>
#
# SPDX-License-Identifier: Apache-2.0

from airflow.exceptions import AirflowSkipException
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.models.baseoperator import BaseOperator


class SaveFolderToDbOperator(BaseOperator):
    """
    Save Alfresco folder children to PostgreSQL tracking table.

    :param child: List of child nodes to save
    :param table_name: Name of the table to save to (default: export_alfresco_folder_children)
    """

    def __init__(self, *, child, table_name: str = "export_alfresco_folder_children", **kwargs):
        super().__init__(**kwargs)
        self.child = child
        self.table_name = table_name

    def execute(self, context):
        from psycopg2 import sql

        if len(self.child) == 0:
            raise AirflowSkipException('No child to proceed')

        postgres_hook = PostgresHook(postgres_conn_id="local_pg")
        conn = postgres_hook.get_conn()
        cur = conn.cursor()

        try:
            insert_rows = []
            update_rows = []
            for c in self.child:
                if not c['isFolder']:
                    continue
                self.log.debug(f"save {c['parentId']} -> {c['id']} ({c['name']})")
                insert_rows.append((c['parentId'], c['id']))
                update_rows.append((c['parentId'],))

            if len(insert_rows) == 0:
                conn.rollback()
                raise AirflowSkipException('No file transformed, mark as skip')

            # Update state for parent nodes
            update_query = sql.SQL("UPDATE {table} SET state = 'success' WHERE uuid = %s").format(
                table=sql.Identifier(self.table_name)
            )
            cur.executemany(update_query, update_rows)

            # Insert new child nodes
            insert_query = sql.SQL("""
                INSERT INTO {table} (parentid, uuid, state)
                VALUES (%s, %s, 'new')
            """).format(table=sql.Identifier(self.table_name))
            cur.executemany(insert_query, insert_rows)

            conn.commit()
        finally:
            cur.close()
            conn.close()
