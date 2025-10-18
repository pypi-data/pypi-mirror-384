import pytest
import random
import dsaria.sort

def test_bogosort_normal_cases():
    assert dsaria.sort.bogosort(arr=[3, 1, 2]) == [1, 2, 3]
    assert dsaria.sort.bogosort(arr=[5, 2, 4, 1, 3]) == [1, 2, 3, 4, 5]

def test_bogosort_single_element():
    assert dsaria.sort.bogosort(arr=[42]) == [42]

def test_bogosort_empty_list():
    assert dsaria.sort.bogosort(arr=[]) == []

def test_bogosort_already_sorted():
    assert dsaria.sort.bogosort(arr=[1, 2, 3, 4]) == [1, 2, 3, 4]

def test_bogosort_duplicates():
    arr = [2, 1, 2, 1]
    assert dsaria.sort.bogosort(arr=arr) == [1, 1, 2, 2]

def test_bogosort_all_equal():
    assert dsaria.sort.bogosort(arr=[9, 9, 9, 9]) == [9, 9, 9, 9]

def test_bogosort_with_floats():
    arr = [3.3, 1.1, 2.2]
    assert dsaria.sort.bogosort(arr=arr) == sorted(arr)

def test_bogosort_with_strings():
    arr = ["b", "a", "c"]
    assert dsaria.sort.bogosort(arr=arr) == ["a", "b", "c"]

def test_bogosort_with_negative_numbers():
    arr = [-1, -5, -3, 0, 2]
    assert dsaria.sort.bogosort(arr=arr) == sorted(arr)

def test_bogosort_small_random_case():
    arr = [random.randint(0, 5) for _ in range(4)]
    assert dsaria.sort.bogosort(arr=arr) == sorted(arr)

def test_bogosort_mixed_types_raises_type_error():
    with pytest.raises(TypeError):
        dsaria.sort.bogosort(arr=[1, "2", 3])

def test_bogosort_inconsistent_types_objects():
    class A: pass
    class B: pass
    with pytest.raises(TypeError):
        dsaria.sort.bogosort(arr=[A(), B()])

def test_bogosort_custom_objects_comparable():
    class Obj:
        def __init__(self, val):
            self.val = val
        def __lt__(self, other): return self.val < other.val
        def __le__(self, other): return self.val <= other.val
        def __repr__(self): return f"Obj({self.val})"

    objs = [Obj(3), Obj(1), Obj(2)]
    sorted_objs = dsaria.sort.bogosort(arr=objs)
    assert [o.val for o in sorted_objs] == [1, 2, 3]

def test_bogosort_eight_elements_nearly_sorted():
    arr = [1, 2, 3, 4, 6, 5, 7, 8]
    original = arr.copy()

    sorted_result = dsaria.sort.bogosort(arr=arr)

    assert sorted_result == sorted(original)
    assert sorted(sorted_result) == sorted(original)

def test_bogosort_no_mutation_on_failure():
    arr = [1, 2, "3"]
    with pytest.raises(TypeError):
        dsaria.sort.bogosort(arr=arr)
