import torch
import torch.nn as nn
import torch.optim as optim
from collections import Counter
from nltk.corpus import brown
import nltk
import numpy as np
from .huffman import build_huffman_tree, generate_codes


class CBOW_HS(nn.Module):
    """
    Continuous Bag of Words with Hierarchical Softmax.
    Predicts the target (center) word given surrounding context words.
    """
    def __init__(self, vocab_size, emb_dim, num_nodes, word_path_nodes, word_codes, node2id):
        super().__init__()
        self.in_embed = nn.Embedding(vocab_size, emb_dim)
        self.node_embed = nn.Embedding(num_nodes, emb_dim)
        self.word_path_nodes = word_path_nodes
        self.word_codes = word_codes
        self.node2id = node2id

    def forward(self, context_idxs, target_word):
        # mean of context embeddings
        context_embeds = self.in_embed(context_idxs)
        v = context_embeds.mean(dim=0)  # averaged context vector
        path_nodes = self.word_path_nodes[target_word]
        codes = self.word_codes[target_word]
        node_ids = torch.tensor([self.node2id[n] for n in path_nodes], dtype=torch.long)
        u = self.node_embed(node_ids)
        logits = torch.matmul(u, v)
        sigmoids = torch.sigmoid(logits)
        loss = 0
        for s, c in zip(sigmoids, codes):
            p = s if c == 1 else (1 - s)
            loss -= torch.log(p + 1e-9)
        return loss


def train_cbow(embed_dim=100, window=2, epochs=3, subset=50000):
    nltk.download('brown')
    words = [w.lower() for w in brown.words()[:subset]]
    word_freq = Counter(words)
    vocab = list(word_freq.keys())
    word2idx = {w: i for i, w in enumerate(vocab)}
    idx2word = {i: w for w, i in word2idx.items()}

    root = build_huffman_tree(word_freq)
    word_codes, word_path_nodes = generate_codes(root)
    internal_nodes = list({n for path in word_path_nodes.values() for n in path})
    node2id = {n: i for i, n in enumerate(internal_nodes)}

    model = CBOW_HS(len(vocab), embed_dim, len(internal_nodes),
                    word_path_nodes, word_codes, node2id)
    optimizer = optim.Adam(model.parameters(), lr=0.01)

    pairs = []
    for i in range(window, len(words) - window):
        context = [words[j] for j in range(i - window, i + window + 1) if j != i]
        target = words[i]
        pairs.append((context, target))

    loss_history = []
    for epoch in range(epochs):
        total_loss = 0
        for ctx, tgt in pairs[:20000]:
            context_ids = torch.tensor([word2idx[w] for w in ctx if w in word2idx])
            if len(context_ids) == 0: continue
            optimizer.zero_grad()
            loss = model(context_ids, tgt)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        avg_loss = total_loss / 20000
        loss_history.append(avg_loss)
        print(f"Epoch {epoch+1}, loss={avg_loss:.4f}")

    np.save("cbow_loss.npy", np.array(loss_history))
    torch.save({
        'model_state_dict': model.state_dict(),
        'word2idx': word2idx,
        'idx2word': idx2word,
        'embed_dim': embed_dim,
        'num_nodes': len(internal_nodes),
    }, "cbow_hs.pt")

    print("\n✅ CBOW model saved to cbow_hs.pt")
    return model, word2idx, idx2word, loss_history
