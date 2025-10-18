from adam.commands.postgres.postgres_utils import pg_table_names
from adam.sql.sql_completer import SqlCompleter

def psql_completions(ns: str, pg_path: str):
    return {
        '\h': None,
        '\d': None,
        '\dt': None,
        '\du': None
    } | SqlCompleter.completions(lambda: pg_table_names(ns, pg_path))