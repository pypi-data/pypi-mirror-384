
import pprint, collections, enum

from .. import Devutils as dev
from .. import Numputils as nput

__all__ = ["TreeWrapper", "tree_traversal", "tree_iter", "TreeSentinels"]

class TreeTraversalOrder(enum.Enum):
    BreadthFirst = 'bfs'
    DepthFirst = 'dfs'

class TreeCallOrder(enum.Enum):
    PreVisit = "pre"
    PostVisit = "post"
    PostChildren = "final"

class TreeSentinels(enum.Enum):
    Stop = "stop"
    Skip = "skip"

def _get_tree_children(tree):
    if hasattr(tree, 'keys'):
        return list(enumerate(tree.keys()))
    else:
        return list(enumerate(tree))
def _get_tree_item(tree, item):
    return tree[item[1]]
def tree_traversal(tree, callback,
                   root=None,
                   get_item=None,
                   get_children=None,
                   visited:set=None,
                   check_visited=None,
                   traversal_ordering='bfs',
                   call_order='post'
                   ):
    if get_children is None and get_item is None:
        get_children, get_item = _get_tree_children, _get_tree_item
    elif get_children is not None and get_item is None:
        raise ValueError("`get_children` must be implemented if `get_item` is provided")
    elif get_children is None and get_item is not None:
        raise ValueError("`get_item` must be implemented if `get_children` is provided")

    if root is dev.default:
        root = get_children(tree)[0]
    if root in visited:
        return

    if check_visited is None:
        check_visited = visited is not None
    if check_visited and visited is None:
        visited = set()

    queue = collections.deque([[None, root]])
    if isinstance(traversal_ordering, str):
        traversal_ordering = TreeTraversalOrder(traversal_ordering)
    if isinstance(call_order, str):
        call_order = TreeCallOrder(call_order)
    if traversal_ordering is traversal_ordering.BreadthFirst:
        pop = queue.popleft
        extend = queue.extend
    else:
        pop = queue.popleft
        extend = queue.extendleft

    while queue:
        parent, head = pop()

        if call_order == TreeCallOrder.PreVisit:
            res = callback(parent, head, visited)
            if res is not None:
                return res

        if check_visited:
            visited.add(head)

        if call_order == TreeCallOrder.PostVisit:
            res = callback(parent, head, visited)
            if res is not None:
                return res

        if check_visited:
            extend(
                [head, get_item(head, h)]
                for h in get_children(head)
                if h not in visited
            )
        else:
            extend(
                [head, get_item(head, h)]
                for h in get_children(head)
            )

        if call_order == TreeCallOrder.PostChildren:
            res = callback(parent, head, visited)
            if res is not None:
                return res

def tree_iter(tree,
              root=None,
              get_item=None,
              get_children=None,
              visited: set=None,
              check_visited=None,
              traversal_ordering='bfs'
              ):
    if get_children is None and get_item is None:
        get_children, get_item = _get_tree_children, _get_tree_item
    elif get_children is not None and get_item is None:
        raise ValueError("`get_children` must be implemented if `get_item` is provided")
    elif get_children is None and get_item is not None:
        raise ValueError("`get_item` must be implemented if `get_children` is provided")

    if root is dev.default:
        root = get_children(tree)[0]
    if root in visited:
        return

    if check_visited is None:
        check_visited = visited is not None
    if check_visited and visited is None:
        visited = set()

    queue = collections.deque([[None, root]])
    if isinstance(traversal_ordering, str):
        traversal_ordering = TreeTraversalOrder(traversal_ordering)
    if traversal_ordering is traversal_ordering.BreadthFirst:
        pop = queue.popleft
        extend = queue.extend
    else:
        pop = queue.popleft
        extend = queue.extendleft

    while queue:
        parent, head = pop()
        res = yield parent
        if res is TreeSentinels.Skip:
            continue
        elif res is TreeSentinels.Stop:
            break

        if check_visited:
            visited.add(head)

        if check_visited:
            extend(
                [head, get_item(head, h)]
                for h in get_children(head)
                if h not in visited
            )
        else:
            extend(
                [head, get_item(head, h)]
                for h in get_children(head)
            )

class TreeWrapper:
    def __init__(self, tree):
        self.tree = tree

    def __repr__(self):
        fmt_tree = pprint.pformat(self.tree)
        cls = type(self)
        return f"{cls.__name__}({fmt_tree})"
    def __len__(self):
        return len(self.tree)
    def __iter__(self):
        return iter(self.tree)
    def condense_subtrees(self):
        if hasattr(self.tree, 'keys') or not all(
            hasattr(t, 'keys') for t in self.tree
        ):
            return self
        else:
            new_tree = self.tree[0]
            for t in self.tree[1:]:
                new_tree = dev.merge_dicts(new_tree, t)
            return type(self)(new_tree)
    def keys(self):
        if hasattr(self.tree, 'keys'):
            return self.tree.keys()
        else:
            return None
    def values(self):
        if hasattr(self.tree, 'values'):
            return self.tree.values()
        else:
            return self.tree
    def find_subtree(self, key):
        if hasattr(self.tree, 'keys'):
            return self.__getitem__(key)
        else:
            if nput.is_atomic(key):
                key = [key]
            for k in key:
                for n,v in enumerate(self.tree):
                    if dev.is_dict_like(v) and k in v:
                        return v[k]
                    # elif v == k:
                    #     return v
    @classmethod
    def get_tree_item(cls, tree, item):
        t = tree
        if nput.is_atomic(item):
            item = [item]
        base_exception = None
        for k in item:
            if not isinstance(k, str) and hasattr(t, 'keys'):
                woof = []
                for n,v in enumerate(t.keys()):
                    woof.append(v)
                    if n >= k:
                        break
                else:
                    base_exception = IndexError("index {} not valid for subtree with keys {}".format(
                        k, t.keys()
                    ))
                    break
                k = woof[-1]
            try:
                t = t[k]
            except (IndexError, KeyError, TypeError) as e:
                base_exception = e
                break


        if base_exception is not None:
            raise IndexError(f"{item} not found in tree") from base_exception

        return t
    def __getitem__(self, item):
        return self.get_tree_item(self.tree, item)
    def bfs(self, callback, **opts):
        #TODO: support most sophsticated children/item indexing
        return tree_traversal(self.tree, callback, traversal_ordering='bfs', **opts)
    def dfs(self, callback, **opts):
        return tree_traversal(self.tree, callback, traversal_ordering='dfs', **opts)