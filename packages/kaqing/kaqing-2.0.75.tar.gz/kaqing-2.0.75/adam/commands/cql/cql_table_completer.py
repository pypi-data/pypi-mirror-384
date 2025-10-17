from adam.sql.term_completer import TermCompleter

class CqlTableNameCompleter(TermCompleter):
    def __init__(self, tables: list[str], ignore_case: bool = True):
        super().__init__(tables, ignore_case=ignore_case)

    def __repr__(self) -> str:
        return "CqlTableCompleter(%r)" % (len(self.words))