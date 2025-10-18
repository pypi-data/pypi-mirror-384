import click

from adam.commands.command import Command
from adam.commands.deploy.deploy_pg_agent import DeployPgAgent
from adam.commands.deploy.deploy_pod import DeployPod
from .deploy_frontend import DeployFrontend
from adam.repl_state import ReplState

class Deploy(Command):
    COMMAND = 'deploy'
    reaper_login = None

    # the singleton pattern
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'): cls.instance = super(Deploy, cls).__new__(cls)

        return cls.instance

    def __init__(self, successor: Command=None):
        super().__init__(successor)

    def command(self):
        return Deploy.COMMAND

    def run(self, cmd: str, state: ReplState):
        if not(args := self.args(cmd)):
            return super().run(cmd, state)

        return super().intermediate_run(cmd, state, args, Deploy.cmd_list())

    def cmd_list():
        return [DeployFrontend(), DeployPod(), DeployPgAgent()]

    def completion(self, state: ReplState):
        if state.sts:
            return super().completion(state)

        return {}

class DeployCommandHelper(click.Command):
    def get_help(self, ctx: click.Context):
        Command.intermediate_help(super().get_help(ctx), Deploy.COMMAND, Deploy.cmd_list())