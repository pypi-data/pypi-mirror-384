# Indexed Heap

This package provides a pure-Python implementation of **MinHeap** and **MaxHeap** that extend standard heap functionality with support for:
- Efficient removal of any value.
- Removal of multiple occurrences of a value in a single operation.
- Insertion of multiple occurrences of a value in a single operation.
- Tracking frequency to handle duplicate values.
- Iteration in sorted order (ascending for MinHeap, descending for MaxHeap) without modifying the heap.
- Container-like behavior with implementations for len(), in, equality checks, and truthiness.

## Features & Time Complexity

| Operation | Description | Time Complexity |
|-----------|-------------|----------------|
| `insert(value, count=1)` | Insert a value (or multiple occurrences). If the value already exists, frequency is incremented | O(log N) for a new value; O(1) for an existing value |
| `pop()` | Remove and return the root value (min or max) | O(log N) |
| `peek()` | Return the root value without removing it | O(1) |
| `remove(value, *, count=1, strict=True)` | Remove a value (or multiple occurrences). | Removing fewer than the total occurrences is O(1); removing the last occurrence is O(log N) |
| `count(value)` | Return the frequency of a value | O(1) |
| `to_sorted_list()` | Return a fully sorted list of all values without modifying the heap | O(N log N) |
| `len(heap)` | Number of elements in the heap | O(1) |
| `value in heap` | Membership check | O(1) |
| `iter(heap)` | Iterate over values in sorted order | O(N log N) |
| `bool(heap)` | Check if heap is non-empty | O(1) |
| `heap1 == heap2` | Check heaps for equality | O(N) |

**Notes:**  
- Equality checks (`heap1 == heap2`) are **structural and strict**. Heaps with identical values but different insertion orders (resulting in different internal layouts) will **not** be considered equal.
- `count` refers to the number of occurrences to insert or remove from the heap, defaults to 1.

 ## Installation

```bash
pip install indexedheap
```

## Quick Reference

### Create an empty heap
```python
from indexedheap import MinHeap, MaxHeap

min_heap = MinHeap() # Heap is empty.
max_heap = MaxHeap() # Heap is empty.
```

### Create a heap from a list
```python
from indexedheap import MinHeap, MaxHeap

arr = [1,2,3]
min_heap = MinHeap(arr) # Heap contains: [(value: 1, frequency: 1), (value: 2, frequency: 1), (value: 3, frequency: 1)].
max_heap = MaxHeap(arr) # Heap contains: [(value: 3, frequency: 1), (value: 1, frequency: 1), (value: 2, frequency: 1)].
```

### Insert a value
```python
from indexedheap import MinHeap, MaxHeap

min_heap = MinHeap() # Heap is empty.
min_heap.insert(1) # Heap contains: [(value: 1, frequency: 1)].

max_heap = MaxHeap() # Heap is empty.
max_heap.insert(1) # Heap contains: [(value: 1, frequency: 1)].
```

### Insert a value multiple times
```python
from indexedheap import MinHeap, MaxHeap

min_heap = MinHeap() # Heap is empty.
min_heap.insert(1, count=2) # Heap contains: [(value: 1, frequency: 2)].

max_heap = MaxHeap() # Heap is empty.
max_heap.insert(1, count=2) # Heap contains: [(value: 1, frequency: 2)].
```

### Remove a value
```python
from indexedheap import MinHeap, MaxHeap

min_heap = MinHeap([1]) # Heap contains: [(value: 1, frequency: 1)].
min_heap.remove(1) # Heap is empty.

max_heap = MaxHeap([1]) # Heap contains: [(value: 1, frequency: 1)].
max_heap.remove(1) # Heap is empty.
```

### Remove multiple occurrences of a value
```python
from indexedheap import MinHeap, MaxHeap

min_heap = MinHeap([1, 1]) # Heap contains: [(value: 1, frequency: 2)].
min_heap.remove(1, count=2) # Heap is empty.

max_heap = MaxHeap([1, 1]) # Heap contains: [(value: 1, frequency: 2)].
max_heap.remove(1, count=2) # Heap is empty.
```

### Remove all occurrences of a value
```python
from indexedheap import MinHeap, MaxHeap

min_heap = MinHeap([1, 1]) # Heap contains: [(value: 1, frequency: 2)].
min_heap.remove(1, count=min_heap.count(1)) # Heap is empty.

max_heap = MaxHeap([1, 1]) # Heap contains: [(value: 1, frequency: 2)].
max_heap.remove(1, count=max_heap.count(1)) # Heap is empty.
```

