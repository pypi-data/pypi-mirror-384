import heapq

class Node:
    def __init__(self, freq, word=None):
        self.freq = freq
        self.word = word
        self.left = None
        self.right = None
        self.id = None  # unique integer ID for each node

    def __lt__(self, other):
        return self.freq < other.freq

class HuffmanNode(Node):
    def __init__(self, freq, left=None, right=None):
        super().__init__(freq)
        self.left = left
        self.right = right

def build_huffman_tree(word_freq):
    heap = [Node(f, w) for w, f in word_freq.items()]
    heapq.heapify(heap)
    while len(heap) > 1:
        n1, n2 = heapq.heappop(heap), heapq.heappop(heap)
        heapq.heappush(heap, HuffmanNode(n1.freq + n2.freq, left=n1, right=n2))
    root = heap[0]

    # Assign unique IDs to all nodes
    counter = 0
    def assign_ids(node):
        nonlocal counter
        node.id = counter
        counter += 1
        if node.left: assign_ids(node.left)
        if node.right: assign_ids(node.right)
    assign_ids(root)
    return root


def generate_codes(root):
    word_codes = {}
    word_path_nodes = {}

    def traverse(node, code=[], path=[]):
        if node.word is not None:
            word_codes[node.word] = code
            word_path_nodes[node.word] = path  # these are node IDs
            return
        if node.left: traverse(node.left, code + [0], path + [node.left.id])
        if node.right: traverse(node.right, code + [1], path + [node.right.id])

    traverse(root)
    return word_codes, word_path_nodes

