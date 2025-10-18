import pytest
import random
import dsaria.sort

def test_bubble_sort_normal_cases():
    assert dsaria.sort.bubble_sort(arr=[1,3,4,5,2,6]) == [1,2,3,4,5,6]
    assert dsaria.sort.bubble_sort(arr=[2,4,3,1,9]) == [1,2,3,4,9]
    assert dsaria.sort.bubble_sort(arr=[5,4,3,2,1]) == [1,2,3,4,5]

def test_bubble_sort_single():
    assert dsaria.sort.bubble_sort(arr=[1]) == [1]

def test_bubble_sort_empty():
    assert dsaria.sort.bubble_sort(arr=[]) == []

def test_bubble_sort_already_sorted():
    assert dsaria.sort.bubble_sort(arr=[1,2,3,4,5]) == [1,2,3,4,5]

def test_bubble_sort_duplicates():
    assert dsaria.sort.bubble_sort(arr=[4,2,2,1,3,4]) == [1,2,2,3,4,4]

def test_bubble_sort_all_equal():
    assert dsaria.sort.bubble_sort(arr=[7,7,7,7]) == [7,7,7,7]

def test_bubble_sort_floats():
    arr = [1.1, 2.2, 0.5, 2.1]
    assert dsaria.sort.bubble_sort(arr=arr) == sorted(arr)

def test_bubble_sort_strings():
    assert dsaria.sort.bubble_sort(arr=["b","a","c"]) == ["a","b","c"]

def test_bubble_sort_negative_numbers():
    arr = [-5, -1, -3, 0, 2]
    assert dsaria.sort.bubble_sort(arr=arr) == sorted(arr)

def test_bubble_sort_large_random():
    arr = [random.randint(-1000,1000) for _ in range(500)]
    sorted_arr = sorted(arr)
    assert dsaria.sort.bubble_sort(arr=arr) == sorted_arr


def test_bubble_sort_mixed_types_raises_type_error():
    with pytest.raises(TypeError):
        dsaria.sort.bubble_sort(arr=[1, "2", 3])

def test_bubble_sort_stable_property():
    class Obj:
        def __init__(self, val, order):
            self.val = val
            self.order = order
        def __gt__(self, other): return self.val > other.val
        def __lt__(self, other): return self.val < other.val
        def __eq__(self, other): return self.val == other.val
        def __repr__(self): return f"Obj({self.val},{self.order})"

    objs = [Obj(1,0), Obj(1,1), Obj(2,2), Obj(1,3)]
    sorted_objs = dsaria.sort.bubble_sort(arr=objs)
    orders = [o.order for o in sorted_objs if o.val==1]
    assert orders == [0,1,3]