from typing import Any

class Heap:
    """
    A binary heap data structure supporting min-heap or max-heap behavior.

    The heap maintains the heap property after insertions and deletions.
    Elements are stored in a dynamic array internally.

    Attributes:
        _arr (List[Any]): Internal array storing heap elements.
        _heap_type (str): Type of heap; either 'min' or 'max'.
        _vt (type): Expected type of elements stored in the heap.

    Properties:
        vt: Returns the expected value type.
        heap_type: Returns whether the heap is a min-heap or max-heap.

    Methods:
        parent(idx: int) -> int: Returns the index of the parent of a node.
        left(idx: int) -> int: Returns the index of the left child of a node.
        right(idx: int) -> int: Returns the index of the right child of a node.
        insert(val: Any): Insert a value while maintaining the heap property.
        extract_top() -> Any: Remove and return the top element (min or max).
        peek_top() -> Any: Return the top element without removing it.
        heapify(idx: int): Restore the heap property starting from a given index.
        __len__() -> int: Returns the number of elements in the heap.

    Raises:
        TypeError: If inserted value does not match expected type.
        IndexError: If extracting or peeking from an empty heap.
        ValueError: If heap_type is not 'min' or 'max'.
    
    Usage:
        >>> h = Heap(heap_type="min", val_type=int)
        >>> h.insert(val=5)
        >>> h.insert(val=3)
        >>> h.peek_top()
        3
        >>> h.extract_top()
        3
        >>> len(h)
        1
    """
    def __init__(self, *, heap_type: str, val_type: type):
        if heap_type not in ["min", "max"]:
            raise ValueError("Heap type must be 'min' or 'max'")
        self._arr = []
        self._heap_type = heap_type
        self._vt = val_type

    @property
    def vt(self) -> type:
        """Read-only property for value type."""
        return self._vt

    @property
    def heap_type(self) -> str:
        """Read-only property for heap type (min/max)."""
        return self._heap_type

    @staticmethod
    def parent(idx: int) -> int: 
        """Return the index of the parent of the node at idx."""
        return (idx - 1) // 2

    @staticmethod
    def left(idx: int) -> int: 
        """Return the index of the left child of the node at idx."""
        return (2 * idx) + 1

    @staticmethod
    def right(idx: int) -> int: 
        """Return the index of the right child of the node at idx."""
        return (2 * idx) + 2

    def _compare(self, a: Any, b: Any) -> bool:
        """Compare two elements according to heap type."""
        if self.heap_type == "min":
            return a < b
        else:
            return a > b

    def heapify(self, idx: int):
        """
        Restore the heap property starting from a given index downwards.

        Args:
            idx (int): Index to start heapifying from.
        """
        i = idx
        left_idx = Heap.left(idx)
        right_idx = Heap.right(idx)

        if (left_idx < len(self._arr)) and (self._compare(a=self._arr[left_idx], b=self._arr[i])):
            i = left_idx
        if (right_idx < len(self._arr)) and (self._compare(a=self._arr[right_idx], b=self._arr[i])):
            i = right_idx

        if i != idx:
            self._arr[idx], self._arr[i] = self._arr[i], self._arr[idx]
            self.heapify(idx=i)

    def insert(self, val: Any):
        """
        Insert a new value into the heap, maintaining the heap property.

        Args:
            val (Any): Value to insert.

        Raises:
            TypeError: If val is not of the expected type.
        """
        if not isinstance(val, self.vt):
            raise TypeError(f"Expected type {self.vt.__name__}, got {type(val).__name__}")
        self._arr.append(val)
        i = len(self._arr) - 1
        while i > 0 and self._compare(a=self._arr[i], b=self._arr[self.parent(i)]):
            self._arr[i], self._arr[self.parent(i)] = self._arr[self.parent(i)], self._arr[i]
            i = self.parent(i)

    def extract_top(self) -> Any:
        """
        Remove and return the top element of the heap (min or max).

        Returns:
            Any: The top element of the heap.

        Raises:
            IndexError: If the heap is empty.
        """
        if not self._arr:
            raise IndexError("Heap is empty")
        top = self._arr[0]
        self._arr[0] = self._arr[-1]
        self._arr.pop(-1)
        if self._arr:
            self.heapify(idx=0)
        return top

    def peek_top(self) -> Any:
        """
        Return the top element of the heap without removing it.

        Returns:
            Any: The top element.

        Raises:
            IndexError: If the heap is empty.
        """
        if not self._arr: raise IndexError("Heap is empty")
        return self._arr[0]

    def __len__(self) -> int: 
        """Return the number of elements in the heap."""
        return len(self._arr)