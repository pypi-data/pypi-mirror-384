import pytest
from dsaria.heap import Heap
import random

def test_init_valid_types():
    h1 = Heap(heap_type="min", val_type=int)
    h2 = Heap(heap_type="max", val_type=str)
    assert h1.heap_type == "min"
    assert h1.vt is int
    assert h2.heap_type == "max"
    assert h2.vt is str

def test_init_invalid_heap_type():
    with pytest.raises(ValueError):
        Heap(heap_type="middle", val_type=int)


def test_vt_property_is_read_only():
    h = Heap(heap_type="min", val_type=int)
    with pytest.raises(AttributeError):
        h.vt = str

def test_heap_type_property_is_read_only():
    h = Heap(heap_type="max", val_type=int)
    with pytest.raises(AttributeError):
        h.heap_type = "min"

def test_insert_valid_type_min_heap():
    h = Heap(heap_type="min", val_type=int)
    h.insert(val=10)
    h.insert(val=5)
    h.insert(val=15)
    assert h.peek_top() == 5
    assert len(h) == 3

def test_insert_valid_type_max_heap():
    h = Heap(heap_type="max", val_type=int)
    h.insert(val=10)
    h.insert(val=5)
    h.insert(val=15)
    assert h.peek_top() == 15
    assert len(h) == 3

def test_insert_invalid_type_raises():
    h = Heap(heap_type="min", val_type=int)
    with pytest.raises(TypeError):
        h.insert(val="not an int")


def test_extract_top_from_min_heap():
    h = Heap(heap_type="min", val_type=int)
    for v in [10, 5, 20]:
        h.insert(val=v)
    top = h.extract_top()
    assert top == 5
    assert len(h) == 2
    assert h.peek_top() in {10, 20}

def test_extract_top_from_max_heap():
    h = Heap(heap_type="max", val_type=int)
    for v in [10, 5, 20]:
        h.insert(val=v)
    top = h.extract_top()
    assert top == 20
    assert len(h) == 2
    assert h.peek_top() in {10, 5}

def test_extract_top_single_element():
    h = Heap(heap_type="min", val_type=int)
    h.insert(val=42)
    assert h.extract_top() == 42
    assert len(h) == 0

def test_extract_top_empty_heap_raises():
    h = Heap(heap_type="min", val_type=int)
    with pytest.raises(IndexError):
        h.extract_top()

def test_peek_top_non_empty():
    h = Heap(heap_type="min", val_type=int)
    h.insert(val=100)
    h.insert(val=50)
    assert h.peek_top() == 50
    assert len(h) == 2

def test_peek_top_empty_heap_raises():
    h = Heap(heap_type="max", val_type=int)
    with pytest.raises(IndexError):
        h.peek_top()

def test_len_on_heap():
    h = Heap(heap_type="min", val_type=int)
    assert len(h) == 0
    h.insert(val=1)
    h.insert(val=2)
    assert len(h) == 2

def test_min_heap_extracts_in_sorted_order():
    h = Heap(heap_type="min", val_type=int)
    nums = random.sample(range(1, 5000), 1000)
    for n in nums:
        h.insert(n)

    extracted = [h.extract_top() for _ in range(len(h))]
    assert extracted == sorted(nums)


def test_max_heap_extracts_in_reverse_sorted_order():
    h = Heap(heap_type="max", val_type=int)
    nums = random.sample(range(1, 5000), 1000)
    for n in nums:
        h.insert(n)

    extracted = [h.extract_top() for _ in range(len(h))]
    assert extracted == sorted(nums, reverse=True)


def test_large_scale_insert_and_peek_top_min_heap():
    h = Heap(heap_type="min", val_type=int)
    nums = random.sample(range(1, 100000), 5000)
    for n in nums:
        h.insert(n)

    assert h.peek_top() == min(nums)


def test_large_scale_insert_and_peek_top_max_heap():
    h = Heap(heap_type="max", val_type=int)
    nums = random.sample(range(1, 100000), 5000)
    for n in nums:
        h.insert(n)

    assert h.peek_top() == max(nums)


def test_mixed_operations_min_heap():
    h = Heap(heap_type="min", val_type=int)
    nums = list(range(100))
    random.shuffle(nums)
    for n in nums:
        h.insert(n)

    extracted = [h.extract_top() for _ in range(50)]
    assert extracted == sorted(extracted)

    for n in [200, 150, 175]:
        h.insert(n)

    prev = h.extract_top()
    while len(h) > 0:
        curr = h.extract_top()
        assert prev <= curr
        prev = curr


def test_mixed_operations_max_heap():
    h = Heap(heap_type="max", val_type=int)
    nums = list(range(100))
    random.shuffle(nums)
    for n in nums:
        h.insert(n)

    extracted = [h.extract_top() for _ in range(50)]
    assert extracted == sorted(extracted, reverse=True)

    for n in [200, 150, 175]:
        h.insert(n)

    prev = h.extract_top()
    while len(h) > 0:
        curr = h.extract_top()
        assert prev >= curr
        prev = curr