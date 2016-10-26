import ast
import re
import sys, inspect
import astor
from collections import OrderedDict

from tree import *

p_elif = re.compile(r'^elif\s?')
p_else = re.compile(r'^else\s?')
p_try = re.compile(r'^try\s?')
p_except = re.compile(r'^except\s?')
p_finally = re.compile(r'^finally\s?')
p_decorator = re.compile(r'^@.*')


ast_classes = dict()

# get all ast classes
for name, obj in inspect.getmembers(sys.modules['ast']):
    if inspect.isclass(obj):
        name = obj.__name__
        ast_classes[name] = obj


ast_node_black_list = {'ctx'}

valid_ast_leaf_nodes = {ast.Ellipsis, ast.And, ast.Or, ast.Add, ast.Sub}

ast_class_fields = {
    'FunctionDef': {
        'name': {
            'type': 'identifier',
            'is_list': False,
            'is_optional': False
        },
        'args': {
            'type': ast.arguments,
            'is_list': False,
            'is_optional': False
        },
        'body': {
            'type': ast.stmt,
            'is_list': True,
            'is_optional': False
        },
        'decorator_list': {
            'type': ast.expr,
            'is_list': True,
            'is_optional': False
        }
    },
    'ClassDef': {
        'name': {
            'type': ast.arguments,
            'is_list': False,
            'is_optional': False
        },
        'bases': {
            'type': ast.expr,
            'is_list': True,
            'is_optional': False
        },
        'body': {
            'type': ast.stmt,
            'is_list': True,
            'is_optional': False
        },
        'decorator_list': {
            'type': ast.expr,
            'is_list': True,
            'is_optional': False
        }
    },
    'Return': {
        'value': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': True
        },
    },
    'Delete': {
        'targets': {
            'type': ast.expr,
            'is_list': True,
            'is_optional': False
        },
    },
    'Assign': {
        'targets': {
            'type': ast.expr,
            'is_list': True,
            'is_optional': False
        },
        'value': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        }
    },
    'AugAssign': {
        'target': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
        'op': {
            'type': ast.operator,
            'is_list': False,
            'is_optional': False
        },
        'value': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        }
    },
    'Print': {
        'dest': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': True
        },
        'values': {
            'type': ast.expr,
            'is_list': True,
            'is_optional': False
        },
        'nl': {
            'type': 'bool',
            'is_list': False,
            'is_optional': False
        }
    },
    'For': {
        'target': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
        'iter': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
        'body': {
            'type': ast.stmt,
            'is_list': True,
            'is_optional': False
        },
        'orelse': {
            'type': ast.stmt,
            'is_list': True,
            'is_optional': False
        }
    },
    'While': {
        'test': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
        'body': {
            'type': ast.stmt,
            'is_list': True,
            'is_optional': False
        },
        'orelse': {
            'type': ast.stmt,
            'is_list': True,
            'is_optional': False
        },
    },
    'If': {
        'test': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
        'body': {
            'type': ast.stmt,
            'is_list': True,
            'is_optional': False
        },
        'orelse': {
            'type': ast.stmt,
            'is_list': True,
            'is_optional': False
        },
    },
    'With': {
        'context_expr': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
        'optional_vars': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': True
        },
        'body': {
            'type': ast.stmt,
            'is_list': True,
            'is_optional': False
        },
    },
    'Raise': {
        'type': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': True
        },
        'inst': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': True
        },
        'tback': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': True
        },
    },
    'TryExcept': {
        'body': {
            'type': ast.stmt,
            'is_list': True,
            'is_optional': False
        },
        'handlers': {
            'type': ast.excepthandler,
            'is_list': True,
            'is_optional': False
        },
        'orelse': {
            'type': ast.stmt,
            'is_list': True,
            'is_optional': False
        },
    },
    'TryFinally': {
        'body': {
            'type': ast.stmt,
            'is_list': True,
            'is_optional': False
        },
        'finalbody': {
            'type': ast.stmt,
            'is_list': True,
            'is_optional': False
        }
    },
    'Assert': {
        'test': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
        'msg': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': True
        }
    },
    'Import': {
        'names': {
            'type': ast.alias,
            'is_list': True,
            'is_optional': False
        }
    },
    'ImportFrom': {
        'module': {
            'type': 'identifier',
            'is_list': False,
            'is_optional': True
        },
        'names': {
            'type': ast.alias,
            'is_list': True,
            'is_optional': False
        },
        'level': {
            'type': 'int',
            'is_list': False,
            'is_optional': True
        }
    },
    'Exec': {
        'body': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
        'globals': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': True
        },
        'locals': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': True
        },
    },
    'Global': {
        'names': {
            'type': 'identifier',
            'is_list': True,
            'is_optional': False
        },
    },
    'Expr': {
        'value': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
    },
    'BoolOp': {
        'op': {
            'type': ast.boolop,
            'is_list': False,
            'is_optional': False
        },
        'values': {
            'type': ast.expr,
            'is_list': True,
            'is_optional': False
        },
    },
    'BinOp': {
        'left': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
        'op': {
            'type': ast.operator,
            'is_list': False,
            'is_optional': False
        },
        'right': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
    },
    'UnaryOp': {
        'op': {
            'type': ast.unaryop,
            'is_list': False,
            'is_optional': False
        },
        'operand': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
    },
    'Lambda': {
        'args': {
            'type': ast.arguments,
            'is_list': False,
            'is_optional': False
        },
        'body': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
    },
    'IfExp': {
        'test': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
        'body': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
        'orelse': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
    },
    'Dict': {
        'keys': {
            'type': ast.expr,
            'is_list': True,
            'is_optional': False
        },
        'values': {
            'type': ast.expr,
            'is_list': True,
            'is_optional': False
        },
    },
    'Set': {
        'elts': {
            'type': ast.expr,
            'is_list': True,
            'is_optional': False
        },
    },
    'ListComp': {
        'elt': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
        'generators': {
            'type': ast.comprehension,
            'is_list': True,
            'is_optional': False
        },
    },
    'SetComp': {
        'elt': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
        'generators': {
            'type': ast.comprehension,
            'is_list': True,
            'is_optional': False
        },
    },
    'DictComp': {
        'key': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
        'value': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
        'generators': {
            'type': ast.comprehension,
            'is_list': True,
            'is_optional': False
        },
    },
    'GeneratorExp': {
        'elt': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
        'generators': {
            'type': ast.comprehension,
            'is_list': True,
            'is_optional': False
        },
    },
    'Yield': {
        'value': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': True
        }
    },
    'Compare': {
        'left': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
        'ops': {
            'type': ast.cmpop,
            'is_list': True,
            'is_optional': False
        },
        'comparators': {
            'type': ast.expr,
            'is_list': True,
            'is_optional': False
        },
    },
    'Call': {
        'func': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
        'args': {
            'type': ast.expr,
            'is_list': True,
            'is_optional': False
        },
        'keywords': {
            'type': ast.keyword,
            'is_list': True,
            'is_optional': False
        },
        'starargs': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': True
        },
        'kwargs': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': True
        },
    },
    'Repr': {
        'value': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        }
    },
    'Num': {
        'n': {
            'type': 'object',
            'is_list': False,
            'is_optional': False
        }
    },
    'Str': {
        's': {
            'type': 'string',
            'is_list': False,
            'is_optional': False
        }
    },
    'Attribute': {
        'value': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
        'attr': {
            'type': 'identifier',
            'is_list': False,
            'is_optional': False
        },
        'ctx': {
            'type': ast.expr_context,
            'is_list': False,
            'is_optional': False
        },
    },
    'Subscript': {
        'value': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
        'slice': {
            'type': ast.slice,
            'is_list': False,
            'is_optional': False
        },
    },
    'Name': {
        'id': {
            'type': 'identifier',
            'is_list': False,
            'is_optional': False
        }
    },
    'List': {
        'elts': {
            'type': ast.expr,
            'is_list': True,
            'is_optional': False
        },
        'ctx': {
            'type': ast.expr_context,
            'is_list': False,
            'is_optional': False
        },
    },
    'Tuple': {
        'elts': {
            'type': ast.expr,
            'is_list': True,
            'is_optional': False
        },
        'ctx': {
            'type': ast.expr_context,
            'is_list': False,
            'is_optional': False
        },
    },
    'ExceptHandler': {
        'type': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': True
        },
        'name': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': True
        },
        'body': {
            'type': ast.stmt,
            'is_list': True,
            'is_optional': False
        }
    },
    'arguments': {
        'args': {
            'type': ast.expr,
            'is_list': True,
            'is_optional': False
        },
        'vararg': {
            'type': 'identifier',
            'is_list': False,
            'is_optional': True
        },
        'kwarg': {
            'type': 'identifier',
            'is_list': False,
            'is_optional': True
        },
        'defaults': {
            'type': ast.expr,
            'is_list': True,
            'is_optional': False
        },
    },
    'comprehension': {
        'target': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
        'iter': {
            'type': ast.expr,
            'is_list': False,
            'is_optional': False
        },
        'ifs': {
            'type': ast.expr,
            'is_list': True,
            'is_optional': False
        },
    },
    'alias': {
        'name': {
            'type': 'identifier',
            'is_list': False,
            'is_optional': False
        },
        'asname': {
            'type': 'identifier',
            'is_list': False,
            'is_optional': True
        }
    },
}