### Optimistically remove a value
The strict flag controls whether removing a non-existent value should raise an error:
- strict=True (default) -> raise a KeyError if the value isn't in the heap
- strict=False -> attempt to remove the value (up to the given count, if provided), but do nothing if it isn't present
```python
from indexedheap import MinHeap, MaxHeap

# Value not present — no error
min_heap = MinHeap([]) # Heap is empty.
min_heap.remove(1) # Raises KeyError.
min_heap.remove(1, strict=False) # Heap is empty, no error.

# Value present, but count exceeds frequency — no error
min_heap = MinHeap([1, 1]) # Heap contains: [(value: 1, frequency: 2)].
min_heap.remove(1, count=3) # Raises ValueError.
min_heap.remove(1, count=3, strict=False) # Heap is empty, no error.

# Same for MaxHeap
max_heap = MaxHeap([]) # Heap is empty.
max_heap.remove(1) # Raises KeyError.
max_heap.remove(1, strict=False) # Heap is empty, no error.

max_heap = MaxHeap([1, 1]) # Heap contains: [(value: 1, frequency: 2)].
max_heap.remove(1, count=3) # Raises ValueError.
max_heap.remove(1, count=3, strict=False) # Heap is empty, no error.
```

### Peek root value
```python
from indexedheap import MinHeap, MaxHeap

min_heap = MinHeap([1, 2]) # Heap contains: [(value: 1, frequency: 1), (value: 2, frequency: 1)].
min_heap.peek() # Returns 1; Heap unchanged.

max_heap = MaxHeap([1, 2]) # Heap contains: [(value: 2, frequency: 1), (value: 1, frequency: 1)].
max_heap.peek() # Returns 2; Heap unchanged.
```

### Pop root value
```python
from indexedheap import MinHeap, MaxHeap

min_heap = MinHeap([1, 2]) # Heap contains: [(value: 1, frequency: 1), (value: 2, frequency: 1)].
min_heap.pop() # Returns 1; Heap contains: [(value: 2, frequency: 1)].

max_heap = MaxHeap([1, 2]) # Heap contains: [(value: 2, frequency: 1), (value: 1, frequency: 1)].
max_heap.pop() # Returns 2; Heap contains: [(value: 1, frequency: 1)].
```

### Get frequency (count) of value
```python
from indexedheap import MinHeap, MaxHeap

# Value present
min_heap = MinHeap([1, 1]) # Heap contains: [(value: 1, frequency: 2)].
min_heap.count(1) # Returns 2; Heap unchanged.

max_heap = MaxHeap([1, 1]) # Heap contains: [(value: 1, frequency: 2)].
max_heap.count(1) # Returns 2; Heap unchanged.

# Value not present
min_heap = MinHeap() # Heap is empty.
min_heap.count(1) # Returns 0; Heap unchanged.

max_heap = MaxHeap() # Heap is empty.
max_heap.count(1) # Returns 0; Heap unchanged.
```

### Get heap size (including duplicates)
```python
from indexedheap import MinHeap, MaxHeap

min_heap = MinHeap([1, 1]) # Heap contains: [(value: 1, frequency: 2)].
len(min_heap) # Returns 2; Heap unchanged.

min_heap = MinHeap([1, 2]) # Heap contains: [(value: 1, frequency: 1), (value: 2, frequency: 1)].
len(min_heap) # Returns 2; Heap unchanged.

max_heap = MaxHeap([1, 1]) # Heap contains: [(value: 1, frequency: 2)].
len(max_heap) # Returns 2; Heap unchanged.

max_heap = MaxHeap([1, 2]) # Heap contains: [(value: 2, frequency: 1), (value: 1, frequency: 1)].
len(max_heap) # Returns 2; Heap unchanged.
```

### Iterate heap contents in sorted order
```python
from indexedheap import MinHeap, MaxHeap

min_heap = MinHeap([1, 3, 2]) # Heap contains: [(value: 1, frequency: 1), (value: 3, frequency: 1), (value: 2, frequency: 1)].
for value in min_heap:
    print(value)
# >>> 1
# >>> 2
# >>> 3
# Iteration yields values in sorted order; Heap unchanged.

max_heap = MaxHeap([1, 3, 2]) # Heap contains: [(value: 3, frequency: 1), (value: 1, frequency: 1), (value: 2, frequency: 1)].
for value in max_heap:
    print(value)
# >>> 3
# >>> 2
# >>> 1
# Iteration yields values in sorted order; Heap unchanged.
```

### Get heap contents as a sorted list
```python
from indexedheap import MinHeap, MaxHeap

min_heap = MinHeap([1, 3, 2]) # Heap contains: [(value: 1, frequency: 1), (value: 3, frequency: 1), (value: 2, frequency: 1)].
min_heap.to_sorted_list() # Returns [1, 2, 3]; Heap unchanged.

max_heap = MaxHeap([1, 3, 2]) # Heap contains: [(value: 3, frequency: 1), (value: 1, frequency: 1), (value: 2, frequency: 1)].
max_heap.to_sorted_list() # Returns [3, 2, 1]; Heap unchanged.

# list(heap) also returns items in sorted order because __iter__ yields items sorted.
list(min_heap)  # Returns [1, 2, 3]; Heap unchanged.
list(max_heap)  # Returns [3, 2, 1]; Heap unchanged.
```

### Test Membership
```python
from indexedheap import MinHeap, MaxHeap

min_heap = MinHeap([1]) # Heap contains: [(value: 1, frequency: 1)].
1 in min_heap # Returns True.
0 in min_heap # Returns False.

max_heap = MaxHeap([1]) # Heap contains: [(value: 1, frequency: 1)].
1 in max_heap # Returns True.
0 in max_heap # Returns False.
```
