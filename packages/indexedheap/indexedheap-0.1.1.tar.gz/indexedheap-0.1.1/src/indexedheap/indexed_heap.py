from abc import ABC, abstractmethod
from .heap_item import HeapItem
    
class IndexedHeap(ABC):
    """
    Abstract base class for a heap with indexed access.

    Elements are stored in a list to maintain heap order, alongside a dictionary
    that maps items to their positions. This enables efficient removal of 
    items, in addition to standard operations like insert, pop, and peek.

    Use `MinHeap` for a min-heap or `MaxHeap` for a max-heap.

    Time Complexity Overview (N = number of unique items in the heap):
    - insert: O(log(N))
    - pop: O(log(N))
    - peek: O(1)
    - remove: O(log(N))
    - count: O(1)
    - to_sorted_list: O(N * log(N))

    """

    def __init__(self, arr = None):
        """
        Initialize the heap with an optional list of items.

        Parameters:
        arr : list, optional
            Initial values to populate the heap. Duplicate items are merged
            and tracked via an internal frequency counter. All items must be
            mutually comparable according to the heap's ordering rules.

        Comparison Requirements:
        - In `MinHeap`, items must support the `<` operator.
        - In `MaxHeap`, items must support the `>` operator.
        - All elements must be comparable with one another. Mixing types like `str`
        and `int` is invalid unless custom comparison logic is provided.
        - To use custom comparison logic, implement `__lt__` (for `MinHeap`) or `__gt__`
        (for `MaxHeap`) so that items can be ordered.

        Time Complexity:
        O(N)
        """


        if arr == None:
            arr = []
        
        if not isinstance(arr, list):
            raise TypeError("arr must be a list")
        
        self.heap = []
        self.item_to_index = {}
        self.size = 0
        prev_item = None
        if len(arr) > 0:
            for item in arr:
                if prev_item:
                    is_comparable, type1, type2 = self._is_comparable(item, prev_item)
                    if not is_comparable:
                        raise TypeError(f"All items in the heap must be comparable. {type1} and {type2} are not comparable.")    
                if item in self.item_to_index:
                    idx = self.item_to_index[item]
                    self.heap[idx].frequency +=1
                else:
                    heap_item = HeapItem(item)
                    self.heap.append(heap_item)
                    self.item_to_index[item] = len(self.heap) - 1
                self.size += 1
                prev_item = item

            for i in range((len(self.heap)//2)-1, -1, -1):
                self._sift_down(i)

    @abstractmethod
    def _comes_before(self, a, b):
        """
        Determine the ordering between two heap items.

        This method is implemented by `MinHeap` and `MaxHeap` to define
        the heap's ordering rule.

        Parameters:
        a : HeapItem
            The first heap item to compare.
        b : HeapItem
            The second heap item to compare.

        Returns:
        bool
            `True` if `a` should come before `b` in the heap (i.e. higher priority),
            `False` otherwise.

        Time Complexity:
        O(1)

        """
        pass
        
    def _sift_up(self, idx = None):
        """
        Move the item at `idx` upward in the heap until the heap property is restored.

        Parameters:
        idx : int, optional
            Index of the item to sift up. Defaults to the last element.

        Returns:
        int
            The final index of the item after sifting.


        Time Complexity:
        O(log(N))

        """

        n = len(self.heap)
        if idx == None:
            idx = n-1
        if idx < 0 or idx >= n:
            raise ValueError(f"idx out of range, idx: {idx}, heap size: {len(self.heap)}")
        while idx > 0:
            parent_idx = (idx - 1) // 2
            parent_heap_item = self.heap[parent_idx]
            curr_heap_item = self.heap[idx]
            if self._comes_before(curr_heap_item, parent_heap_item):
                self.heap[idx], self.heap[parent_idx] = self.heap[parent_idx], self.heap[idx]
                self.item_to_index[curr_heap_item.value] = parent_idx
                self.item_to_index[parent_heap_item.value] = idx
                idx = parent_idx
            else:
                break
        return idx
    
    def _sift_down(self, idx = None):
        """
        Move the item at `idx` downward in the heap until the heap property is restored.

        Parameters:
        idx : int, optional
            Index of the item to sift down. Defaults to the first element.

        Returns:
        int
            The final index of the item after sifting.

        Time Complexity:
        O(log(N))

        """
        n = len(self.heap)
        if idx == None:
            idx = 0
        if idx < 0 or idx >= n:
            raise ValueError(f"idx out of range, idx: {idx}, heap size: {len(self.heap)}")
        child1_idx, child2_idx = (2 * idx + 1), (2 * idx + 2)    
        while child1_idx < n and \
            (self._comes_before(self.heap[child1_idx], self.heap[idx]) \
            or (child2_idx < n and self._comes_before(self.heap[child2_idx], self.heap[idx]))    
            ):
            child_idx = child1_idx
            child_heap_item = self.heap[child1_idx]
            if child2_idx < n and self._comes_before(self.heap[child2_idx], child_heap_item):
                child_idx = child2_idx
                child_heap_item = self.heap[child2_idx]
            curr_heap_item = self.heap[idx]
            self.heap[idx], self.heap[child_idx] = self.heap[child_idx], self.heap[idx]
            self.item_to_index[child_heap_item.value] = idx
            self.item_to_index[curr_heap_item.value] = child_idx
            idx = child_idx
            child1_idx, child2_idx = (2 * idx + 1), (2 * idx + 2)
        return idx
    
    def peek(self):
        """
        Return the top element of the heap without removing it.

        Returns
        -------
        Any or None
            The smallest/largest item depending on heap type, or None if the heap is empty.

        Time Complexity:
        O(1)
        """
        if self.heap:
            return self.heap[0].value
        else:
            return None
        
    def insert(self, item,*, count = 1):
        """
        Insert an item into the heap.

        If the item already exists, its internal frequency counter is incremented
        instead of creating a duplicate entry.

        Parameters
        ----------
        item : Any
            The value to insert. Must be comparable with existing items in the heap.
        count : int, optional
            Number of occurrences to add. Defaults to 1.

        Raises
        ------
        TypeError
            If the item is not comparable with existing items.

        Notes
        -----
        Comparison is based on the heap type:
        - `MinHeap` uses `<`
        - `MaxHeap` uses `>`

        Time Complexity:
        O(log(N))

        """

        if len(self.heap) > 0:
            is_comparable, type1, type2 = self._is_comparable(item, self.heap[0].value)
            if not is_comparable:
                raise TypeError(f"All items in the heap must be comparable. {type1} and {type2} are not comparable.")
        self.size += count
        heap_item = HeapItem(item, count)
        if item in self.item_to_index:
            idx = self.item_to_index[item]
            self.heap[idx].frequency += count
        else:
            self.heap.append(heap_item)
            self.item_to_index[item] = len(self.heap) - 1
            self._sift_up()

    def pop(self):
        """
        Remove and return the top element of the heap.

        If the root element has a frequency greater than 1, its frequency is
        decremented instead of removing the node entirely.

        Returns:
        Any
            The smallest (in MinHeap) or largest (in MaxHeap) item in the heap.

        Raises:
        IndexError
            If called on an empty heap.

        Time Complexity:
        O(log(N))

        """
        
        n = len(self.heap)
        if n == 0:
            raise IndexError("Pop from empty heap")
        self.size -= 1
        root: HeapItem = self.heap[0]
        if root.frequency > 1:
            root.frequency -= 1
            return root.value
        else:
            if n > 1:
                last_heap_item = self.heap[n-1]
                self.heap[0], self.heap[n-1] = self.heap[n-1], self.heap[0]
                self.item_to_index[last_heap_item.value] = 0
            res = self.heap.pop()
            del self.item_to_index[res.value]
            if len(self.heap) > 1:
                self._sift_down()
            return res.value
    
    def _item_in_heap(self, item):
        """
        Check if an item exists in the heap.

        Returns a tuple of (found, heap_item, index):
            found (bool): True if the item is in the heap and its index is valid.
            heap_item (HeapItem or None): The HeapItem instance if found, else None.
            index (int or None): The index of the item in the heap array if found, else None.

        Notes:
        Under normal operation, the index dictionary (`self.item_to_index`) and heap list (`self.heap`)
        should always be in sync. This method defensively removes any stale entries that may occur,
        for example if a user manually modifies `self.heap` or `self.item_to_index`, or in the event of
        an unexpected interruption during heap operations.

        Time Complexity: O(1)

        """
        if item not in self.item_to_index:
            return (False, None, None)
        idx = self.item_to_index[item]
        if 0 <= idx < len(self.heap):
            return (True, self.heap[idx], idx)
        else:
            del self.item_to_index[item]
            return (False, None, None)
    
    def remove(self, item, *, count = 1, strict = True):
        """
        Remove a specified number of occurrences of an item from the heap.

        Parameters
        ----------
        item : Any
            The value to remove from the heap.
        count : int, optional
            The number of occurrences to remove. Defaults to 1. Must be at least 1.
        strict : bool, default True
            If True, raises a ValueError when the item is not in the heap or
            if the requested count exceeds the item's frequency.
            If False, removes as many occurrences as possible (up to `count`) without
            raising an error. Returns False only if the item was not found.

        Returns
        -------
        bool
            True if the removal was successful. False only if the item was not found
            and `strict=False`.

        Raises
        ------
        ValueError
            If `strict=True` and the item is not in the heap, or if `count` is invalid.

        Notes
        -----
        - If the item has a frequency greater than the removal count, its frequency
        is decremented instead of removing the heap node entirely.
        - If the item’s frequency equals the removal count, the heap node is removed
        and the heap property is restored via `_sift_down` and `_sift_up`.

        Time Complexity:
        O(log(N))

        """

        found_in_heap, heap_item, idx = self._item_in_heap(item)
        if not found_in_heap:
            if strict == False:
                return False
            else:
                raise KeyError(f"{item} not in heap")
            
        if not isinstance(count, int):
            raise ValueError("The count must be an integer")
        if count < 1:
            raise ValueError("Count must be at least 1")
        if count > heap_item.frequency:
            if strict == False:
                count = heap_item.frequency
            else: 
                raise ValueError(f"Count must be less than or equal to item frequency ({heap_item.frequency})")
        if count < heap_item.frequency:
            heap_item.frequency -= count
            self.size -= count
        else:
            last_idx = len(self.heap) -1
            if idx != last_idx:
                last_heap_item = self.heap[last_idx]
                self.heap[idx], self.heap[last_idx] = self.heap[last_idx], self.heap[idx]
                self.item_to_index[last_heap_item.value] = idx
            self.heap.pop()
            del self.item_to_index[heap_item.value]
            self.size -= heap_item.frequency
            if idx != last_idx:
                new_idx = self._sift_down(idx)
                self._sift_up(new_idx)
        return True

    def __len__(self):
        """
        Return the total number of items in the heap, including duplicates.

        Returns:
        int
            The sum of frequencies of all items in the heap.
        
        Time Complexity:
        O(1)

        """
        return self.size
    
    def __bool__(self):
        """
        Return True if the heap contains any items, False otherwise.

        Returns:
        bool
            True if the heap is non-empty, False if empty.
        
        Time Complexity:
        O(1)

        """
        return bool(self.heap)
    
    def count(self, item):
        """
        Return the frequency of a given item in the heap.

        Parameters:
        item : Any
            The item to count occurrences of.

        Returns:
        int
            The number of times `item` appears in the heap (its frequency). Returns 0 if not present.

        Time Complexity:
        O(1)
             
        """
        found_in_heap, heap_item, _ = self._item_in_heap(item)
        if found_in_heap:
            return heap_item.frequency
        else:
            return 0

    def internal_heap(self):
        """
        Return a list representation of the internal heap structure.

        Each element is returned as a tuple `(value, frequency)`.

        Returns:
        list of tuples
            A list of `(value, frequency)` tuples representing the heap in its
            current internal order (not necessarily sorted order).
        
        Time Complexity:
        O(N)
        """
        return [(heap_item.value, heap_item.frequency) for heap_item in self.heap]
    
    def _copy(self):
        """
        Create a shallow copy of the heap.

        Returns:
        MinHeap | MaxHeap
            A new heap instance of the same type with the same items,
            frequencies, and internal index mapping. Modifying the copy
            does not affect the original heap.

        Notes
        -----
        This is primarily used for iteration or internal operations
        where a temporary copy of the heap is needed.

        Time Complexity:
        O(N)
        """
        heap_copy = [HeapItem(heap_item.value, heap_item.frequency) for heap_item in self.heap]
        item_to_index_copy = {heap_copy[index].value: index for index in range(len(heap_copy))}
        size_copy = self.size
        new_heap = self.__class__()
        new_heap.heap, new_heap.item_to_index, new_heap.size = heap_copy, item_to_index_copy, size_copy
        return new_heap
    
    def __iter__(self):
        """
        Iterate over the heap elements in sorted order.

        Returns:
        Iterator[Any]
            Yields items from the heap one by one in order determined
            by the heap type (smallest to largest for MinHeap, largest
            to smallest for MaxHeap).

        Notes:
        Iteration is performed on a copy of the heap by repeatedly popping
        the root, so the original heap remains unchanged.

        Time Complexity:
        O(N)

        """
        copy = self._copy()
        while len(copy) > 0:
            yield copy.pop()

    def to_sorted_list(self):
        """
        Return a list of all heap elements in sorted order.

        Returns:
        list
            A list of items in the heap sorted according to the heap type
            (MinHeap: ascending, MaxHeap: descending).

        Notes:
        Internally uses the `__iter__` method.

        Time Complexity:
        O(N * log(N))

        """
        return list(self)
    
    def __str__(self):
        """
        Return a string representation of the heap suitable for printing.

        This makes printing the heap display its items and frequencies as a list,
        rather than the default class instance representation.

        Returns
        -------
        str
            A string showing all items in the heap along with their frequencies,
            as produced by `internal_heap()`.
        
        Time Complexity:
        O(N)

        """
        return str(self.internal_heap())
    
    def __contains__(self, item):
        """
        Check if an item exists in the heap.

        This allows using the `in` operator with the heap, e.g. `item in heap`.

        Parameters:
        item : Any
            The item to check for in the heap.

        Returns:
        bool
            True if the item exists in the heap, False otherwise.

        Time Complexity:
        O(1)
        """
        found, _, _ = self._item_in_heap(item)
        return found
        
    @abstractmethod
    def _is_class(self, other):
        """
        Check if another object is of the same heap class.

        Parameters
        ----------
        other : Any
            The object to check.

        Returns
        -------
        bool
            True if `other` is an instance of the same heap subclass
            (e.g., MinHeap or MaxHeap), False otherwise.

        """
        pass
    
    def __eq__(self, other):
        """
        Compare two heaps for strict equality.

        Returns:
        bool
            True if and only if:

            - `other` is an instance of the same heap subclass (e.g. both MinHeap),
            - Both heaps contain the same number of internal nodes (unique items),
            - Each position `i` in the internal heap array contains a HeapItem with
            the same value *and* frequency,
            - And the internal `item_to_index` mappings agree for all values.

        Notes:
        This is a structural equality check. It verifies not only that both
        heaps contain the same multiset of values, but that they have the same
        internal layout and index mapping. Heaps with equal contents but different
        tree shapes (due to different insertion orders) will be considered unequal.

        Time Complexity:
        O(N)
        """
        if not self._is_class(other):
            return False
        elif len(self.heap) != len(other.heap):
            return False
        for i in range(len(self.heap)):
            if self.heap[i] != other.heap[i]:
                return False
            try:
                if self.item_to_index[self.heap[i].value] != other.item_to_index[other.heap[i].value]:
                    return False
            except KeyError:
                return False
            
            if self.heap[i].frequency != other.heap[i].frequency:
                return False
        return True
    
    @abstractmethod
    def _is_comparable(self, a, b):
        """
        Determine whether two items can be compared according to the heap's ordering rules.

        Parameters:
        a : Any
            The first item.
        b : Any
            The second item.

        Returns:
        tuple
            (is_comparable, type(a), type(b))

            `is_comparable` is True if the items can be compared according 
            to the heap rules, False otherwise.

        Time Complexity:
        O(1)

        """
        pass
    
class MinHeap(IndexedHeap):

    """
    Min-heap implementation of the IndexedHeap class.

    Elements are ordered such that the smallest element is at the root.

    """
    def _comes_before(self, a, b):
        """
        Determine the ordering between two items for a min-heap.

        Parameters:
        a : HeapItem
            The first heap item to compare.
        b : HeapItem
            The second heap item to compare.

        Returns:
        bool
            True if `a` should come before `b` in the min-heap (i.e. a < b).

        Time Complexity:
        O(1)
        """
        return a < b
    
    def _is_comparable(self, a, b):
        """
        Check if two items can be compared using `<`.

        Parameters:
        a : Any
            First item to check.
        b : Any
            Second item to check.

        Returns:
        tuple
            (is_comparable, type(a), type(b)), where `is_comparable` is True
            if both items support `<` comparisons, False otherwise.
        
        Time Complexity:
        O(1)

        """
        try:
            a < b
            b < a
            return (True, type(a), type(b))
        except TypeError:
            return (False, type(a), type(b))
    
    def _is_class(self, other):
        """
        Check if another object is a MinHeap instance.

        Parameters:
        other : Any
            The object to check.

        Returns:
        bool
            True if `other` is an instance of MinHeap, False otherwise.

        Time Complexity:
        O(1)

        """
        if isinstance(other, MinHeap):
            return True
        else:
            return False

class MaxHeap(IndexedHeap):
    """
    Max-heap implementation of the IndexedHeap class.

    Elements are ordered such that the greatest element is at the root.

    """
    def _comes_before(self, a, b):
        """
        Determine the ordering between two items for a max-heap.

        Parameters:
        a : HeapItem
            The first heap item to compare.
        b : HeapItem
            The second heap item to compare.

        Returns:
        bool
            True if `a` should come before `b` in the max-heap (i.e. a > b).
        
        Time Complexity:
        O(1)

        """
        return a > b
    
    def _is_comparable(self, a, b):
        """
        Check if two items can be compared using `>`.

        Parameters
        ----------
        a : Any
            First item to check.
        b : Any
            Second item to check.

        Returns
        -------
        tuple
            (is_comparable, type(a), type(b)), where `is_comparable` is True
            if both items support `>` comparisons, False otherwise.
        
        Time Complexity:
        O(1)

        """
        try:
            a > b
            b > a
            return (True, type(a), type(b))
        except TypeError:
            return (False, type(a), type(b))
    
    def _is_class(self, other):
        """
        Check if another object is a MaxHeap instance.

        Parameters:
        other : Any
            The object to check.

        Returns:
        bool
            True if `other` is an instance of MaxHeap, False otherwise.

        Time Complexity:
        O(1)
            
        """
        if isinstance(other, MaxHeap):
            return True
        else:
            return False
