import matplotlib.pyplot as plt
import re
from collections import Counter

def plot_stats(text: str):
    words = re.findall(r'\b\w+\b', text.lower())
    counts = Counter(words)
    common = counts.most_common(10)

    labels, values = zip(*common)
    plt.bar(labels, values)
    plt.title("?n çox isl?n?n 10 söz")
    plt.xlabel("Sözl?r")
    plt.ylabel("Tezlik")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
