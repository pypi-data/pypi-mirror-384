from robot.parsing.model.statements import KeywordCall
from robotidy.transformers import Transformer

def is_same_keyword(first: str, second: str) -> bool: ...
def get_normalized_keyword(keyword: str) -> str: ...

OLD_KW_NAME: str
OLD_KW_NAME_WITH_LIB: str

class NetworkIdle(Transformer):
    def visit_KeywordCall(self, node: KeywordCall): ...
