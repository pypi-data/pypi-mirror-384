from adam.commands.command import Command
from adam.commands.cql.cql_utils import run_cql, table_names
from adam.pod_exec_result import PodExecResult
from adam.repl_state import ReplState, RequiredState
from adam.utils import log2

class DescribeTable(Command):
    COMMAND = 'describe table'

    # the singleton pattern
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'): cls.instance = super(DescribeTable, cls).__new__(cls)

        return cls.instance

    def __init__(self, successor: Command=None):
        super().__init__(successor)

    def required(self):
        return RequiredState.CLUSTER

    def command(self):
        return DescribeTable.COMMAND

    def run(self, cmd: str, state: ReplState):
        if not(args := self.args(cmd)):
            return super().run(cmd, state)

        state, args = self.apply_state(args, state)
        if not self.validate_state(state):
            return state

        args, all_nodes = Command.extract_options(args, '--all-nodes')

        if not args:
            if state.in_repl:
                log2('Please enter table name')
            else:
                log2('* table name is missing.')
                log2()
                Command.display_help()

            return 'missing-table'

        r: list[PodExecResult] = run_cql(state, f'describe table {args[0]}', show_out=True, on_any=not all_nodes)
        if not r:
            log2('No pod is available')
            return 'no-pod'

        # do not continue to cql route
        return state

    def completion(self, state: ReplState) -> dict[str, any]:
        if state.sts:
            return super().completion(state, {t: {'--all-nodes': None} for t in table_names(state)})

        return {}

    def help(self, _: ReplState) -> str:
        return f'{DescribeTable.COMMAND} <table-name> [--all-nodes]\t describe Cassandra table'