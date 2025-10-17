import functools

from adam.commands.postgres.postgres_session import PostgresSession
from adam.config import Config

TestPG = [False]

@functools.lru_cache()
def pg_database_names(ns: str, pg_path: str):
    if TestPG[0]:
        return ['azops88_c3ai_c3']

    Config().wait_log('Inspecting Postgres Databases...')

    pg = PostgresSession(ns, pg_path)
    return [db['name'] for db in pg.databases() if db['owner'] == PostgresSession.default_owner()]

@functools.lru_cache()
def pg_table_names(ns: str, pg_path: str):
    if TestPG[0]:
        return ['C3_2_XYZ1']

    Config().wait_log('Inspecting Postgres Database...')
    return [table['name'] for table in pg_tables(ns, pg_path) if table['schema'] == PostgresSession.default_schema()]

def pg_tables(ns: str, pg_path: str):
    pg = PostgresSession(ns, pg_path)
    if pg.db:
        return pg.tables()

    return []