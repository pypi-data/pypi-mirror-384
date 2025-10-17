import click

from adam.commands.command import Command
from adam.commands.medusa.medusa_show_backupjobs import MedusaShowBackupJobs
from adam.commands.medusa.medusa_show_restorejobs import MedusaShowRestoreJobs
from adam.commands.show.show_app_actions import ShowAppActions
from adam.commands.show.show_app_queues import ShowAppQueues
from adam.commands.show.show_login import ShowLogin
from .show_params import ShowParams
from .show_app_id import ShowAppId
from .show_cassandra_status import ShowCassandraStatus
from .show_cassandra_version import ShowCassandraVersion
from .show_commands import ShowKubectlCommands
from .show_processes import ShowProcesses
from .show_repairs import ShowRepairs
from .show_storage import ShowStorage
from .show_adam import ShowAdam
from adam.repl_state import ReplState

class Show(Command):
    COMMAND = 'show'

    # the singleton pattern
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'): cls.instance = super(Show, cls).__new__(cls)

        return cls.instance

    def __init__(self, successor: Command=None):
        super().__init__(successor)

    def command(self):
        return Show.COMMAND

    def run(self, cmd: str, state: ReplState):
        if not(args := self.args(cmd)):
            return super().run(cmd, state)

        return super().intermediate_run(cmd, state, args, Show.cmd_list())

    def cmd_list():
        return [ShowAppActions(), ShowAppId(), ShowAppQueues(), ShowLogin(), ShowKubectlCommands(),
                ShowParams(), ShowProcesses(), ShowRepairs(), ShowStorage(), ShowAdam(),
                ShowCassandraStatus(), ShowCassandraVersion(), MedusaShowRestoreJobs(), MedusaShowBackupJobs()]

    def completion(self, state: ReplState):
        return super().completion(state)

class ShowCommandHelper(click.Command):
    def get_help(self, ctx: click.Context):
        Command.intermediate_help(super().get_help(ctx), Show.COMMAND, Show.cmd_list(), show_cluster_help=True)