def escape(text):
    text = text \
        .replace('"', '`') \
        .replace('\'', '`') \
        .replace(' ', '-SP-') \
        .replace('\t', '-TAB-') \
        .replace('\n', '-NL-') \
        .replace('(', '-LRB-') \
        .replace(')', '-RRB-') \
        .replace('|', '-BAR-')
    return repr(text)[1:-1] if text else '-NONE-'


def typename(x):
    return type(x).__name__


def get_tree_str_repr(node):
    treeStr = ''
    if type(node) == list:
        for n in node:
            treeStr += get_tree_str_repr(n)

        return treeStr

    node_name = str(type(node))
    begin = node_name.find('ast.') + len('ast.')
    end = node_name.rfind('\'')
    node_name = node_name[begin: end]
    treeStr = '(' + node_name + ' '
    for field_name in node._fields:
        field = getattr(node, field_name)
        if hasattr(field, '_fields') and len(field._fields) == 0:
            continue
        if field:
            if type(field) == list:
                fieldRepr = get_tree_str_repr(field)
                fieldRepr = '(' + field_name + ' ' + fieldRepr + ') '
            elif type(field) == str or type(field) == int:
                fieldRepr = '(' + field_name + ' ' + str(field) + ') '
            else:
                fieldRepr = get_tree_str_repr(field)
                fieldRepr = '(' + field_name + ' ' + fieldRepr + ') '

            treeStr += fieldRepr
    treeStr += ') '

    return treeStr


