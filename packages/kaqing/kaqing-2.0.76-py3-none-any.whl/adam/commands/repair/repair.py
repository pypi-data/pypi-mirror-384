import click

from adam.commands.command import Command
from .repair_run import RepairRun
from .repair_scan import RepairScan
from .repair_stop import RepairStop
from .repair_log import RepairLog
from adam.repl_state import ReplState, RequiredState

class Repair(Command):
    COMMAND = 'repair'

    # the singleton pattern
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'): cls.instance = super(Repair, cls).__new__(cls)

        return cls.instance

    def __init__(self, successor: Command=None):
        super().__init__(successor)

    def command(self):
        return Repair.COMMAND

    def required(self):
        return RequiredState.CLUSTER

    def run(self, cmd: str, state: ReplState):
        if not(args := self.args(cmd)):
            return super().run(cmd, state)

        return super().intermediate_run(cmd, state, args, Repair.cmd_list())

    def cmd_list():
        return [RepairRun(), RepairScan(), RepairStop(), RepairLog()]

    def completion(self, state: ReplState):
        if state.sts:
            return super().completion(state)
        return {}

class RepairCommandHelper(click.Command):
    def get_help(self, ctx: click.Context):
        Command.intermediate_help(super().get_help(ctx), Repair.COMMAND, Repair.cmd_list(), show_cluster_help=True)