from typing import Callable, Iterable
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
import sqlparse
from sqlparse.sql import Statement

from adam.sql.state_machine import StateMachine, StateTo
from adam.sql.term_completer import TermCompleter

__all__ = [
    "SqlCompleter",
]

DML_COMPLETER = TermCompleter(['select', 'insert', 'delete', 'update'])

class SqlCompleter(Completer):
    def __init__(self, tables: Callable[[], list[str]], dml: str = None, debug = False):
        super().__init__()
        self.dml = dml
        self.tables = tables
        self.debug = debug
        self.machine = StateMachine(debug=self.debug)

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        text = document.text_before_cursor.lstrip()
        state = ''
        if self.dml:
            state = f'{self.dml}_'
            text = f'{self.dml} {text}'

        completer: Completer = None
        stmts = sqlparse.parse(text)
        if not stmts:
            completer = DML_COMPLETER
        else:
            statement: Statement = stmts[0]
            state: StateTo = self.machine.traverse_tokens(statement.tokens, StateTo(state))
            if self.debug:
                print('\n  =>', state.to_s if isinstance(state, StateTo) else '')

            if not state or not state.to_s:
                completer = DML_COMPLETER

            if state and state.to_s in self.machine.suggestions:
                terms = []

                for word in self.machine.suggestions[state.to_s].strip(' ').split(','):
                    if word == 'tables':
                        terms.extend(self.tables())
                    elif word == 'single':
                        terms.append("'")
                    elif word == 'comma':
                        terms.append(",")
                    else:
                        terms.append(word)

                if terms:
                    completer = TermCompleter(terms)

        if completer:
            for c in completer.get_completions(document, complete_event):
                yield c

    def completions(table_names: Callable[[], list[str]]):
        return {
            'delete': SqlCompleter(table_names, 'delete'),
            'insert': SqlCompleter(table_names, 'insert'),
            'select': SqlCompleter(table_names, 'select'),
            'update': SqlCompleter(table_names, 'update'),
        }