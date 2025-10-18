import pytest
import random
import dsaria.sort

def test_counting_sort_normal_case():
    arr = [3, 1, 4, 1, 5, 9, 2, 6, 5]
    assert dsaria.sort.counting_sort(arr=arr) == sorted(arr)

def test_counting_sort_empty_list():
    assert dsaria.sort.counting_sort(arr=[]) == []

def test_counting_sort_single_element():
    assert dsaria.sort.counting_sort(arr=[42]) == [42]

def test_counting_sort_single_repeated_value():
    arr = [7] * 10
    assert dsaria.sort.counting_sort(arr=arr) == arr

def test_counting_sort_duplicates():
    arr = [2, 3, 2, 1, 4, 1, 1]
    assert dsaria.sort.counting_sort(arr=arr) == sorted(arr)

def test_counting_sort_reverse_sorted():
    arr = [5, 4, 3, 2, 1, 0]
    assert dsaria.sort.counting_sort(arr=arr) == sorted(arr)

def test_counting_sort_already_sorted():
    arr = [0, 1, 2, 3, 4, 5]
    assert dsaria.sort.counting_sort(arr=arr) == arr

def test_counting_sort_negative_raises_value_error():
    with pytest.raises(ValueError):
        dsaria.sort.counting_sort(arr=[1, 2, -3])

def test_counting_sort_float_raises_type_error():
    with pytest.raises(TypeError):
        dsaria.sort.counting_sort(arr=[1, 2, 3.5])

def test_counting_sort_string_raises_type_error():
    with pytest.raises(TypeError):
        dsaria.sort.counting_sort(arr=[1, 2, "3"])

def test_counting_sort_large_random():
    arr = [random.randint(0, 1000) for _ in range(1000)]
    sorted_arr = sorted(arr)
    assert dsaria.sort.counting_sort(arr=arr) == sorted_arr

def test_counting_sort_all_zeroes():
    arr = [0] * 50
    assert dsaria.sort.counting_sort(arr=arr) == arr

def test_counting_sort_single_zero():
    arr = [0]
    assert dsaria.sort.counting_sort(arr=arr) == [0]

def test_counting_sort_stress_large_range():
    arr = [random.randint(0, 5000) for _ in range(2000)]
    sorted_arr = sorted(arr)
    assert dsaria.sort.counting_sort(arr=arr) == sorted_arr