import math
from collections import defaultdict, Counter # `Counter` counts how many times each value occurs in an iterable

# the inverted index uses words as keys and an integer array of document indexes as values
# usually, a `token` is just an individual word we extract from a document
class InvertedIndex:
    def __init__(self):
        self.body_index = defaultdict(dict) # each token key will store a dict w/ keys being document IDs & values being num. of token occurences
        self.title_index = defaultdict(dict) # separate index for title tokens
        self.doc_ids = set()
        self.doc_lens = {}

    # upon tokenizing a document, we can add it's body_index along with all the words we extracted from it
    def add_document(self, doc_id, title_tokens, body_tokens): # `tokens` is a list of words in THE document
        self.doc_ids.add(doc_id)
        self.doc_lens[doc_id] = len(body_tokens)
        for token, count in Counter(body_tokens).items(): # count the occurences of each token in the body
            self.body_index[token][doc_id] = count
        for token, count in Counter(title_tokens).items(): # count the occurences of each token in the title
            self.title_index[token][doc_id] = count

    # `@property` is computed everytime access the method
    @property
    def document_count(self):
        return len(self.doc_ids)

    @property
    def avg_document_len(self):
        if not self.doc_ids: # python treats empty containers as False
            return 0
        return sum(self.doc_lens.values()) / self.document_count

    # we chose not to find the intersection of all candidate documents because that's too strict
    # we're retrieving the union of all candidate documents now
    # we rank the union documents based on keyword occurences
    # let's use the inverse document frequency theory: the less a keyword occurs in the documents, the more valuable it is (so we should rank those documents higher)
    # IDF formula: log(N/t) where `N` is the total number of documents & `t` is the number of documents w/ out keyword
    # since the log function flattens out, a low `t` value doesn't have a monopoly over our ranking (the weights are more forgiving)
    # we must account for term frequency per document in the scoring
    # we've just impled TF-IDF (which is an older method)
    # BM25 is a method that improved upon TF-IDF. what is it?
    # it's sessentially IDF for rarity + saturated + length normalization for fairness across short & long documents
    def search(self, tokens):
        # BM25 parames
        k1 = 1.5
        b = 0.75
        scores = {}
        for token in set(tokens): # `set` is used to avoid duplicate query tokens
            if token in self.body_index:
                # number of documents with the token
                t = len(self.body_index[token])
                # IDF formula: log(N/t) where `N` is the total number of documents & `t` is the number of documents w/ out keyword
                # we'll evolve our IDF formula into the standard BM25 IDF formula: log((N - t + 0.5) / (t + 0.5))
                # original: idf = math.log((self.document_count - t + 0.5) / (t + 0.5))
                # the original IDF formula gave common words (words that occured in at least N/2 documents) a negative weight, leading to possible negative scores for some documents
                # we'll use a variant of the IDF formula that instead gives them a value close to zero
                idf = math.log(1 + (self.document_count - t + 0.5) / (t + 0.5))
                for doc_id, term_frequency in self.body_index[token].items(): # the score for each document is computed/added here
                    doc_len = self.doc_lens[doc_id]
                    len_normalization = (1 - b + b * (doc_len / self.avg_document_len))
                    tf_score = (term_frequency * (k1 + 1) / (term_frequency + k1 * len_normalization))
                    scores[doc_id] = scores.get(doc_id, 0) + idf * tf_score
            if token in self.title_index:
                # number of documents with the token
                t = len(self.title_index[token])
                # IDF formula: log(N/t) where `N` is the total number of documents & `t` is the number of documents w/ out keyword
                # we'll evolve our IDF formula into the standard BM25 IDF formula: log((N - t + 0.5) / (t + 0.5))
                idf = math.log((self.document_count - t + 0.5) / (t + 0.5))
                for doc_id, term_frequency in self.title_index[token].items(): # the score for each document is computed/added here
                    # for title tokens, we don't need length normalization, so we can use the standard saturated TF-IDF formula
                    tf_score = term_frequency * (k1 + 1) / (term_frequency + k1)
                    scores[doc_id] = scores.get(doc_id, 0) + idf * tf_score
        return sorted(
            scores.items(), # returns a list of tuples (doc_id, score)
            key=lambda x: x[1], # sort by the score value in the tuple (doc_id, score)
            reverse=True # sort in descending order
        )
