import pyfcg.routes
fcg = pyfcg

__all__ = [
    'Construction'
    ]

class Construction():
    """
    An FCG construction.
    """

    def __init__(self, name, conditional_pole, contributing_pole=[], attributes={'score': 0.5, 'label': 'cxn'}, feature_types=[]):
        self.grammar_id = None
        self.name = name
        self.conditional_pole = conditional_pole
        self.contributing_pole = contributing_pole
        self.attributes = attributes
        self.feature_types = feature_types

    def __repr__(self):
        """String representation for printing construction objects."""
        return "<Construction: " + self.name + " (" + str(self.get_score()) + ")>"

    def set_score(self, score):
        """Set the score of a construction to score."""
        self.attributes['score'] = score
        fcg.routes.set_cxn_score(self.name, score, self.grammar_id)

    def get_score(self):
        """Return the score of a construction."""
        return self.attributes['score']
    
    def increase_score(self, delta=0.1, upper_bound=1.0):
        """Increase the score of a construction by delta."""
        new_score = self.get_score() + delta
        if new_score > upper_bound:
            new_score = upper_bound
        self.set_score(new_score)
        return new_score

    def decrease_score(self, delta=0.2, lower_bound=0):
        """Decrease the score of a construction by delta."""
        new_score = self.get_score() - delta
        if new_score < lower_bound:
            new_score = lower_bound
        self.set_score(new_score)
        return new_score

    def show_in_web_interface (self):
        """Show construction in FCG's web interface."""
        fcg.routes.show_construction_in_web_interface(self.name, self.grammar_id)