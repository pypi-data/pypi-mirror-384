import os
from lark import Lark, Tree, Token
from lark.exceptions import LarkError
import unittest

if os.environ.get("DEV_PBAT") == "1":
    base = os.path.dirname(__file__)
    path = os.path.join(base, "macro.lark")
    with open(path, encoding='utf-8') as f:
        GRAMMAR = f.read()
else:
    GRAMMAR = """
start: (ret_name "=")? fn_name ( "(" arg ("," arg)* ")" | "(" ")" )

name: NAME

ret_name: NAME

fn_name: NAME

?arg: parg | kwarg

parg: ARG | list

kwarg: ":" name ("=" parg)?

list: "[" parg ("," parg)* "]" | "[" "]"

NAME: /[a-z0-9_-]+/i

ARG: /([^",()\[\]:\s][^",()\[\]]*)|("[^"]*")/

WS: /[ \\t\\f\\r\\n]/+

%ignore WS    
"""

parser = Lark(GRAMMAR)

def _unquote(s):
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    return s

def find_data(tree, data, trace = False):
    if trace:
        print([child.data for child in tree.children])

    return [child for child in tree.children if hasattr(child, 'data') and child.data == data]

def find_tokens(tree, type):
    return [child for child in tree.children if isinstance(child, Token) and child.type == type]

def parse_kwarg(tree):
    name = None
    value = True
    for item in find_data(tree, 'name'):
        name = item.children[0].value.strip()
    for item in find_data(tree, 'parg'):
        value = parse_parg(item)
    return name, value

def parse_list(tree):
    return [parse_parg(item) for item in find_data(tree, 'parg')]

def parse_parg(tree):
    for item in find_tokens(tree, 'ARG'):
        return _unquote(item.value.strip())
    for item in find_data(tree, 'list'):
        return parse_list(item)

class ParseMacroError(Exception):
    pass

def parse_macro(s):

    try:
        tree = parser.parse(s)
    except LarkError as e:
        raise ParseMacroError(e)

    ret_name = None
    fn_name = None

    for item in find_data(tree, 'ret_name'):
        ret_name = item.children[0].value.strip()
    for item in find_data(tree, 'fn_name'):
        fn_name = item.children[0].value.strip()

    pargs = [parse_parg(item) for item in find_data(tree, 'parg')]
    kwargs = {}

    for item in find_data(tree, 'kwarg'):
        k, v = parse_kwarg(item)
        kwargs[k] = v

    return ret_name, fn_name, pargs, kwargs

class TestParse(unittest.TestCase):

    def test_ret(self):
        expected = "res", "fn", [], {}
        self.assertEqual(parse_macro('res = fn()'), expected)

    def test_kwargs_bool(self):
        expected = None, "fn", [], {"foo": True, "bar": True, "baz": True}
        self.assertEqual(parse_macro('fn ( :foo , :bar , :baz )'), expected)

    def test_kwargs_value(self):
        expected = None, "fn", [], {"foo": "one", "bar": "two", "baz": "three"}
        self.assertEqual(parse_macro('fn ( :foo = one , :bar = two , :baz = "three" )'), expected)
        
    def test_pargs(self):
        expected = None, "fn", ["foo","bar","baz"], {}
        self.assertEqual(parse_macro('fn ( foo , bar , "baz" )'), expected)

    def test_kwargs_pargs(self):
        expected = None, "fn", ["foo","baz"], {"bar": "three"}
        self.assertEqual(parse_macro('fn ( foo , :bar = "three" , "baz" )'), expected)

    def test_cyrillic(self):
        expected = None, "fn", ["раз", "два"], {"foo": "три"}
        self.assertEqual(parse_macro('fn ( раз , :foo = три , "два")'), expected)

    def test_whitespace(self):
        expected = None, "fn", ["foo", "bar"], {"baz": '1 \t\n \t\n2'}
        self.assertEqual(parse_macro('fn \t\n \t\n( \t\n \t\nfoo \t\n \t\n, \t\n \t\nbar \t\n \t\n, \t\n \t\n:baz \t\n \t\n= \t\n \t\n1 \t\n \t\n2 \t\n \t\n)'), expected)

    def test_par_and_br(self):
        expected = None, "fn", ["()", ["foo","[]", "bar"]], {"baz": "[]"}
        self.assertEqual(parse_macro('fn("()", :baz = "[]", [foo , "[]" , bar])'), expected)

if __name__ == '__main__':
    unittest.main()