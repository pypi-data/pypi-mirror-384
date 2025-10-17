class HeapItem:
    def __init__(self, item, frequency = 1):
        self.value = item
        self.frequency = frequency

    def __eq__(self, other):
        return self.value == other.value
    
    def __lt__(self, other):
        return self.value < other.value
    
    def __gt__(self, other):
        return self.value > other.value
    
    def __hash__(self):
        return hash(self.value)