import click

from adam.commands.command import Command
from .medusa_backup import MedusaBackup
from .medusa_restore import MedusaRestore
from .medusa_show_backupjobs import MedusaShowBackupJobs
from .medusa_show_restorejobs import MedusaShowRestoreJobs
from adam.repl_state import ReplState, RequiredState

class Medusa(Command):
    COMMAND = 'medusa'

    # the singleton pattern
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'): cls.instance = super(Medusa, cls).__new__(cls)

        return cls.instance

    def __init__(self, successor: Command=None):
        super().__init__(successor)

    def command(self):
        return Medusa.COMMAND

    def required(self):
        return RequiredState.CLUSTER

    def run(self, cmd: str, state: ReplState):
        if not(args := self.args(cmd)):
            return super().run(cmd, state)

        return super().intermediate_run(cmd, state, args, Medusa.cmd_list())

    def cmd_list():
        return [MedusaBackup(), MedusaRestore(), MedusaShowBackupJobs(), MedusaShowRestoreJobs()]

    def completion(self, state: ReplState):
        if state.sts:
            return super().completion(state)

        return {}

class MedusaCommandHelper(click.Command):
    def get_help(self, ctx: click.Context):
        Command.intermediate_help(super().get_help(ctx), Medusa.COMMAND, Medusa.cmd_list(), show_cluster_help=True)