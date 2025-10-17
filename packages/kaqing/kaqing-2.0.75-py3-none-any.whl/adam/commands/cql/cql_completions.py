from adam.commands.cql.cql_utils import table_names
from adam.repl_state import ReplState
from adam.sql.sql_completer import SqlCompleter

def cql_completions(state: ReplState) -> dict[str, any]:
    return {
        'describe': {
            'keyspaces': None,
            'table': {t: None for t in table_names(state)},
            'tables': None},
    } | SqlCompleter.completions(lambda: table_names(state))