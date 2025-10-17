import pytest
from indexedheap import MaxHeap, MinHeap
import math

@pytest.fixture
def arr():
    return [1, -10, 50, 2, 25, 642, 1.32, 8, -1000, math.pi]

@pytest.fixture
def duplicate_value_arr():
    duplicate_value = 1
    arr_length = 10
    return (duplicate_value, [duplicate_value] * arr_length)


@pytest.mark.parametrize("HeapClass", [MinHeap, MaxHeap])
class TestHeapCreation:
    def test_create_empty_heap(self, HeapClass):
        heap = HeapClass()
        assert len(heap) == 0
        assert not heap
        assert heap.peek() is None
        assert heap.to_sorted_list() == []
        assert list(heap) == []

    def test_create_heap_invalid_arr(self, HeapClass):
        with pytest.raises(TypeError):
            HeapClass(arr = "helloworld")

    def test_create_heap_non_comparable_items(self, HeapClass):
        with pytest.raises(TypeError):
            HeapClass(arr=[1, "helloworld"])

    def test_create_heap_with_valid_arr(self, HeapClass, arr): 
        heap = HeapClass(arr)
        assert len(heap) == len(arr)
        for value in arr:
            assert arr.count(value) == heap.count(value)
        if HeapClass is MinHeap:
            sorted_arr = sorted(arr)
            assert heap.peek() == sorted_arr[0]
            assert heap.to_sorted_list() == sorted(arr)
        else:
            sorted_arr = sorted(arr, reverse = True)
            assert heap.peek() == sorted_arr[0]
            assert heap.to_sorted_list() == sorted(arr, reverse=True)


@pytest.mark.parametrize("HeapClass", [MinHeap, MaxHeap])
class TestInsert:
    def test_insert_non_comparable_items_int_then_string(self, HeapClass):
        heap = HeapClass()
        heap.insert(1)
        with pytest.raises(TypeError):
            heap.insert("helloworld")
    
    def test_insert_non_comparable_items_string_then_int(self, HeapClass):
        heap = HeapClass()
        heap.insert("helloworld")
        with pytest.raises(TypeError):
            heap.insert(1)
    
    def test_insert_duplicates(self, HeapClass):
        heap = HeapClass()
        value = 1
        expected_count = 0
        for _ in range(5):
            heap.insert(value)
            expected_count += 1
            assert len(heap) == expected_count
            assert heap.count(value) == expected_count
        
        additional_count = 10
        heap.insert(1, count = additional_count)
        expected_count += additional_count
        assert len(heap) == expected_count
        assert heap.count(value) == expected_count
    
    def test_insert_unique(self, HeapClass):
        heap = HeapClass()
        for i in range(1, 10):
            heap.insert(i)
            assert heap.count(i) == 1
            assert len(heap) == i

@pytest.mark.parametrize("HeapClass", [MinHeap, MaxHeap])
class TestPeek:
    def test_peek_empty_heap(self, HeapClass, arr):
        heap = HeapClass()
        assert heap.peek() == None
    
    def test_peek(self, HeapClass, arr):
        heap = HeapClass(arr)
        if HeapClass == MinHeap:
            arr.sort()
        else:
            arr.sort(reverse=True)
        assert heap.peek() == arr[0]

@pytest.mark.parametrize("HeapClass", [MinHeap, MaxHeap])
class TestPop:
    def test_pop_from_empty_heap(self, HeapClass):
        heap = HeapClass()
        with pytest.raises(IndexError):
            heap.pop()
    
    def test_pop_no_duplicates(self, HeapClass, arr):
        heap = HeapClass(arr)
        expected_heap_length = len(arr)
        if HeapClass == MinHeap:
            arr.sort()
        else:
            arr.sort(reverse=True)
        
        for i in range(len(arr)):
            assert arr[i] == heap.pop()
            expected_heap_length -= 1
            assert len(heap) == expected_heap_length
            assert heap.count(arr[i]) == 0
        with pytest.raises(IndexError):
            heap.pop()

    def test_pop_duplicates(self, HeapClass, duplicate_value_arr):
        value, arr = duplicate_value_arr
        duplicate_count = len(arr)
        heap = HeapClass(arr)

        for _ in range(duplicate_count):
            assert value == heap.pop()
            duplicate_count -= 1
            assert len(heap) == duplicate_count
            assert heap.count(value) == duplicate_count
        with pytest.raises(IndexError):
            heap.pop()

