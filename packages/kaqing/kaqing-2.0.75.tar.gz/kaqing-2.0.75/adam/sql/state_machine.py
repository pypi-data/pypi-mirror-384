# <select_statement> ::= SELECT <select_list>
#                      FROM <table_expression>
#                      [WHERE <search_condition>]
#                      [<group_by_clause>]
#                      [<having_clause>]
#                      [<order_by_clause>]
#                      [<limit_clause>]

# <search_condition> ::= <boolean_term>
#                      | <search_condition> OR <boolean_term>

# <boolean_term> ::= <boolean_factor>
#                  | <boolean_term> AND <boolean_factor>

# <boolean_factor> ::= [NOT] <predicate>
#                    | ([NOT] <search_condition>)

# <predicate> ::= <comparison_predicate>
#               | <between_predicate>
#               | <in_predicate>
#               | <like_predicate>
#               | <null_predicate>
#               | <exists_predicate>
#               | <quantified_predicate>
#               | <unique_predicate>
#               | <match_predicate>
#               | <overlaps_predicate>
#               | <distinct_predicate>
#               | <member_predicate>
#               | <submultiset_predicate>
#               | <set_predicate>

# <comparison_predicate> ::= <row_value_expression> <comparison_operator> <row_value_expression>
# <comparison_operator> ::= '=' | '<>' | '<' | '<=' | '>' | '>='

# <row_value_expression> ::= <value_expression>
#                          | (<value_expression> [ { <comma> <value_expression> }... ])

# <value_expression> ::= <numeric_value_expression>
#                      | <string_value_expression>
#                      | <datetime_value_expression>
#                      | <interval_value_expression>
#                      | <boolean_value_expression>
#                      | <user_defined_type_value_expression>
#                      | <reference_value_expression>
#                      | <collection_value_expression>
#                      | <row_value_constructor>
#                      | <case_expression>
#                      | <cast_expression>
#                      | <subquery>
#                      | NULL
#                      | DEFAULT
#                      | <identifier>
#                      | <literal>

# <insert_statement> ::= INSERT INTO <table_name> [ ( <column_list> ) ]
#                        VALUES ( <value_list> )
#                      | INSERT INTO <table_name> [ ( <column_list> ) ]
#                        <query_expression>

# <table_name> ::= <identifier>

# <column_list> ::= <column_name> [ , <column_list> ]

# <column_name> ::= <identifier>

# <value_list> ::= <expression> [ , <value_list> ]

# <query_expression> ::= SELECT <select_list> FROM <table_reference_list> [ WHERE <search_condition> ] [ GROUP BY <grouping_column_list> ] [ HAVING <search_condition> ] [ ORDER BY <sort_specification_list> ]

# <update_statement> ::= UPDATE <table_name>
#                        SET <set_clause_list>
#                        [WHERE <search_condition>]

# <set_clause_list> ::= <set_clause> { , <set_clause> }

# <set_clause> ::= <column_name> = <update_value>

# <update_value> ::= <expression> | NULL | DEFAULT

# <search_condition> ::= <boolean_expression>

# <delete_statement> ::= DELETE FROM <table_name> [ WHERE <search_condition> ]

# <table_name> ::= <identifier>

# <search_condition> ::= <boolean_expression>

# <boolean_expression> ::= <predicate>
#                      | <boolean_expression> AND <predicate>
#                      | <boolean_expression> OR <predicate>
#                      | NOT <predicate>
#                      | ( <boolean_expression> )

# <predicate> ::= <expression> <comparison_operator> <expression>
#              | <expression> IS NULL
#              | <expression> IS NOT NULL
#              | <expression> LIKE <pattern> [ ESCAPE <escape_character> ]
#              | <expression> IN ( <expression_list> )
#              | EXISTS ( <select_statement> )
#              | ... (other predicates)

# <comparison_operator> ::= = | <> | != | > | < | >= | <=

# <expression> ::= <literal>
#               | <column_name>
#               | <function_call>
#               | ( <expression> )
#               | <expression> <arithmetic_operator> <expression>
#               | ... (other expressions)

# <literal> ::= <numeric_literal> | <string_literal> | <boolean_literal> | <date_literal> | ...

# <column_name> ::= <identifier>

# <identifier> ::= <letter> { <letter> | <digit> | _ }...

# <pattern> ::= <string_literal>

# <escape_character> ::= <string_literal> (single character)

# <expression_list> ::= <expression> { , <expression> }...

from sqlparse.sql import Token
from sqlparse import tokens as T

__all__ = [
    "StateMachine",
]

