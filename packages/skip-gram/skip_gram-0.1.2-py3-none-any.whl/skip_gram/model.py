import torch
import torch.nn as nn

class SkipGramHS(nn.Module):
    def __init__(self, vocab_size, emb_dim, num_nodes, word_path_nodes, word_codes, node2id):
        super().__init__()
        self.in_embed = nn.Embedding(vocab_size, emb_dim)
        self.node_embed = nn.Embedding(num_nodes, emb_dim)
        self.word_path_nodes = word_path_nodes
        self.word_codes = word_codes
        self.node2id = node2id

    def forward(self, target_idx, context_word):
        v = self.in_embed(target_idx)
        if context_word not in self.word_path_nodes:
            raise ValueError(f"Context word '{context_word}' not in Huffman mapping")
        path_nodes = self.word_path_nodes[context_word]
        codes = self.word_codes[context_word]
        node_ids = torch.tensor([self.node2id[n] for n in path_nodes], dtype=torch.long)
        u = self.node_embed(node_ids)
        logits = torch.matmul(u, v)
        sigmoids = torch.sigmoid(logits)
        loss = 0
        for s, c in zip(sigmoids, codes):
            p = s if c == 1 else (1 - s)
            loss -= torch.log(p + 1e-9)
        return loss
