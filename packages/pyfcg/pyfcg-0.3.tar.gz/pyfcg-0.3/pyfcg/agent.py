import pyfcg as fcg

__all__ = [
    'Agent'
    ]

class Agent:
    """
    The class for representing PyFCG agents.
    """

    def __init__(self, name="agent"):
        self.name = name
        self.id = fcg.routes.gensym(name)
        self.grammar = fcg.Grammar(fcg.routes.gensym(name + "-grammar"))

    def __repr__(self):
        """String representation for printing agent objects."""
        return "<Agent: " + self.name + " (id: " + self.id + ") ~ " + str(self.grammar_size()) + " constructions>"

    def load_grammar_image(self, pathname):
        """Loading a grammar image into an agent."""
        self.grammar.load_grammar_image(pathname)

    def save_grammar_image(self, pathname):
        """Saving an image of an agent's grammar for later reuse."""
        return self.grammar.save_grammar_image(pathname)
        
    def load_grammar_from_file(self, file_name):
        """Load an FCG grammar spec in JSON format from a file."""
        self.grammar.load_grammar_from_file(file_name)

    def formulate(self, meaning):
        """Formulate meaning through an agent's grammar."""
        return self.grammar.formulate(meaning)

    def formulate_all(self, meaning):
        """Formulate meaning through an agent's grammar, returning all solutions."""
        return self.grammar.formulate_all(meaning)

    def comprehend(self, utterance):
        """Comprehend an utterance through an agent's grammar."""
        return self.grammar.comprehend(utterance)

    def comprehend_all(self, utterance):
        """Comprehend an utterance through an agent's grammar, returning all solutions."""
        return self.grammar.comprehend_all(utterance)

    def comprehend_and_formulate(self, utterance):
        """Comprehend an utterance and call formulate on the resulting meaning."""
        return self.grammar.comprehend_and_formulate(utterance)

    def formulate_and_comprehend(self, meaning):
        """Formulate meaning and call comprehend on the resulting utterance."""
        return self.grammar.formulate_and_comprehend(meaning)

    def add_cxn(self, cxn):
        """Add a construction to an agent's grammar."""
        self.grammar.add_cxn(cxn)

    def delete_cxn(self, cxn):
        """Delete a construction from an agent's grammar."""
        self.grammar.delete_cxn(cxn)

    def grammar_size(self):
        """Return the size of an agent's grammar (number of constructions)."""
        return self.grammar.size()

    def clear_cxns(self):
        """Delete all constructions from an agent's grammar."""
        self.grammar.clear_cxns()

    def find_cxn_by_name (self, cxn_name):
        """Retrieves a construction by name."""
        return self.grammar.find_cxn_by_name(cxn_name)

    def add_category (self, category):
        """Add a category to an agent's categorial network."""
        self.grammar.add_category(category)

    def add_link (self, category_1, category_2):
        """Add a link between two categories in an agent's categorial network."""
        self.grammar.add_link(category_1, category_2)
