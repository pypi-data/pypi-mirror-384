import functools

from adam.commands.command import Command
from adam.commands.cql.cql_table_completer import CqlTableNameCompleter
from adam.commands.cql.cql_utils import run_cql, table_names, tables
from adam.commands.postgres.postgres_session import PostgresSession
from adam.commands.postgres.psql_table_completer import PsqlTableNameCompleter
from adam.config import Config
from adam.repl_state import ReplState, RequiredState
from adam.utils import lines_to_tabular, log, log2

class PreviewTable(Command):
    COMMAND = 'preview'

    # the singleton pattern
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'): cls.instance = super(PreviewTable, cls).__new__(cls)

        return cls.instance

    def __init__(self, successor: Command=None):
        super().__init__(successor)

    def command(self):
        return PreviewTable.COMMAND

    def required(self):
        return RequiredState.CLUSTER_OR_POD

    def run(self, cmd: str, state: ReplState):
        if not(args := self.args(cmd)):
            return super().run(cmd, state)

        state, args = self.apply_state(args, state)
        if state.device == ReplState.P:
            if not self.validate_state(state, RequiredState.PG_DATABASE):
                return state
        else:
            if not self.validate_state(state):
                return state

        if not args:
            def show_tables():
                if state.device == ReplState.P:
                    pg = PostgresSession(state.namespace, state.pg_path)
                    lines = [db["name"] for db in pg.tables() if db["schema"] == PostgresSession.default_schema()]
                    log(lines_to_tabular(lines, separator=','))
                else:
                    run_cql(state, f'describe tables', show_out=True)

            if state.in_repl:
                log2('Table is required.')
                log2()
                log2('Tables:')
                show_tables()
            else:
                log2('* Table is missing.')
                show_tables()

                Command.display_help()

            return 'command-missing'

        table = args[0]

        rows = Config().get('preview.rows', 10)
        if state.device == ReplState.P:
            PostgresSession(state.namespace, state.pg_path).run_sql(f'select * from {table} limit {rows}')
        else:
            run_cql(state, f'select * from {table} limit {rows}', show_out=True, use_single_quotes=True)

        return state

    def completion(self, state: ReplState):
        if state.device == ReplState.P:
            return {PreviewTable.COMMAND: PsqlTableNameCompleter(state.namespace, state.pg_path)}
        elif state.sts:
            return {PreviewTable.COMMAND: CqlTableNameCompleter(table_names(state))}

        return {}

    def help(self, _: ReplState):
        return f'{PreviewTable.COMMAND} TABLE\t preview table'

    @functools.lru_cache()
    def cql_tables(state: ReplState):
        if state.pod:
            return tables(state)

        return tables(state, on_any=True)