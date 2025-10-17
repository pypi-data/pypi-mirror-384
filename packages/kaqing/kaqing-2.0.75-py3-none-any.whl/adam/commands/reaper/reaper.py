import click

from adam.commands.command import Command
from .reaper_forward import ReaperForward
from .reaper_forward_stop import ReaperForwardStop
from .reaper_restart import ReaperRestart
from .reaper_run_abort import ReaperRunAbort
from .reaper_runs import ReaperRuns
from .reaper_runs_abort import ReaperRunsAbort
from .reaper_schedule_activate import ReaperScheduleActivate
from .reaper_schedule_start import ReaperScheduleStart
from .reaper_schedule_stop import ReaperScheduleStop
from .reaper_schedules import ReaperSchedules
from .reaper_status import ReaperStatus
from adam.repl_state import ReplState, RequiredState

class Reaper(Command):
    COMMAND = 'reaper'
    reaper_login = None

    # the singleton pattern
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'): cls.instance = super(Reaper, cls).__new__(cls)

        return cls.instance

    def __init__(self, successor: Command=None):
        super().__init__(successor)

    def command(self):
        return Reaper.COMMAND

    def required(self):
        return RequiredState.CLUSTER

    def run(self, cmd: str, state: ReplState):
        if not(args := self.args(cmd)):
            return super().run(cmd, state)

        return super().intermediate_run(cmd, state, args, Reaper.cmd_list())

    def cmd_list():
        return [ReaperSchedules(), ReaperScheduleStop(), ReaperScheduleActivate(), ReaperScheduleStart(),
                ReaperForwardStop(), ReaperForward(), ReaperRunAbort(), ReaperRunsAbort(), ReaperRestart(),
                ReaperRuns(), ReaperStatus()]

    def completion(self, state: ReplState):
        if state.sts:
            return super().completion(state)

        return {}

class ReaperCommandHelper(click.Command):
    def get_help(self, ctx: click.Context):
        Command.intermediate_help(super().get_help(ctx), Reaper.COMMAND, Reaper.cmd_list(), show_cluster_help=True)