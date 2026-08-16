from collections import defaultdict

# the inverted idnex uses words as keys and an integer array of document indexes as values

class InvertedIndex:
    def __init__(self):
        self.index = defaultdict(list)

    # upon tokenizing a document, we can add it's index along with all the words we extracted from it
    def add_document(self, document_id, tokens):
        for token in tokens:
            self.index[token].append(document_id)

    def search_document(self,
                        token # a `token` is basically just a singular word
    ):
        return self.index.get(token, []) # retrieve all relevant documents for a given token
        
        
