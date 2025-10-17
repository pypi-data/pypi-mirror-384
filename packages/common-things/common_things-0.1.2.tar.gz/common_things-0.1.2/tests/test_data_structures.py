import pytest
from src.common_things.data_structures import *


class TestOneWayLinkList:
    """单向链表测试类"""

    def test_init_empty(self):
        """测试空链表初始化"""
        ll = OneWayLinkList()
        assert ll.is_empty
        assert list(ll) == []
        assert str(ll) == "OneWayLinkList()"

    def test_init_with_values(self):
        """测试带值初始化"""
        ll = OneWayLinkList(1, 2, 3)
        assert not ll.is_empty
        assert list(ll) == [1, 2, 3]
        assert str(ll) == "OneWayLinkList(1, 2, 3)"

    def test_append(self):
        """测试追加元素"""
        ll = OneWayLinkList()
        ll.append(1)
        ll.append(2)
        ll.append(3)
        assert list(ll) == [1, 2, 3]
        assert not ll.is_empty

    def test_clear(self):
        """测试清空链表"""
        ll = OneWayLinkList(1, 2, 3)
        ll.clear()
        assert ll.is_empty
        assert list(ll) == []


class TestTwoWayLinkList:
    """双向链表测试类"""

    def test_init_empty(self):
        """测试空链表初始化"""
        ll = TwoWayLinkList()
        assert ll.is_empty
        assert list(ll) == []

    def test_init_with_values(self):
        """测试带值初始化"""
        ll = TwoWayLinkList(1, 2, 3)
        assert not ll.is_empty
        assert list(ll) == [1, 2, 3]
        assert ll.tail is not None
        assert ll.tail.value == 3

    def test_bidirectional_links(self):
        """测试双向连接"""
        ll = TwoWayLinkList(1, 2, 3)
        # 测试正向连接
        assert ll.head.value == 1
        assert ll.head.next_node.value == 2
        assert ll.head.next_node.next_node.value == 3

        # 测试反向连接
        tail = ll.tail
        assert tail.value == 3
        assert tail.prev_node.value == 2
        assert tail.prev_node.prev_node.value == 1

    def test_append(self):
        """测试追加元素"""
        ll = TwoWayLinkList()
        ll.append(1)
        ll.append(2)
        assert list(ll) == [1, 2]
        assert ll.tail.value == 2


class TestBinaryTree:
    """二叉树测试类"""

    def test_init_empty(self):
        """测试空树初始化"""
        tree = BinaryTree()
        assert tree.is_empty()
        assert tree.root is None

    def test_init_with_value(self):
        """测试带值初始化"""
        tree = BinaryTree(10)
        assert not tree.is_empty()
        assert tree.root.value == 10
        assert tree.root.left is None
        assert tree.root.right is None

    def test_set_children(self):
        """测试设置子节点"""
        tree = BinaryTree(10)
        left_child = BinaryTree.Node(5)
        right_child = BinaryTree.Node(15)

        tree.root.left = left_child
        tree.root.right = right_child

        assert tree.root.left.value == 5
        assert tree.root.right.value == 15

    def test_clear(self):
        """测试清空树"""
        tree = BinaryTree(10)
        tree.clear()
        assert tree.is_empty()
        assert tree.root is None


class TestNAryTree:
    """多叉树测试类"""

    def test_init_empty(self):
        """测试空树初始化"""
        tree = NAryTree()
        assert tree.is_empty
        assert tree.root is None

    def test_init_with_value(self):
        """测试带值初始化"""
        tree = NAryTree(10)
        assert not tree.is_empty
        assert tree.root.value == 10
        assert tree.root.children_count == 0

    def test_append_children(self):
        """测试添加子节点"""
        tree = NAryTree(10)
        tree.root.append_node(5)
        tree.root.append_node(15)
        tree.root.append_node(20)

        assert tree.root.children_count == 3
        assert tree.root[0] == 5
        assert tree.root[1] == 15
        assert tree.root[2] == 20

    def test_clear(self):
        """测试清空树"""
        tree = NAryTree(10)
        tree.clear()
        assert tree.is_empty
        assert tree.root is None