@pytest.mark.parametrize("HeapClass", [MinHeap, MaxHeap])
class TestRemove:
    def test_remove_item_strict_off(self, HeapClass, arr):
        heap = HeapClass(arr)
        size_before = len(heap)
        assert heap.remove(arr[0], strict = False) == True
        size_after = len(heap)
        assert size_before == size_after+1
        assert heap.count(arr[0]) == 0
        assert heap.remove(arr[0], strict = False) == False

    def test_remove_item_all_duplicates(self, HeapClass, duplicate_value_arr):
        _, arr = duplicate_value_arr
        heap = HeapClass(arr)
        size = len(arr)
        assert heap.remove(arr[0], count = size) == True
        assert len(heap) == 0
        assert heap.count(arr[0]) == 0     
    
    def test_remove_item_count_not_int(self, HeapClass, arr):
        heap = HeapClass(arr)
        with pytest.raises(ValueError):
            heap.remove(arr[0], count = 1.5)

        with pytest.raises(ValueError):
            heap.remove(arr[0], count = "helloworld")
    
    def test_remove_item_count_below_1(self, HeapClass, arr):
        heap = HeapClass(arr)
        with pytest.raises(ValueError):
            heap.remove(arr[0], count = 0)

        with pytest.raises(ValueError):
            heap.remove(arr[0], count = -1)

    def test_remove_item_exceeding_frequency_strict(self, HeapClass, duplicate_value_arr):
        _, arr = duplicate_value_arr
        heap = HeapClass(arr)
        size = len(arr)
        with pytest.raises(ValueError):
            heap.remove(arr[0], count = size + 1) == True
        assert heap.count(arr[0]) == size
        assert len(heap) == size

    def test_remove_item_exceeding_frequency_not_strict(self, HeapClass, duplicate_value_arr):
        _, arr = duplicate_value_arr
        heap = HeapClass(arr)
        size = len(arr)
        assert heap.remove(arr[0], count = size + 1, strict = False) == True
        assert len(heap) == 0
        assert heap.count(arr[0]) == 0      
    
    def test_remove_item_not_in_heap_strict_on(self, HeapClass, arr):
        heap = HeapClass(arr)
        with pytest.raises(KeyError):
            value_to_remove = "#"
            while value_to_remove in heap:
                value_to_remove += "#"
            heap.remove(value_to_remove)

@pytest.mark.parametrize("HeapClass", [MinHeap, MaxHeap])
class TestToSortedList:
    def test_to_sorted_list_empty_heap(self, HeapClass):
        heap = HeapClass()
        assert heap.to_sorted_list() == []

    def test_to_sorted_list(self, HeapClass, arr):
        heap = HeapClass(arr)
        if HeapClass == MinHeap:
            arr.sort()
        else:
            arr.sort(reverse=True)
        assert heap.to_sorted_list() == arr

@pytest.mark.parametrize("HeapClass", [MinHeap, MaxHeap])
class TestEquality:
    def test_equal_heaps_same_elements_same_order(self, HeapClass, arr):
        heap1 = HeapClass(arr)
        heap2 = HeapClass(arr)
        assert heap1 == heap2

    def test_not_equal_heaps_same_elements_different_order(self, HeapClass, arr):
        heap1 = HeapClass(arr)
        heap2 = HeapClass(list(reversed(arr))) 
        assert heap1 != heap2  

    def test_not_equal_heaps_different_sizes(self, HeapClass, arr):
        heap1 = HeapClass(arr)
        heap2 = HeapClass(arr + [1])
        assert heap1 != heap2

    def test_not_equal_heaps_same_size_different_elements(self, HeapClass, arr, duplicate_value_arr):
        heap1 = HeapClass(arr)
        heap2 = HeapClass(duplicate_value_arr[1])
        assert heap1 != heap2
