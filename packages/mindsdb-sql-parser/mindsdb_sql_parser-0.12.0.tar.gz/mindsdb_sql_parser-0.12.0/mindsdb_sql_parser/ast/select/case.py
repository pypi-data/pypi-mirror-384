from mindsdb_sql_parser.ast.base import ASTNode
from mindsdb_sql_parser.utils import indent


class Case(ASTNode):
    def __init__(self, rules, default=None, arg=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # structure:
        # [
        #   [ condition, result ]
        # ]
        self.arg = arg
        self.rules = rules
        self.default = default

    def get_value(self, record):
        # TODO get value from record using "case" conditions
        ...

    def assert_arguments(self):
        pass

    def to_tree(self, *args, level=0, **kwargs):
        ind = indent(level)
        ind1 = indent(level+1)

        # rules
        rules_ar = []
        for condition, result in self.rules:
            rules_ar.append(
                f'{ind1}{condition.to_string()} => {result.to_string()}'
            )
        rules_str = '\n'.join(rules_ar)
        default_str = ''
        if self.default is not None:
            default_str = f'{ind1}default => {self.default.to_string()}\n'

        arg_str = ''
        if self.arg is not None:
            arg_str = f'{ind1}arg => {self.arg.to_string()}\n'

        return f'{ind}Case(\n' \
               f'{arg_str}'\
               f'{rules_str}\n' \
               f'{default_str}' \
               f'{ind})'

    def get_string(self, *args, alias=True, **kwargs):
        # rules
        rules_ar = []
        for condition, result in self.rules:
            rules_ar.append(
                f'WHEN {condition.to_string()} THEN {result.to_string()}'
            )
        rules_str = ' '.join(rules_ar)

        default_str = ''
        if self.default is not None:
            default_str = f' ELSE {self.default.to_string()}'

        arg_str = ''
        if self.arg is not None:
            arg_str = f'{self.arg.to_string()} '
        return f"CASE {arg_str}{rules_str}{default_str} END"
