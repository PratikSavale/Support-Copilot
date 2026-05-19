import math
import re

class BM25Ranker:
    """A self-contained, lightweight BM25 sparse ranker in Python."""

    def __init__(self, documents: list[str], k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.documents = documents
        self.doc_count = len(documents)
        
        # Tokenize corpus
        self.doc_tokens = [self._tokenize(doc) for doc in documents]
        self.doc_lengths = [len(tokens) for tokens in self.doc_tokens]
        self.avg_doc_len = sum(self.doc_lengths) / max(self.doc_count, 1)

        # Document frequencies of terms
        self.doc_freqs: dict[str, int] = {}
        for tokens in self.doc_tokens:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

    def _tokenize(self, text: str) -> list[str]:
        """Convert text into normalized token list, keeping technical tags and code fragments intact."""
        if not text:
            return []
        # Lowercase and split on words/digits, preserving periods or dollar signs in class names (e.g., com.test.class)
        raw_tokens = re.findall(r"\b[a-zA-Z0-9_\.\$]+\b", text.lower())
        return [t for t in raw_tokens if len(t) > 1]

    def _get_idf(self, term: str) -> float:
        """Calculate inverse document frequency of a term with smoothing."""
        df = self.doc_freqs.get(term, 0)
        # Standard Lucene/BM25 IDF formula with smoothing
        return math.log(1.0 + (self.doc_count - df + 0.5) / (df + 0.5))

    def score(self, query: str) -> list[float]:
        """Calculate BM25 scores for all corpus documents against a query string.
        
        Returns a list of float scores corresponding to each document index.
        """
        query_tokens = self._tokenize(query)
        scores = [0.0] * self.doc_count
        
        if not query_tokens or self.doc_count == 0:
            return scores

        for term in query_tokens:
            idf = self._get_idf(term)
            if idf <= 0.0:
                continue

            for idx in range(self.doc_count):
                term_count = self.doc_tokens[idx].count(term)
                if term_count == 0:
                    continue

                doc_len = self.doc_lengths[idx]
                numerator = term_count * (self.k1 + 1.0)
                denominator = term_count + self.k1 * (1.0 - self.b + self.b * (doc_len / max(self.avg_doc_len, 1.0)))
                scores[idx] += idf * (numerator / denominator)

        return scores