def get_tree(node):

    if isinstance(node, str):
        node_name = escape(node)
    elif isinstance(node, int):
        node_name = node
    else:
        node_name = typename(node)

    tree = Tree(node_name)

    if not isinstance(node, ast.AST):
        return tree

    for field_name, field in ast.iter_fields(node):
        # omit empty fields
        if field is None or (isinstance(field, list) and len(field) == 0):
            continue

        if isinstance(field, ast.AST):
            # if len(field._fields) == 0:
            #     continue
            if field_name in ast_node_black_list:
                continue

            child = get_tree(field)

            tree.children.append(Tree(field_name, child))
        elif isinstance(field, str):
            field_val = escape(field)
            child = Tree(field_name, Tree(field_val))
            tree.children.append(child)
        elif isinstance(field, int):
            child = Tree(field_name, Tree(field))
            tree.children.append(child)
        elif isinstance(field, float):
            child = Tree(field_name, Tree(field))
            tree.children.append(child)
        elif isinstance(field, list):
            if len(field) > 0:
                child = Tree(field_name)
                # list_node = Tree('list')
                # child.children.append(list_node)
                for n in field:
                    # list_node.children.append(get_tree(n))
                    child.children.append(get_tree(n))

                tree.children.append(child)
        else:
            raise RuntimeError('unknown field!')

    return tree


def parse(code):
    root_node = code_to_ast(code)

    tree = get_tree(root_node.body[0])

    return tree


def code_to_ast(code):
    if p_elif.match(code):
        code = 'if True: pass\n' + code

    if p_else.match(code):
        code = 'if True: pass\n' + code

    if p_try.match(code):
        code = code + 'pass\nexcept: pass'
    elif p_except.match(code):
        code = 'try: pass\n' + code
    elif p_finally.match(code):
        code = 'try: pass\n' + code

    if p_decorator.match(code):
        code = code + '\ndef dummy(): pass'

    if code[-1] == ':':
        code = code + 'pass'

    ast_tree = ast.parse(code)

    return ast_tree


