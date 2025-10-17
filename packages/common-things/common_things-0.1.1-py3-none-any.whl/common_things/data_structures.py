import sys
from abc import ABC, abstractmethod
from typing import (
    Any,
    List,
    Tuple,
    Optional, Generic, TypeVar, Iterator,
)


T = TypeVar('T')
V = TypeVar('V')


class EmptyCollectionError(Exception):
    """自定义空集合异常"""
    pass


class _LinkList(ABC, Generic[T]):
    """链表抽象基类，定义公共接口与初始化逻辑"""
    class Node(Generic[V]):
        """节点抽象类（强制子类实现结构）"""
        def __init__(self, value: V):
            self.value = value

    def __init__(self, *values) -> None:
        if not values:
            self.head: Optional[_LinkList.Node[T]] = None
        else:
            self.head = self.Node(values[0])
            if len(values) > 1:
                self.init_values(values[1:])

    @abstractmethod
    def init_values(self, values: Tuple[T]) -> None:
        pass

    def __repr__(self) -> str:
        """通用链表字符串表示（兼容单向/双向）"""
        values = [str(val) for val in self]
        return f"{self.__class__.__name__}({', '.join(values)})" if values else f"{self.__class__.__name__}()"

    def __iter__(self) -> Iterator[T]:
        """迭代器支持"""
        current = self.head
        while current:
            yield current.value
            current = getattr(current, 'next_node', None)

    def clear(self) -> None:
        """清空链表（置空头节点）"""
        self.head = None

    @property
    def is_empty(self) -> bool:
        return self.head is None


class OneWayLinkList(_LinkList[T]):
    """单向列表"""
    class Node(_LinkList.Node[V]):
        def __init__(self, value: V) -> None:
            super().__init__(value)
            self.next_node: Optional[OneWayLinkList.Node[V]] = None

    def __init__(self, *values) -> None:
        super().__init__(*values)

    def init_values(self, values: Tuple[T]) -> None:
        """构建单向链表：依次连接后续节点"""
        current = self.head
        for value in values:
            new_node = self.Node(value)
            current.next_node = new_node
            current = new_node

    def append(self, value: T) -> None:
        """追加元素"""
        new_node = self.Node(value)
        if not self.head:
            self.head = new_node
            return

        current = self.head
        while current.next_node:
            current = current.next_node
        current.next_node = new_node


class TwoWayLinkList(OneWayLinkList[T]):
    """双向链表"""
    class Node(OneWayLinkList.Node[V]):
        def __init__(self, value: V) -> None:
            super().__init__(value)
            self.prev_node: Optional[TwoWayLinkList.Node[V]] = None  # 新增前向指针

    def __init__(self, *values) -> None:
        super().__init__(*values)

    def init_values(self, values: List[T]) -> None:
        """构建双向链表：设置双向连接"""
        current = self.head
        for value in values:
            new_node = self.Node(value)
            # 关键修正：设置前向与后向指针
            current.next_node = new_node
            new_node.prev_node = current
            current = new_node

    @property
    def tail(self) -> Optional[Node[T]]:
        """获取尾节点"""
        if not self.head:
            return None
        current = self.head
        while current.next_node:
            current = current.next_node
        return current


class _Tree(ABC, Generic[T]):
    class Node(Generic[V]):
        def __init__(self, value: V) -> None:
            self.value = value

        def __repr__(self) -> str:
            return f"{self.value}"

    @abstractmethod
    def clear(self) -> None:
        """清空链表（置空头节点）"""
        pass

    @property
    @abstractmethod
    def is_empty(self) -> bool:
        pass


class BinaryTree(_Tree[T]):
    """二叉树"""
    class Node(_Tree.Node[V]):
        def __init__(self, value: V) -> None:
            super().__init__(value)
            self._left: Optional[BinaryTree.Node[V]] = None  # 左子节点
            self._right: Optional[BinaryTree.Node[V]] = None  # 右子节点

        @property
        def left(self) -> None:
            return self._left

        @left.setter
        def left(self, node: Optional["BinaryTree.Node[T]"]) -> None:
            self._left = node

        @left.deleter
        def left(self) -> None:
            self._left = None

        @property
        def right(self) -> None:
            return self._right

        @right.setter
        def right(self, node: Optional["BinaryTree.Node[T]"]) -> None:
            self._right = node

        @right.deleter
        def right(self) -> None:
            self._right = None

    def __init__(self, value: Optional[T] = None) -> None:
        self.root = self.Node(value) if value is not None else None

    def __repr__(self) -> str:
        return f"BinaryTree(root={self.root.value if self.root else None})"

    def clear(self) -> None:
        self.root = None

    def is_empty(self) -> bool:
        return self.root is None


