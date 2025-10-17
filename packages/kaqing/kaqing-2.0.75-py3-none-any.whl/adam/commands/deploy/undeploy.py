import click

from adam.commands.command import Command
from adam.commands.deploy.undeploy_frontend import UndeployFrontend
from adam.commands.deploy.undeploy_pg_agent import UndeployPgAgent
from adam.commands.deploy.undeploy_pod import UndeployPod
from adam.repl_state import ReplState

class Undeploy(Command):
    COMMAND = 'undeploy'
    reaper_login = None

    # the singleton pattern
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'): cls.instance = super(Undeploy, cls).__new__(cls)

        return cls.instance

    def __init__(self, successor: Command=None):
        super().__init__(successor)

    def command(self):
        return Undeploy.COMMAND

    def run(self, cmd: str, state: ReplState):
        if not(args := self.args(cmd)):
            return super().run(cmd, state)

        return super().intermediate_run(cmd, state, args, Undeploy.cmd_list())

    def cmd_list():
        return [UndeployFrontend(), UndeployPod(), UndeployPgAgent()]

    def completion(self, state: ReplState):
        if state.sts:
            return super().completion(state)

        return {}

class UndeployCommandHelper(click.Command):
    def get_help(self, ctx: click.Context):
        Command.intermediate_help(super().get_help(ctx), Undeploy.COMMAND, Undeploy.cmd_list())