def parse_django(code_file):
    line_num = 0
    error_num = 0
    parse_trees = []
    for line in open(code_file):
        code = line.strip()
        # try:
        parse_tree = parse(code)
        rule_list = parse_tree.get_rule_list(include_leaf=False)
        parse_trees.append(parse_tree)
        ast_tree = tree_to_ast(parse_tree)
        print astor.to_source(ast_tree)
            # print parse_tree
        # except Exception as e:
        #     error_num += 1
        #     #pass
        #     #print e

        line_num += 1

    print 'total line of code: %d' % line_num
    print 'error num: %d' % error_num

    assert error_num == 0

    grammar = get_grammar(parse_trees)

    with open('grammar.txt', 'w') as f:
        for rule in grammar:
            str = rule.parent + ' -> ' + ', '.join(rule.children)
            f.write(str + '\n')

    with open('parse_trees.txt', 'w') as f:
        for tree in parse_trees:
            f.write(tree.__repr__() + '\n')

    return grammar, parse_trees


def tree_to_ast(tree):
    node_name = tree.name

    if tree.is_leaf:
        if node_name in ast_classes and node_name not in {'alias', 'operator'}:
            ast_node = ast_classes[node_name]()

            fields_info = None
            # init fields to empty
            if node_name in ast_class_fields:
                fields_info = ast_class_fields[node_name]

            for field in ast_node._fields:
                if fields_info and fields_info[field]['is_list'] and not fields_info[field]['is_optional']:
                    setattr(ast_node, field, list())
                else:
                    setattr(ast_node, field, None)

            return ast_node

        return node_name
    elif node_name in ast_classes:
        src_class = ast_classes[node_name]
        tgt_fields = src_class._fields

        # child_nodes = OrderedDict()
        # for child in tree.children:
        #     child_name = child.name
        #     if child not in child_nodes:
        #         child_nodes[child_name] = child
        #     else:
        #         old_child = child_nodes[child_name]
        #         if isinstance(old_child, list):
        #             old_child.append(child)
        #         else:
        #             child_nodes[child_name] = [old_child, child]

        fields_info = None
        if node_name in ast_class_fields:
            fields_info = ast_class_fields[node_name]

        ast_node = src_class()
        for child_node in tree.children:
            field = child_node.name

            if fields_info and fields_info[field]['is_list']:
                field_value = []
                nodes_in_list = child_node.children
                for sub_node in nodes_in_list:
                    sub_node_ast = tree_to_ast(sub_node)
                    field_value.append(sub_node_ast)
            else:
                assert len(child_node.children) == 1
                sub_node = child_node.children[0]
                field_value = tree_to_ast(sub_node)

            setattr(ast_node, field, field_value)

        for field in tgt_fields:
            if not hasattr(ast_node, field):
                if fields_info and fields_info[field]['is_list'] and not fields_info[field]['is_optional']:
                    setattr(ast_node, field, list())
                else:
                    setattr(ast_node, field, None)

        return ast_node

    else:
        raise RuntimeError('unknown tree node!')


if __name__ == '__main__':
    #     node = ast.parse('''
    # # for i in range(1, 100):
    # #  sum = sum + i
    # #
    # # sorted(arr, reverse=True)
    # # sorted(my_dict, key=lambda x: my_dict[x], reverse=True)
    # # m = dict ( zip ( new_keys , keys ) )
    # # for f in sorted ( os . listdir ( self . path ) ) :
    # #     pass
    # for f in sorted ( os . listdir ( self . path ) ) : pass
    # ''')
    # print ast.dump(node, annotate_fields=False)
    # print get_tree_str_repr(node)
    # print parse('for f in sorted ( os . listdir ( self . path ) ) : sum = sum + 1; sum = "(hello there)" ')
    # print parse('global _standard_context_processors')

    parse_django('/Users/yinpengcheng/Research/SemanticParsing/CodeGeneration/en-django/all.code')

    # code = """pos_inf = 1e200 * 1e200"""
    # ast_node = code_to_ast(code)
    # parse_tree = parse(code)
    # print parse_tree
    # ast_tree = tree_to_ast(parse_tree)
    # #
    # import astor
    # print astor.to_source(ast_node)

    pass