class NAryTree(_Tree[T]):
    """多叉树"""
    class Node(_Tree.Node[V]):
        def __init__(self, value: V) -> None:
            self.value = value
            self._children: List[NAryTree.Node[V]] = []

        @property
        def children_count(self) -> int:
            return len(self._children)

        def __getitem__(self, index: int) -> "NAryTree.Node[T]":
            return self._children[index]

        def __setitem__(self, index: int, value: T) -> None:
            self._children[index] = value

        def append_node(self, value: T) -> None:
            self._children.append(value)

        def __len__(self) -> int:
            return len(self.value)

    def __init__(self, value: Optional[T] = None) -> None:
        self.root = self.Node(value) if value is not None else None

    def __repr__(self) -> str:
        if self.root is None:
            return f"NAryTree()"
        return f"NAryTree(root={self.root.value}, children={self.root.children_count})"

    def clear(self) -> None:
        self.root = None

    @property
    def is_empty(self) -> bool:
        return self.root is None

class Stack(Generic[T]):
    """基于列表实现的栈（LIFO）"""
    def __init__(self, max_len: Optional[int] = None) -> None:
        self._max_len = max_len if max_len is not None else sys.maxsize
        self._items: List[T] = []

    def __len__(self):
        return len(self._items)

    def push(self, item: T) -> T | None:
        popped = None
        """压栈：将元素添加到栈顶（列表末尾）"""
        if self._max_len and len(self._items) >= self._max_len:
            popped = self.pop()
        self._items.append(item)
        return popped

    def pop(self) -> T:
        """弹栈：移除并返回栈顶元素（列表末尾）"""
        if self.is_empty:
            raise EmptyCollectionError("Cannot pop from an empty stack")
        return self._items.pop()

    def peek(self) -> T:
        """查看栈顶元素（不弹出）"""
        if self.is_empty:
            raise EmptyCollectionError("Cannot peek from an empty stack")
        return self._items[-1]  # 列表最后一个元素是栈顶

    @property
    def is_empty(self) -> bool:
        """判断栈是否为空"""
        return not self._items

    def clear(self) -> None:
        """清空栈"""
        self._items.clear()

    def __repr__(self) -> str:
        """字符串表示（方便调试）"""
        return f"{self.__class__.__name__}{self._items}"


from collections import deque

class Queue(Generic[T]):
    """基于deque实现的高效队列（FIFO）"""
    def __init__(self, max_len: Optional[int] = None) -> None:
        self._queue = deque(maxlen=max_len)  # 存储队列元素

    def __len__(self) -> int:
        return len(self._queue)

    def enqueue(self, item: T) -> None:
        """入队：将元素添加到队尾（deque的右端）"""
        self._queue.append(item)

    def dequeue(self) -> T:
        """出队：移除并返回队首元素（deque的左端）"""
        if self.is_empty:
            raise EmptyCollectionError("Cannot dequeue from an empty queue")
        return self._queue.popleft()  # deque的popleft()是O(1)

    def front(self) -> T:
        """查看队首元素（不删除）"""
        if self.is_empty:
            raise EmptyCollectionError("Cannot get front from an empty queue")
        return self._queue[0]  # 直接访问deque的第一个元素

    def back(self) -> T:
        """查看队尾元素（不删除）"""
        if self.is_empty:
            raise EmptyCollectionError("Cannot get front from an empty queue")
        return self._queue[-1]

    @property
    def is_empty(self) -> bool:
        """判断队列是否为空"""
        return not self._queue  # deque为空时返回False

    def clear(self) -> None:
        """清空队列"""
        self._queue.clear()

    def __repr__(self) -> str:
        """字符串表示（方便调试）"""
        return f"Queue({list(self._queue)})"  # deque转列表展示


import heapq

class PriorityQueue(Generic[T]):
    """基于最小堆实现的优先队列（优先级数值越小越优先）"""
    def __init__(self, reverse: bool = False) -> None:
        self._heap: List[Tuple[int, int, Any]] = []  # 堆存储（优先级, 元素）元组
        self._counter = 0  # 计数器：解决相同优先级元素的顺序问题
        self.reverse = reverse # 反转优先级：最小堆 -> 最大堆

    def push(self, item: Any, priority: int) -> None:
        """插入元素：用（优先级, 计数器, 元素）元组保证稳定性"""
        if self.reverse:
            priority = -priority
        heapq.heappush(self._heap, (priority, self._counter, item))
        self._counter += 1  # 计数器递增，确保相同优先级元素按插入顺序出队

    def pop(self) -> T:
        """弹出优先级最高的元素（堆顶）"""
        if self.is_empty:
            raise EmptyCollectionError("pop from empty priority queue")
        # 返回元组中的第三个元素（item），忽略优先级和计数器
        return heapq.heappop(self._heap)[2]

    def peek(self) -> T:
        """查看优先级最高的元素（堆顶）"""
        if self.is_empty:
            raise EmptyCollectionError("peek from empty priority queue")
        return self._heap[0][2]  # 堆顶元组的第三个元素是item

    @property
    def is_empty(self) -> bool:
        """判断队列是否为空"""
        return not self._heap

    @property
    def size(self) -> int:
        """返回队列大小"""
        return len(self._heap)

    def __repr__(self) -> str:
        """字符串表示（按优先级排序展示元素）"""
        sorted_items = sorted(self._heap, key=lambda x: x[0])
        return f"PriorityQueue({[item[2] for item in sorted_items]})"


__all__ = [
    'OneWayLinkList',
    'TwoWayLinkList',
    'BinaryTree',
    'NAryTree',
    'Stack',
    'Queue',
    'PriorityQueue',
]