SPEC = [
    '                                > select           > select',
    'select_                         > name|*           > select_a                                ^ *',
    'select_a                        > ,                > select_a_comma_',
    'select_a_comma_                 > name|*           > select_a                                ^ *',
    'select_a_                       > from             > select_from                             ^ from',
    'select_from_                    > name             > select_from_x                           ^ (select,tables',
    '-                               > (                > select_from_lp_',
    '-                               < )                > select_from_sq',
    'select_from_lp_                 > select           > select',
    'select_from_x                   > ,                > select_from_x_comma_',
    'select_from_sq_                 > as               > select_from_x_as                        ^ as',
    'select_from_x_comma_            > name             > select_from_x                           ^ tables',
    'select_from_x_                                                                               ^ as,where,inner join,left outer join,right outer join,full outer join,group by,limit',
    'select_from_x_as_x_             > ,                > select_from_x_comma_                    ^ where,inner join,left outer join,right outer join,full outer join,group by,limit',
    '-                               > as               > select_from_x_as',
    '-                               > where            > select_where',
    '-                               > limit            > select_where_sc_limit',
    '-                               > group            > select_group',
    '-                               > group by         > select_group_by',
    '-                               > inner            > select_from_x_inner',
    '-                               > inner join       > select_join',
    '-                               > left             > select_from_x_left',
    '-                               > left join        > select_join',
    '-                               > left outer join  > select_join',
    '-                               > right            > select_from_x_right',
    '-                               > right join       > select_join',
    '-                               > right outer join > select_join',
    '-                               > full             > select_from_x_full',
    '-                               > full outer join  > select_join',
    'select_from_x_as_               > name             > select_from_x_as_x                      ^ x,y,z',
    'select_from_x_as_x              > ,                > select_from_x_as_x_comma_',
    'select_from_x_as_x_comma_       > name             > select_from_x                           ^ tables',
    'select_where_                   > name             > select_where_a                          ^ id,x.,y.,z.',
    'select_where_a                  > comparison       > select_where_a_op                       ^ =,<,<=,>,>=,<>,like,not,in',
    'select_where_a_                 > comparison       > select_where_a_op                       ^ =,<,<=,>,>=,<>,like,not,in',
    '-                               > not              > select_where_a_not',
    '-                               > in               > select_where_a_in',
    'select_where_a_not_             > comparison       > select_where_a_not_op                   ^ like,in',
    '-                               > in               > select_where_a_in',
    'select_where_a_in               > (                > select_where_a_in_lp_                   ^ (',
    '-                               < )                > select_where_sc',
    'select_where_a_in_lp_           > name|single|num  > select_where_a_in_lp_a                  ^ single,select',
    '-                               > select           > select_where_a_in_lp_select',
    'select_where_a_in_lp_select_    > name             > select_a                                ^ id',
    'select_where_a_in_lp_a          > ,                > select_where_a_in_lp_a_comma_           ^ comma,)',
    'select_where_a_in_lp_a_comma_   > name|single|num  > select_where_a_in_lp_a                  ^ single',
    'select_where_a_not_op           > name|single|num  > select_where_sc                         ^ single',
    'select_where_a_op               > name|single|num  > select_where_sc                         ^ single',
    'select_where_sc_                > and|or           > select_where                            ^ and,or,group by,limit',
    '-                               > group            > select_group',
    '-                               > group by         > select_group_by',
    '-                               > limit            > select_where_sc_limit',
    'select_group_                   > by               > select_group_by                         ^ by',
    'select_group_by_                > name             > select_group_by_a                       ^ id,x.,y.,z.',
    'select_group_by_a               > ,                > select_group_by_a_comma_',
    'select_group_by_a_comma_        > name             > select_group_by_a                       ^ id,x.,y.,z.',
    'select_group_by_a_              > limit            > select_where_sc_limit                   ^ limit',
    'select_where_sc_limit_          > num              > select_where_sc_limit_num               ^ 1',
    'select_where_sc_limit_num_rp__  > as               > select_from_x_as                        ^ as',
    'select_where_x_inner_           > join             > select_join',
    'select_join_                    > name             > select_x_join_y                         ^ tables',
    'select_from_x_left_             > join             > select_join                             ^ outer join',
    '-                               > outer            > select_from_x_left_outer',
    'select_from_x_left_outer_       > join             > select_join                             ^ join',
    'select_from_x_right_            > join             > select_join                             ^ outer join',
    '-                               > outer            > select_from_x_right_outer',
    'select_from_x_right_outer_      > join             > select_join                             ^ join',
    'select_from_x_full_             > join             > select_join                             ^ outer join',
    '-                               > outer            > select_from_x_full_outer',
    'select_from_x_full_outer_       > join             > select_join                             ^ join',
    'select_x_join_y_                > as               > select_x_join_y_as                      ^ as,on',
    '-                               > on               > select_x_join_y_on                      ^ as,on',
    'select_x_join_y_as_             > name             > select_x_join_y_as_y                    ^ x,y,z',
    'select_x_join_y_as_y_           > on               > select_x_join_y_on                      ^ on',
    'select_x_join_y_on_             > name             > select_x_join_y_on_a                    ^ id,x.,y.,z.',
    'select_x_join_y_on_a            > comparison       > select_x_join_y_on_a_op                 ^ =',
    'select_x_join_y_on_a_op         > name             > select_x_join_y_on_a_op_b               ^ id,x.,y.,z.',
    'select_x_join_y_on_a_op_b       > _                > select_from_x_as_x_',


    '                                > insert           > insert',
    'insert_                         > into             > insert_into                             ^ into',
    'insert_into_                    > name             > insert_into_x                           ^ tables',
    'insert_into_x                   > (                > insert_into_x_lp_',
    'insert_into_x_                  > (                > insert_into_x_lp_                       ^ (,values(',
    '-                               > values           > insert_values',
    'insert_into_x_lp_               > name             > insert_into_x_lp_a                      ^ id',
    'insert_into_x_lp_a              > ,                > insert_into_x_lp_a_comma_',
    '-                               > )                > insert_into_x_lp_a_rp_',
    'insert_into_x_lp_a_comma_       > name             > insert_into_x_lp_a                      ^ id',
    'insert_into_x_lp_a_rp__         > values           > insert_values                           ^ values(,select',
    '-                               > select           > select',
    'insert_values                   > (                > insert_values_lp_',
    'insert_values_lp_               > name|single|num  > insert_values_lp_v                      ^ single',
    'insert_values_lp_v              > ,                > insert_values_lp_v_comma_',
    'insert_values_lp_v_comma_       > name|single|num  > insert_values_lp_v',


    '                                > update           > update',
    'update_                         > name             > update_x                                ^ tables',
    'update_x_                       > set              > update_set                              ^ set',
    'update_set_                     > name             > update_set_a                            ^ id',
    'update_set_a                    > comparison       > update_set_a_op',
    'update_set_a_op                 > name|single|num  > update_set_sc                           ^ single',
    'update_set_sc                   > ,                > update_set_sc_comma_',
    'update_set_sc_comma_            > name             > update_set_a                            ^ id',
    'update_set_sc_                  > ,                > update_set_sc_comma_                    ^ where',
    '-                               > where            > update_where',
    'update_where_                   > name             > update_where_a                          ^ id',
    'update_where_a                  > comparison       > update_where_a_op',
    'update_where_a_                 > comparison       > update_where_a_op                       ^ =,<,<=,>,>=,<>,like,not,in',
    '-                               > not              > update_where_a_not',
    '-                               > in               > update_where_a_in',
    'update_where_a_not_             > comparison       > update_where_a_not_op                   ^ like,in',
    '-                               > in               > update_where_a_in',
    'update_where_a_in               > (                > update_where_a_in_lp_                   ^ (',
    '-                               < )                > update_where_sc',
    'update_where_a_in_lp_           > name|single|num  > update_where_a_in_lp_a                  ^ single,select',
    '-                               > select           > update_where_a_in_lp_select',
    'update_where_a_in_lp_select_    > name             > select_a                                ^ id',
    'update_where_a_in_lp_a          > ,                > update_where_a_in_lp_a_comma_           ^ comma,)',
    'update_where_a_in_lp_a_comma_   > name|single|num  > update_where_a_in_lp_a                  ^ single',
    'update_where_a_not_op           > name|single|num  > update_where_sc                         ^ single',
    'update_where_a_op               > name|single|num  > update_where_sc                         ^ single',
    'update_where_sc_                > and|or           > update_where                            ^ and,or',


    '                                > delete           > delete',
    'delete_                         > from             > delete_from                             ^ from',
    'delete_from_                    > name             > delete_from_x                           ^ tables',
    'delete_from_x_                  > where            > update_where                            ^ where',
]

