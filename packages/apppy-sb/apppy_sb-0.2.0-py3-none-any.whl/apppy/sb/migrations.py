import psycopg

from apppy.db.migrations import Migrations
from apppy.db.postgres import PostgresClient


class SupabaseMigrations(Migrations):
    def __init__(
        self,
        postgres_client: PostgresClient,
    ):
        self._postgres_client = postgres_client

    async def head(self) -> str | None:
        latest_migration_query = """
        SELECT version, name
        FROM supabase_migrations.schema_migrations
        ORDER BY version DESC
        LIMIT 1
        """
        try:
            result_set = await self._postgres_client.db_query_async(latest_migration_query)
            if result_set is None or len(result_set) != 1:
                return None

            return f"{result_set[0]['version']}_{result_set[0]['name']}"
        except psycopg.errors.UndefinedTable:  # type: ignore[unresolved-attribute]
            # It's been observed that supabase will create the schema_migrations
            # table lazily whenever the first migration file is run. So it's valid
            # that the table may not exist yet.
            return None