class TestStack:
    """栈测试类"""

    def test_init_empty(self):
        """测试空栈初始化"""
        stack = Stack()
        assert stack.is_empty
        assert len(stack) == 0

    def test_push_pop(self):
        """测试压栈和弹栈"""
        stack = Stack()
        stack.push(1)
        stack.push(2)
        stack.push(3)

        assert not stack.is_empty
        assert len(stack) == 3
        assert stack.pop() == 3
        assert stack.pop() == 2
        assert stack.pop() == 1
        assert stack.is_empty

    def test_peek(self):
        """测试查看栈顶"""
        stack = Stack()
        stack.push(10)
        stack.push(20)

        assert stack.peek() == 20
        assert len(stack) == 2  # peek不应改变栈大小

    def test_pop_empty(self):
        """测试空栈弹栈异常"""
        stack = Stack()
        with pytest.raises(EmptyCollectionError):
            stack.pop()

    def test_peek_empty(self):
        """测试空栈查看异常"""
        stack = Stack()
        with pytest.raises(EmptyCollectionError):
            stack.peek()

    def test_max_length(self):
        """测试栈长度限制"""
        stack = Stack(max_len=2)
        stack.push(1)
        stack.push(2)
        popped = stack.push(3)  # 应弹出第一个元素

        assert popped == 2
        assert list(stack._items) == [1, 3]
        assert len(stack) == 2


class TestQueue:
    """队列测试类"""

    def test_init_empty(self):
        """测试空队列初始化"""
        queue = Queue()
        assert queue.is_empty
        assert len(queue) == 0

    def test_enqueue_dequeue(self):
        """测试入队和出队"""
        queue = Queue()
        queue.enqueue(1)
        queue.enqueue(2)
        queue.enqueue(3)

        assert not queue.is_empty
        assert len(queue) == 3
        assert queue.dequeue() == 1
        assert queue.dequeue() == 2
        assert queue.dequeue() == 3
        assert queue.is_empty

    def test_front_back(self):
        """测试查看队首和队尾"""
        queue = Queue()
        queue.enqueue(10)
        queue.enqueue(20)
        queue.enqueue(30)

        assert queue.front() == 10
        assert queue.back() == 30
        assert len(queue) == 3  # 查看不应改变队列大小

    def test_dequeue_empty(self):
        """测试空队列出队异常"""
        queue = Queue()
        with pytest.raises(EmptyCollectionError):
            queue.dequeue()

    def test_front_empty(self):
        """测试空队列查看队首异常"""
        queue = Queue()
        with pytest.raises(EmptyCollectionError):
            queue.front()

    def test_back_empty(self):
        """测试空队列查看队尾异常"""
        queue = Queue()
        with pytest.raises(EmptyCollectionError):
            queue.back()

    def test_max_length(self):
        """测试队列长度限制"""
        queue = Queue(max_len=2)
        queue.enqueue(1)
        queue.enqueue(2)
        queue.enqueue(3)  # 应自动移除第一个元素

        assert len(queue) == 2
        assert queue.dequeue() == 2
        assert queue.dequeue() == 3


class TestPriorityQueue:
    """优先队列测试类"""

    def test_init_empty(self):
        """测试空优先队列初始化"""
        pq = PriorityQueue()
        assert pq.is_empty
        assert pq.size == 0

    def test_push_pop(self):
        """测试插入和弹出"""
        pq = PriorityQueue()
        pq.push("task1", 3)
        pq.push("task2", 1)  # 最高优先级
        pq.push("task3", 2)

        assert not pq.is_empty
        assert pq.size == 3
        assert pq.pop() == "task2"  # 优先级最高
        assert pq.pop() == "task3"
        assert pq.pop() == "task1"
        assert pq.is_empty

    def test_peek(self):
        """测试查看队首"""
        pq = PriorityQueue()
        pq.push("task1", 2)
        pq.push("task2", 1)

        assert pq.peek() == "task2"
        assert pq.size == 2  # peek不应改变队列大小

    def test_pop_empty(self):
        """测试空优先队列弹出异常"""
        pq = PriorityQueue()
        with pytest.raises(EmptyCollectionError):
            pq.pop()

    def test_peek_empty(self):
        """测试空优先队列查看异常"""
        pq = PriorityQueue()
        with pytest.raises(EmptyCollectionError):
            pq.peek()

    def test_reverse_priority(self):
        """测试反向优先级（最大堆）"""
        pq = PriorityQueue(reverse=True)
        pq.push("task1", 1)
        pq.push("task2", 3)  # 反向后优先级最高
        pq.push("task3", 2)

        assert pq.pop() == "task2"
        assert pq.pop() == "task3"
        assert pq.pop() == "task1"

    def test_same_priority_order(self):
        """测试相同优先级的插入顺序"""
        pq = PriorityQueue()
        pq.push("task1", 1)
        pq.push("task2", 1)  # 相同优先级，按插入顺序
        pq.push("task3", 1)

        # 相同优先级应按插入顺序出队
        assert pq.pop() == "task1"
        assert pq.pop() == "task2"
        assert pq.pop() == "task3"
