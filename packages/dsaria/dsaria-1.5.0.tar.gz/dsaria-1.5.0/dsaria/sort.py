from typing import List, Any
import random

def bubble_sort(*, arr: List[Any]) -> List[Any]:
    """
    Sorts a list in ascending order using the bubble sort algorithm.
    Bubble sort swaps adjacent elements if they are in the wrong order.
    The implementation below is optimized so that if no swaps occur in the inner loop,
    the outer loop breaks.

    Args:
        arr (List[Any]): A list of comparable elements. 
        If you're passing in a list of objects, make sure that the comparison methods, such as __gt__(self, other), are defined.

    Returns:
        List[Any]: The sorted list in ascending order.

    Example:
        >>> bubble_sort([3, 1, 2])
        [1, 2, 3]

    Stable: Yes
    In-Place: Yes
    Space complexity: O(1)

    Time Complexity:
        Best case: O(n)
        Worst case: O(n^2)
        Average case: O(n^2)

    """
    if arr:
        list_type = type(arr[0])
        for val in arr:
            if not isinstance(val, list_type): raise TypeError("All elements in the input array must be the same data type.")

    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        
        if not swapped: break

    return arr

def counting_sort(*, arr: List[int]) -> List[int]:
    """
    Sorts a list of non-negative integers in ascending order using the counting sort algorithm.

    Counting sort counts the occurrences of each value in the input list and uses
    this information to construct the sorted output. This algorithm is efficient for
    sorting integers when the range of input values is not significantly larger than
    the number of elements.

    Args:
        arr (List[int]): A list of non-negative integers to sort.

    Returns:
        List[int]: A new list containing the sorted elements.

    Raises:
        TypeError: If any element in the input list is not an integer.
        ValueError: If any integer in the input list is negative.

    Example:
        >>> counting_sort(arr=[3, 1, 2, 1, 0])
        [0, 1, 1, 2, 3]

    Stable: Yes 
    In-Place: No

    Time Complexity:
        O(n + k), where n is the number of elements and k is the range of input values.

    Space Complexity:
        O(k), where k is the range of input values.
        
    """
    if len(arr) == 0: return arr
    for num in arr: 
        if not isinstance(num, int): 
            raise TypeError("All elements in the input array must be integers.")
    if min(arr) < 0: raise ValueError("Counting sort cannot take negative integers")

    num_vals = max(arr) +1 
    count = [0] * num_vals
    for num in arr: count[num] += 1
    sorted_arr = []
    for i in range(len(count)): sorted_arr.extend([i] * count[i])
    return sorted_arr

def bogosort(*, arr: List[Any]) -> List[Any]:
    """
    Sorts a list in ascending order using bogosort/random sort

    Bogosort shuffles the list until it happens to be sorted

    Args:
        arr (List[int]): A list to sort.

    Returns:
        List[int]: A new list containing the sorted elements.

    Example:
        >>> bogosort(arr=[3, 1, 2])
        [1, 2, 3]

    Stable: No
    In-Place: Yes
    Space Complexity: O(1)
    
    Time Complexity:
        Best case: O(n)
        Average/Worst case: O(n! * n)
    """
    if arr:
        list_type = type(arr[0])
        for val in arr:
            if not isinstance(val, list_type): raise TypeError("All elements in the input array must be the same data type.")
            
    def is_sorted(arr: List[Any]) -> bool:
        """Check if the list is sorted in ascending order."""
        return all(arr[i] <= arr[i + 1] for i in range(len(arr) - 1))
    
    while not is_sorted(arr=arr):
        random.shuffle(arr)

    return arr
