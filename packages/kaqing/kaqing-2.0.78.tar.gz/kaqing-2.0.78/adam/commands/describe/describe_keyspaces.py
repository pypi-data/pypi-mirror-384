from adam.commands.command import Command
from adam.commands.cql.cql_utils import run_cql
from adam.pod_exec_result import PodExecResult
from adam.repl_state import ReplState, RequiredState
from adam.utils import log2

class DescribeKeyspaces(Command):
    COMMAND = 'describe keyspaces'

    # the singleton pattern
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'): cls.instance = super(DescribeKeyspaces, cls).__new__(cls)

        return cls.instance

    def __init__(self, successor: Command=None):
        super().__init__(successor)

    def required(self):
        return RequiredState.CLUSTER

    def command(self):
        return DescribeKeyspaces.COMMAND

    def run(self, cmd: str, state: ReplState):
        if not(args := self.args(cmd)):
            return super().run(cmd, state)

        state, args = self.apply_state(args, state)
        if not self.validate_state(state):
            return state

        _, all_nodes = Command.extract_options(args, '--all-nodes')

        r: list[PodExecResult] = run_cql(state, f'describe keyspaces', show_out=True, on_any=not all_nodes)
        if not r:
            log2('No pod is available')
            return 'no-pod'

        # do not continue to cql route
        return state

    def completion(self, state: ReplState) -> dict[str, any]:
        if state.sts:
            return super().completion(state, {'--all-nodes': None})

        return {}

    def help(self, _: ReplState) -> str:
        return f'{DescribeKeyspaces.COMMAND} [--all-nodes]\t describe Cassandra keyspaces'