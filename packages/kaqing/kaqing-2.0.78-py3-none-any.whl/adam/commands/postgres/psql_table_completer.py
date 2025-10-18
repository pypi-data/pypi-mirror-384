from adam.commands.postgres.postgres_utils import pg_table_names
from adam.sql.term_completer import TermCompleter

class PsqlTableNameCompleter(TermCompleter):
    def __init__(self, namespace: str, pg_path: str, ignore_case: bool = True):
        super().__init__(pg_table_names(namespace, pg_path), ignore_case=ignore_case)
        self.namespace = namespace
        self.pg_path = pg_path

    def __repr__(self) -> str:
        return "PsqlTableCompleter(%r, pg_path=%r)" % (self.namespace, self.pg_path)