import torch, torch.optim as optim, numpy as np
from collections import Counter
from nltk.corpus import brown
import nltk
from .huffman import build_huffman_tree, generate_codes
from .model import SkipGramHS

def train_skipgram(embed_dim=100, window=2, epochs=3, subset=50000):
    nltk.download('brown')
    words = [w.lower() for w in brown.words()[:subset]]
    word_freq = Counter(words)
    vocab = list(word_freq.keys())
    vocab_size = len(vocab)
    word2idx = {w: i for i, w in enumerate(vocab)}
    idx2word = {i: w for w, i in word2idx.items()}

    # Huffman Tree
    root = build_huffman_tree(word_freq)
    word_codes, word_path_nodes = generate_codes(root)
    internal_nodes = list({n for path in word_path_nodes.values() for n in path})
    node2id = {n: i for i, n in enumerate(internal_nodes)}

    model = SkipGramHS(vocab_size, embed_dim, len(internal_nodes),
                       word_codes, word_path_nodes, node2id)
    optimizer = optim.Adam(model.parameters(), lr=0.01)

    pairs = []
    for i in range(len(words)):
        for j in range(max(0, i - window), min(len(words), i + window + 1)):
            if i != j: pairs.append((words[i], words[j]))

    loss_history = []
    for epoch in range(epochs):
        total_loss = 0
        for t, c in pairs[:20000]:
            optimizer.zero_grad()
            loss = model(torch.tensor(word2idx[t]), c)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        avg_loss = total_loss / 20000
        loss_history.append(avg_loss)
        print(f"Epoch {epoch+1}, loss={avg_loss:.4f}")

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
