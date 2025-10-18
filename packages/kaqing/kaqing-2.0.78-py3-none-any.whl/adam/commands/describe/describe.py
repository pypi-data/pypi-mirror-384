import click

from adam.commands.command import Command
from adam.commands.describe.describe_keyspace import DescribeKeyspace
from adam.commands.describe.describe_keyspaces import DescribeKeyspaces
from adam.commands.describe.describe_table import DescribeTable
from adam.commands.describe.describe_tables import DescribeTables
from adam.repl_state import ReplState, RequiredState

class Describe(Command):
    COMMAND = 'describe'
    reaper_login = None

    # the singleton pattern
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'): cls.instance = super(Describe, cls).__new__(cls)

        return cls.instance

    def __init__(self, successor: Command=None):
        super().__init__(successor)

    def required(self):
        return RequiredState.CLUSTER

    def command(self):
        return Describe.COMMAND

    def run(self, cmd: str, state: ReplState):
        if not(args := self.args(cmd)):
            return super().run(cmd, state)

        return super().intermediate_run(cmd, state, args, Describe.cmd_list())

    def cmd_list():
        return [DescribeKeyspace(), DescribeKeyspaces(), DescribeTable(), DescribeTables()]

    def completion(self, state: ReplState):
        if state.sts:
            return super().completion(state)

        return {}

class DescribeCommandHelper(click.Command):
    def get_help(self, ctx: click.Context):
        Command.intermediate_help(super().get_help(ctx), Describe.COMMAND, Describe.cmd_list(), show_cluster_help=True)