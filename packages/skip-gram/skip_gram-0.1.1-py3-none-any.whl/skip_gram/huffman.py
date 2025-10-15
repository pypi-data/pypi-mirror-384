import heapq

class HuffmanNode:
    def __init__(self, freq, word=None, left=None, right=None):
        self.freq = freq
        self.word = word
        self.left = left
        self.right = right
    def __lt__(self, other): return self.freq < other.freq

def build_huffman_tree(word_freq):
    heap = [HuffmanNode(f, w) for w, f in word_freq.items()]
    heapq.heapify(heap)
    while len(heap) > 1:
        n1, n2 = heapq.heappop(heap), heapq.heappop(heap)
        heapq.heappush(heap, HuffmanNode(n1.freq + n2.freq, left=n1, right=n2))
    return heap[0]

def generate_codes(root):
    word_codes, word_path_nodes = {}, {}
    def traverse(node, code=[], path=[]):
        if node.word is not None:
            word_codes[node.word] = code
            word_path_nodes[node.word] = path
            return
        if node.left: traverse(node.left, code + [0], path + [node.left])
        if node.right: traverse(node.right, code + [1], path + [node.right])
    traverse(root)
    return word_codes, word_path_nodes
