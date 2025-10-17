
import ast, collections, inspect

__all__ = [
    "ExamplesParser"
]

class ExamplesParser:
    """
    Provides a parser for unit tests to turn them into examples
    """

    def __init__(self, unit_tests):
        self.source = unit_tests
        self.ast = ast.parse(unit_tests)
        self._class_node = None
        self._setup = None
        self._functions = None
        self._functions_map = None
        self._node_cache = {}

    def find_setup(self, tree_iter):
        setup = []
        for node in tree_iter:
            node_type = type(node).__name__
            if node_type not in ["ClassDef"]:
                setup.append(node)
            else:
                break
        else:
            node = None
        return node, setup

    def parse_tests(self, tree_iter):
        """
        Parses out the
        :param tree_iter:
        :type tree_iter:
        :return:
        :rtype:
        """
        class_setup = []
        functions = collections.OrderedDict()
        for node in tree_iter:
            node_type = type(node).__name__
            if node_type == 'FunctionDef':
                fname = node.name
                if fname.startswith('test_'):
                    functions[fname.split("_", 1)[1]] = node
                else:
                    class_setup.append(node)
            else:
                class_setup.append(node)
            # else:
            #     raise ValueError(
            #         "AST node of type {} with body {} not handled".format(
            #             node_type, ast.get_source_segment(self.source, node)
            #         )
            #     )
        return class_setup, functions

    def walk_tree(self):
        if hasattr(self.ast, 'body'):
            tree = self.ast.body
        else:
            tree = self.ast
        tree_iter = iter(tree)
        class_node, base_setup = self.find_setup(tree_iter)
        class_setup, functions = self.parse_tests(class_node.body)
        self._class_node = class_node
        self._setup = (base_setup, class_setup)
        self._functions = functions
        self._functions_map = self.load_function_map()
        return self._setup, self._functions

    def format_node(self, node):
        try:
            repr = self._node_cache[node]
        except KeyError:
            base = ast.get_source_segment(self.source, node)
            indent = " "*node.col_offset
            repr = indent + base
            self._node_cache[node] = repr
        return repr

    @classmethod
    def from_file(cls, tests_file):
        with open(tests_file) as f:
            return cls(f.read())

    @property
    def class_spec(self):
        if self._class_node is None:
            self.walk_tree()
        return (self._class_node, self._setup[1])
    @property
    def setup(self):
        if self._setup is None:
            self.walk_tree()
        return self._setup[0]
    @property
    def functions(self):
        if self._functions is None:
            self.walk_tree()
        return self._functions
    @property
    def functions_map(self):
        if self._functions is None:
            self.walk_tree()
        return self._functions_map

    def load_function_map(self):
        mapping = {}
        for k,v in self._functions.items():
            for f in self.get_examples_functions(v):
                if f not in mapping:
                    mapping[f] = [k]
                else:
                    mapping[f].append(k)
        return mapping

    IGNORE_UNHANDLED_STATEMENTS = False
    def _handle_stmt(self, stmt, all_fns):
        if hasattr(stmt, 'body'):
            all_fns.update(self.get_examples_functions(stmt))
        elif hasattr(stmt, 'names'):
            for name in stmt.names:
                if isinstance(name, str):
                    all_fns.add(name)
                else:
                    all_fns.add(name.name)
        elif hasattr(stmt, 'id'):
            name = stmt.id
            if isinstance(name, str):
                all_fns.add(name)
            else:
                all_fns.add(name.name)
        elif hasattr(stmt, 'func'):
            self._handle_stmt(stmt.func, all_fns)
            # for substmt in stmt.args:
            #     self._handle_stmt(substmt, all_fns)
        # we'll only check common patterns for speed purposes...
        elif hasattr(stmt, 'operand'):
            pass
            # self._handle_stmt(stmt.operand, all_fns)
        elif hasattr(stmt, 'right'):
            pass
            # self._handle_stmt(stmt.left, all_fns)
            # self._handle_stmt(stmt.right, all_fns)
        elif hasattr(stmt, 'comparators'):
            pass
            # self._handle_stmt(stmt.left, all_fns)
            # for v in stmt.comparators:
            #     self._handle_stmt(v, all_fns)
        elif hasattr(stmt, 'value'):
            if hasattr(stmt, 'targets'):
                # assignment
                self._handle_stmt(stmt.value, all_fns)
            else:
                node_type = type(stmt).__name__
                if node_type == 'Constant':
                    pass
                else:
                    self._handle_stmt(stmt.value, all_fns)
        elif hasattr(stmt, 'values'):
            pass
            # for v in stmt.values:
            #     self._handle_stmt(v, all_fns)
        elif hasattr(stmt, 'elts'):
            pass
            # for v in stmt.elts:
            #     self._handle_stmt(v, all_fns)
        elif (
            stmt is None
            or hasattr(stmt, 'generators')
            or hasattr(stmt, 'exc')
            or hasattr(stmt, 'targets')
        ):
            pass # for now at least...
        else:
            if self.IGNORE_UNHANDLED_STATEMENTS:
                print("IGNORING:", stmt)
            else:
                raise ValueError(f"don't know what to do with statement {stmt}")
    def get_examples_functions(self, node):
        all_fns = set()
        try:
            for stmt in node.body:
                self._handle_stmt(stmt, all_fns)
        except TypeError:
            self._handle_stmt(node.body, all_fns)
        return all_fns

    def filter_by_name(self, name):
        import copy
        if self._functions is None:
            self.walk_tree()
        c = copy.copy(self)
        try:
            keys = c._functions_map[name]
        except KeyError:
            new_fns = {}
        else:
            new_fns = {k:c._functions[k] for k in keys if k in c._functions}
        if len(new_fns) == 0:
            return None
        else:
            c._functions = new_fns
            return c