KEYWORDS = [
    'select', 'from', 'as', 'not', 'in', 'where',
    'and', 'or', 'group', 'by', 'group by', 'limit',
    'inner join', 'on', 'left', 'right', 'full', 'outer', 'left outer join',
    'left join', 'right outer join', 'right join', 'full join', 'full outer join',
    'insert', 'into', 'values',
    'update', 'where', 'set',
    'delete'
]

class StateTo:
    def __init__(self, to_s: str, comeback_token: str = None, comeback_state: str = None):
        self.to_s = to_s
        self.comeback_token = comeback_token
        self.comeback_state = comeback_state

    def __str__(self):
        return f'{self.to_s} comeback[{self.comeback_token} {self.comeback_state}]'

class StateMachine:
    def __init__(self, indent=0, lp_level = 0, debug = False):
        self.states: dict[str, StateTo] = {}
        self.suggestions: dict[str, str] = {}

        self.indent = indent
        self.lp_level = lp_level
        self.comebacks: dict[int, str] = {}
        self.debug = debug

        from_ss_to_add = []
        from_ss = ['']
        words: str = None
        for l in SPEC:
            t_and_w = l.split('^')
            if len(t_and_w) > 1:
                words = t_and_w[1]
            else:
                words = None

            tks = t_and_w[0].strip(' ').split('>')
            if not l.startswith('-'):
                if words:
                    self.suggestions[tks[0].strip(' ')] = words

                if len(tks) == 1:
                    from_ss_to_add.append(tks[0].strip(' '))
                    continue

                from_ss = []
                from_ss.extend(from_ss_to_add)
                from_ss_to_add = []
                from_ss.append(tks[0].strip(' '))

            self.add_transitions(from_ss, tks)

    def add_transitions(self, from_ss: list[str], tks: list[str]):
        token = tks[1].strip(' ')
        if len(tks) > 2:
            to_s = tks[2].strip(' ')
            for from_s in from_ss:
                self.add_whitespace_transition(from_s, to_s)
                self.add_transition(from_s, token, to_s)
        elif '<' in tks[0]:
            from_and_token = tks[0].split('<')
            if len(from_and_token) > 1:
                for from_s in from_ss:
                    self.add_comeback_transition(from_s, from_and_token[1], tks[1].strip(' '))

    def add_whitespace_transition(self, from_s: str, to_s: str):
        # add whitespace transition if a state with trailing whitespace is found from from states, for example, select > _ > select_
        if from_s.endswith('_') and not from_s.endswith('_comma_') and not from_s.endswith('_lp_') and not from_s.endswith('_rp_'):
            if self.debug:
                print(f'{from_s[:-1]} > _ = {to_s}')
            self.states[f'{from_s[:-1]} > _'] = StateTo(from_s)

    def add_transition(self, from_s: str, token: str, to_s: str):
        tokens = [token]
        if '|' in token:
            tokens = token.split('|')

        for t in tokens:
            if self.debug:
                print(f'{from_s} > {t} = {to_s}')
            self.states[f'{from_s} > {t}'] = StateTo(to_s)

    def add_comeback_transition(self, from_s: str, token: str, to_s: str):
        key = f'{from_s} > ('
        orig = self.states[key]
        if not orig:
            raise Exception(f'from state not found for {key}')

        orig.comeback_token = token
        orig.comeback_state = to_s
        if self.debug:
            print(f'{from_s} > ) = {to_s}')
        self.states[key] = orig

    def traverse_tokens(self, tokens: list[Token], state: StateTo = StateTo('')):
        def handle_opening_parenthesis():
            if f'{state.to_s} > {it}' in self.states:
                state_test = self.states[f'{state.to_s} > {it}']
                if state_test.comeback_token:
                    self.comebacks[self.lp_level] = state_test.comeback_state

        def handle_closing_parenthesis():
            if self.lp_level in self.comebacks:
                try:
                    return StateTo(self.comebacks[self.lp_level])
                finally:
                    del self.comebacks[self.lp_level]

            return None

        for token in tokens:
            if self.debug:
                if token.ttype == T.Whitespace:
                    print('_ ', end='')
                elif token.ttype in [T.DML, T.Wildcard, T.Punctuation]:
                    print(f'{token.value} ', end='')
                elif token.ttype:
                    tks = str(token.ttype).split('.')
                    typ = tks[len(tks) - 1]
                    if ' ' in token.value:
                        print(f'"{token.value}:{typ}" ', end='')
                    else:
                        print(f'{token.value}:{typ} ', end='')
            # print("  " * self.indent + f"Token: {token.value}, Type: {token.ttype}@{token.ttype.__class__}")

            if token.is_group:
                state = self.traverse_tokens(token.tokens, state)
            else:
                comeback_state = None

                it = ''
                if (t := token.value.lower()) in KEYWORDS:
                    it = t
                elif token.ttype == T.Text.Whitespace:
                    it = '_'
                elif token.ttype == T.Name:
                    it = 'name'
                elif token.ttype == T.Literal.String.Single:
                    it = 'single'
                elif token.ttype in [T.Literal.Number.Integer, T.Literal.Number.Float]:
                    it = 'num'
                elif token.ttype == T.Wildcard:
                    it = '*'
                elif token.ttype == T.Punctuation:
                    it = token.value

                    if it == '(':
                        handle_opening_parenthesis()
                        self.lp_level += 1
                    elif it == ')':
                        self.lp_level -= 1
                        comeback_state = handle_closing_parenthesis()

                elif token.ttype == T.Operator.Comparison:
                    it = 'comparison'

                try:
                    # print(f'\n{state.to_s} > {it} > ', end='')
                    if comeback_state:
                        state = comeback_state
                    else:
                        state = self.states[f'{state.to_s} > {it}']
                    # print(state)
                except:
                    pass
                    # print('error')

        return state