import math
from collections import defaultdict, Counter # `Counter` counts how many times each value occurs in an iterable

# the inverted idnex uses words as keys and an integer array of document indexes as values
# usually, a `token` is just an individual word we extract from a document
class InvertedIndex:
    def __init__(self):
        self.index = defaultdict(dict) # each token key will store a dict w/ keys being doc IDs & values being num. of token occurences
        self.doc_ids = set()

    # upon tokenizing a document, we can add it's index along with all the words we extracted from it
    def add_doc(self, doc_id, tokens): # `tokens` is a list of words in THE doc
        self.doc_ids.add(doc_id)
        token_counts = Counter(tokens) # returns a dict w/ key being the word and value being occurences
        for token, count in token_counts.items():
            self.index[token][doc_id] = count

    @property
    def doc_count(self):
        return len(self.doc_ids)

    # we chose not to find the intersection of all candidate documents because that's too strict
    # we're retrieving the union of all candidate docs now
    # we rank the union documents based on keyword occurences
    # let's use the inverse document frequency theory: the less a keyword occurs in the docs, the more valuable it is (so we should rank those docs higher)
    # IDF formula: log(N/t) where `N` is the total number of docs & `t` is the number of docs w/ out keyword
    # since the log function flattens out, a low `t` value doesn't have a monopoly over our ranking (the weights are more forgiving)
    # we must account for term frequency per document in the scoring
    def search(self, tokens):
        scores = {}
        for token in tokens:
            if not token:
                continue
            # number of docs with the token
            t = len(self.index[token])
            # IDF formula: log(N/t) where `N` is the total number of docs & `t` is the number of docs w/ out keyword
            idf = math.log(self.doc_count / t)
            for doc_id, term_frequency in self.index[token].items():
                scores[doc_id] = scores.get(doc_id, 0) + term_frequency * idf # IDF scales each occurence through multiplication
        return sorted(scores, key=scores.get, reverse=True)