# train_skipgram_fixed.py
from .huffman import build_huffman_tree, generate_codes
from .model import SkipGramHS
import torch
import torch.optim as optim
from collections import Counter
from nltk.corpus import brown
import nltk
import numpy as np

def train_skipgram(embed_dim=100, window=2, epochs=3, subset=50000):
    nltk.download('brown')
    words = [w.lower() for w in brown.words()[:subset]]
    word_freq = Counter(words)
    vocab = list(word_freq.keys())
    vocab_size = len(vocab)
    word2idx = {w: i for i, w in enumerate(vocab)}
    idx2word = {i: w for w, i in word2idx.items()}

    # -------------------
    # Huffman tree
    # -------------------
    root = build_huffman_tree(word_freq)

    # Assign unique integer IDs to all nodes BEFORE generating codes
    def assign_ids(node, counter=[0]):
        node.id = counter[0]
        counter[0] += 1
        if node.left:
            assign_ids(node.left, counter)
        if node.right:
            assign_ids(node.right, counter)

    assign_ids(root)

    # Generate Huffman codes and path nodes (with integer IDs)
    word_codes, word_path_nodes = generate_codes(root)

    # Build node2id mapping from all internal node IDs
    internal_nodes = list({n for path in word_path_nodes.values() for n in path})
    node2id = {n: i for i, n in enumerate(internal_nodes)}

    # Sanity check
    for word, path in word_path_nodes.items():
        for n in path:
            if n not in node2id:
                raise ValueError(f"Node {n} missing in node2id mapping!")

    # -------------------
    # Model
    # -------------------
    model = SkipGramHS(vocab_size, embed_dim, len(internal_nodes),
                       word_path_nodes, word_codes, node2id)
    optimizer = optim.Adam(model.parameters(), lr=0.01)

    # -------------------
    # Generate (target, context) pairs safely
    # -------------------
    pairs = []
    for i in range(len(words)):
        for j in range(max(0, i - window), min(len(words), i + window + 1)):
            if i != j and words[i] in word_path_nodes and words[j] in word_path_nodes:
                pairs.append((words[i], words[j]))

    # -------------------
    # Training loop
    # -------------------
    loss_history = []
    for epoch in range(epochs):
        total_loss = 0
        for t, c in pairs[:20000]:  # small subset for testing
            optimizer.zero_grad()
            loss = model(torch.tensor(word2idx[t]), c)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        avg_loss = total_loss / 20000
        loss_history.append(avg_loss)
        print(f"Epoch {epoch+1}, loss={avg_loss:.4f}")

    # -------------------
    # Save model and loss history
    # -------------------
    np.save("loss_history.npy", np.array(loss_history))
    torch.save({
        'model_state_dict': model.state_dict(),
        'word2idx': word2idx,
        'idx2word': idx2word,
        'embed_dim': embed_dim,
        'num_nodes': len(internal_nodes),
    }, "skipgram_hs.pt")
    print("\n✅ Model saved to skipgram_hs.pt")

    return model, word2idx, idx2word, loss_history


