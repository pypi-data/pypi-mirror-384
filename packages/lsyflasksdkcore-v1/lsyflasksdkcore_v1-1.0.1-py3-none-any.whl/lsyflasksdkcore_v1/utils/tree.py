# -*- coding: utf-8 -*-

from inspect import isfunction
from typing import Collection, Callable, Dict


def depth_find_child(lst: Collection, join: Callable, root_node: Dict, one: Callable):
    """
    深度查询一个满足条件的子级
    :param lst: 列表
    :param join: 关联lambda item, parent_item: parent_item['id'] == item['parent_id']
    :param root_node: 父节点字典
    :param one: 单词匹配的lambda item: item['chaild_count'] == 0
    :return:
    """

    def _find(parent_node):
        childs = [row for row in lst if join(row, parent_node)]
        for item in childs:
            if one(item):
                return item
            else:
                ret = _find(item)
                if ret:
                    return ret
        return None

    return _find(root_node)


def depth_find_childs(lst, join=None, parent_node=None):
    """
    深度查找下级节点及子孙级节点.

    返回下级节点的列表.
    举例：lst = depth_find_childs(lst, join=lambda item,
            parent_item: item['parent_id'] == parent_item['id'], parent_node=object)
    """

    _childs = []

    if join is None or parent_node is None:
        return _childs

    nodes = []
    if isfunction(parent_node):
        nodes = filter(parent_node, lst)

    def _find(parent_node):
        childs = (row for row in lst if join(row, parent_node))
        if childs:
            for item in childs:
                _childs.append(item)
                _find(item)

    if nodes:
        _find(nodes.pop())
    else:
        _find(parent_node)

    return _childs


def tree_sorted(lst, key=None, join=None, root_node=None, reverse=False):
    """
    按照树的结构排序，返回排序后的新的列表对象.
    举例：lst = tree_sorted(lst, key=lambda item: item['order_number'], join=lambda item,
                          parent_item: item['parent_id'] == parent_item['id'],
                          root=lambda item: item['parent_id'] is None)
    """

    def _tree_recursion(parent_item, rs):
        result = [item for item in lst if join(item, parent_item)]

        if key is not None:
            result = sorted(result, key=key, reverse=reverse)

        parent_item_depth = parent_item.get('_depth', 0)
        for item in result:
            item['_depth'] = parent_item_depth + 1
            rs.append(item)
            _tree_recursion(item, rs)

    if join is None:
        return lst

    if root_node is None:
        roots = [item for item in lst if item['parent_id'] is None]
    else:
        roots = [item for item in lst if root_node(item)]

    if roots:
        root = roots.pop()
        rs = [root]
        _tree_recursion(root, rs)
        return rs
    return lst


def tree_node(lst, key=None, join=None, root_node=None, node=None, reverse=False):
    """
    生成树节点，返回根节点树结构.
    def test():
        def node(item):
            if item['parent_id'] is None:
                return {'id': '*', 'text': '所有联系人', 'checked': False,
                        'state': 'open', 'children': []}
            else:
                return {'id': item['id'], 'text': item['name'],
                        'checked': False, 'state': None, 'children': None, 'data': item}

        tree_node(lst, key=lambda item: item['order_number'], join=lambda item,
                  parent_item: item['parent_id'] == parent_item['id'], node=node)
    """

    def _tree_node(parent_node, parent_item):
        childs = [item for item in lst if join(item, parent_item)]

        if key is not None and childs:
            childs = sorted(childs, key=key, reverse=reverse)

        if childs:
            parent_node_depth = parent_node.get('_depth', 0)
            parent_node_children = []

            for item in childs:
                item['_depth'] = parent_node_depth + 1
                child_node = node(item)
                parent_node_children.append(child_node)
                _tree_node(child_node, item)
            parent_node['children'] = parent_node_children
        else:
            parent_node['state'] = 'open'

    if join is None or node is None:
        raise ValueError('join or node')

    if root_node is None:
        roots = [item for item in lst if item['parent_id'] is None]
    else:
        roots = list(filter(root_node, lst))

    if roots:
        root = roots.pop()
        root_node = node(root)
        _tree_node(root_node, root)
        return [root_node]
    return []
