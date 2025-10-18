from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class Node:
    """
    A Node in a singly linked list.

    Attributes:
        val (Any): The value stored in the node.
        next (Optional[Node]): Reference to the next node in the list, or None if this is the last node.

    Methods:
        __repr__(): Returns a string representation of the node's value.
    """
    val: Any
    next: Optional['Node'] = None

    def __repr__(self) -> str: return f"{self.val}"

class LinkedList:
    """
    A singly linked list supporting insertion, deletion, search, and traversal.

    This linked list maintains sorted order upon insertion.
    It supports optional type checking and uniqueness enforcement on node values.

    Attributes:
        head (Optional[Node]): The first node in the list.
        _vt (type): Expected data type of values stored in the list nodes.
        _uv (bool): If True, enforces uniqueness of values in the list.

    Properties:
        vt: Returns the expected value type.
        uv: Returns whether the list enforces unique values.

    Methods:
        node_with_val_exists(val: Any) -> bool:
            Checks if a node with the given value exists in the list.
        search(val: Any) -> Optional[Node]:
            Returns the node with the specified value if it exists, else None.
        insert(val: Any):
            Inserts a value maintaining sorted order.
            Raises TypeError if value type does not match expected.
            Raises ValueError if unique values enforced and duplicate found.
        delete(val: Any):
            Deletes all nodes with the specified value.
        clear():
            Removes all nodes from the list.
        is_empty() -> bool:
            Returns True if the list is empty.
        __iter__():
            Iterator over nodes in the list.
        __repr__() -> str:
            Returns string representation of the list values separated by '->'.
        __len__() -> int:
            Returns the number of nodes in the list.
        to_list() -> list:
            Returns a Python list of all node values in order.

    Usage:
        >>> ll = LinkedList(val_type=int, unique_vals=True)
        >>> ll.insert(val=5)
        >>> ll.insert(val=3)
        >>> print(ll)
        3->5
        >>> ll.search(5)
        5
        >>> ll.delete(val=3)
        >>> print(ll.to_list())
        [5]

    Raises:
        TypeError: When inserted, searched, or deleted values do not match the expected type.
        ValueError: When attempting to insert duplicate values if unique_vals is True.
    """
    def __init__(self, *, head: Optional[Node]=None, val_type: type, unique_vals: bool) -> None:
        self.head = head
        self._vt = val_type
        self._uv = unique_vals

    @property
    def vt(self) -> type: return self._vt

    @property
    def uv(self) -> bool: return self._uv

    def node_with_val_exists(self, *, val: Any)->bool:
        """
        Check if a node with the specified value exists in the list.

        Args:
            val (Any): The value to search for.

        Returns:
            bool: True if a node with the value exists, False otherwise.

        Raises:
            TypeError: If val is not of the expected type.
        """
        if not isinstance(val, self.vt): raise TypeError(f"Expected type {self.vt.__name__}, got {type(val).__name__}")
        for node in self: 
            if node.val == val: return True
        return False
    
    def search(self, val: Any) -> Optional[Node]:
        """
        Search for the node containing the specified value.

        Args:
            val (Any): The value to find.

        Returns:
            Optional[Node]: The node containing the value, or None if not found.

        Raises:
            TypeError: If val is not of the expected type.
        """
        if not isinstance(val, self.vt): raise TypeError(f"Expected type {self.vt.__name__}, got {type(val).__name__}")
        for node in self:
            if node.val == val: return node
        return None
    
    def __iter__(self):
        current = self.head
        while current:
            yield current
            current = current.next
    
    def insert(self, *, val : Any):
        """
        Insert a new node with the specified value into the list, maintaining sorted order.

        Args:
            val (Any): The value to insert.

        Raises:
            TypeError: If val is not of the expected type.
            ValueError: If unique_vals is True and val already exists in the list.
        """
        if not isinstance(val, self.vt): raise TypeError(f"Expected type {self.vt.__name__}, got {type(val).__name__}")
        if self.uv and self.node_with_val_exists(val=val): raise ValueError(f"Duplicate value '{val}' not allowed in a unique-value list.")
        if self.head is None: 
            self.head = Node(val=val)
            return
        if val < self.head.val: 
            self.head = Node(val=val, next=self.head)
            return
        prev = self.head
        curr = prev.next
        while curr:
            if val > curr.val:
                curr = curr.next
                prev = prev.next
            else:
                break
        prev.next = Node(val=val, next=curr)
        
    def __repr__(self) -> str:
        nodes = []
        for node in self: nodes.append(str(node.val))
        return "->".join(nodes) if nodes else "Empty"
    
    def __len__(self) -> int:
        count = 0
        for _ in self: count+=1
        return count
    
    def to_list(self) -> list:
        """
        Convert the linked list to a Python list of values.

        Returns:
            list: Values from the linked list in order.
        """
        ll = []
        for node in self: ll.append(node.val)
        return ll
    
    def delete(self, *, val: Any):
        """
        Delete all nodes with the specified value from the list.

        Args:
            val (Any): The value to delete.

        Raises:
            TypeError: If val is not of the expected type.
        """
        if not isinstance(val, self.vt): raise TypeError(f"Expected type {self.vt.__name__}, got {type(val).__name__}")
        temp = self.head
        prev = None
        while temp:
            if prev is None and temp.val == val:
                temp2 = temp
                self.head = self.head.next
                temp = self.head
                del temp2
                if self.uv: return
                continue
            elif temp.val == val:
                temp2 = temp
                prev.next = temp.next
                temp = temp.next
                del temp2
                if self.uv: return
                continue
            prev = temp
            temp = temp.next

    def clear(self) -> None: 
        """Remove all nodes from the list."""
        self.head = None

    def is_empty(self) -> bool: 
        """
        Check if the linked list is empty.

        Returns:
            bool: True if empty, False otherwise.
        """
        return self.head is None