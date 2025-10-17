from abc import abstractmethod
import copy
import subprocess
import sys

from adam.commands.command_helpers import ClusterCommandHelper
from adam.repl_state import ReplState, RequiredState
from adam.utils import lines_to_tabular, log, log2

repl_cmds: list['Command'] = []

class Command:
    """Abstract base class for commands"""
    def __init__(self, successor: 'Command'=None):
        if not hasattr(self, '_successor'):
            self._successor = successor

    @abstractmethod
    def command(self) -> str:
        pass

    # The chain of responsibility pattern
    # Do not do child of child!!!
    @abstractmethod
    def run(self, cmd: str, state: ReplState):
        if self._successor:
            return self._successor.run(cmd, state)

        return None

    def completion(self, _: ReplState, leaf: dict[str, any] = None) -> dict[str, any]:
        # COMMAND = 'reaper activate schedule'
        d = leaf
        for t in reversed(self.command().split(' ')):
            d = {t: d}

        return d

    def required(self) -> RequiredState:
        return None

    def validate_state(self, state: ReplState, pg_required: RequiredState = None, app_required: RequiredState = None):
        return state.validate(self.required(), pg_required=pg_required, app_required=app_required)

    def help(self, _: ReplState) -> str:
        return None

    def args(self, cmd: str):
        a = list(filter(None, cmd.split(' ')))
        spec = self.command_tokens()
        if spec != a[:len(spec)]:
            return None

        return a

    def apply_state(self, args: list[str], state: ReplState, resolve_pg = True) -> tuple[ReplState, list[str]]:
        return state.apply_args(args, cmd=self.command_tokens(), resolve_pg=resolve_pg)

    def command_tokens(self):
        return self.command().split(' ')

    # build a chain-of-responsibility chain
    def chain(cl: list['Command']):
        global repl_cmds
        repl_cmds.extend(cl)

        cmds = cl[0]
        cmd = cmds
        for successor in cl[1:]:
            cmd._successor = successor
            cmd = successor

        return cmds

    def command_to_completion(self):
        # COMMAND = 'reaper activate schedule'
        d = None
        for t in reversed(self.command().split(' ')):
            d = {t: d}

        return d

    def display_help():
        args = copy.copy(sys.argv)
        args.extend(['--help'])
        subprocess.run(args)

    def extract_options(args: list[str], names: list[str]):
        found: list[str] = []

        new_args: list[str] = []
        for arg in args:
            if arg in names:
                found.append(arg)
            else:
                new_args.append(arg)

        return new_args, found

    def print_chain(cmd: 'Command'):
        print(f'{cmd.command()}', end = '')
        while s := cmd._successor:
            print(f'-> {s.command()}', end = '')
            cmd = s
        print()

    def intermediate_run(self, cmd: str, state: ReplState, args: list[str], cmds: list['Command'], separator='\t'):
        state, _ = self.apply_state(args, state)

        if state.in_repl:
            log(lines_to_tabular([c.help(state) for c in cmds], separator=separator))

            return 'command-missing'
        else:
            # head with the Chain of Responsibility pattern
            cmds = Command.chain(cmds)
            if not cmds.run(cmd, state):
                log2('* Command is missing.')
                Command.display_help()

        return state

    def intermediate_help(super_help: str, cmd: str, cmd_list: list['Command'], separator='\t', show_cluster_help=False):
        log(super_help)
        log()
        log('Sub-Commands:')

        log(lines_to_tabular([c.help(ReplState()).replace(f'{cmd} ', '  ', 1) for c in cmd_list], separator=separator))
        if show_cluster_help:
            log()
            ClusterCommandHelper.cluster_help()