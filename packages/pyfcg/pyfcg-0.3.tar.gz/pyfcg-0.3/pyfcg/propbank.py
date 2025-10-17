import pyfcg as fcg
import os

__all__ = [
    'PropBankAgent',
]

#: 
TRAINING_CONFIGURATION = {
    "de-render-mode" : ":de-render-constituents-dependents",
    "node-tests" : [":check-double-role-assignment"],
    "parse-goal-tests" : [":no-valid-children"],
    "construction-inventory-processor-mode" : ":heuristic-search",
    "search-algorithm" : ":best-first",
    "cxn-supplier-mode" : ":hashed-categorial-network",
    "heuristics": [":nr-of-units-matched"],
    "heuristic-value-mode": ":sum-heuristics-and-parent",
    "node-expansion-mode" : ":full-expansion",
    "hash-mode": ":hash-lemma",
    "learning-modes": [":core-roles", ":argm-leaf", ":argm-pp", ":argm-sbar", ":argm-phrase-with-string"]
    } 


class PropBankAgent(fcg.Agent):
    """A class for representing a PropBank agent."""

    def learn_grammar_from_conll_file(self, pathname, training_configuration={}, excluded_rolesets=[]):
        """Learn a grammar from a conll file using the PropBank grammar learning route"""
        training_configuration = fcg.utils.merge_dicts(TRAINING_CONFIGURATION, training_configuration)
        grammar_info = fcg.routes.learn_propbank_grammar(os.path.abspath(pathname), self.grammar.id, training_configuration, excluded_rolesets)
        for cxn_name in grammar_info['construction-names']:
            self.grammar.cxns[cxn_name] = fcg.Construction(cxn_name, conditional_pole=[])
        self.grammar.categorial_network['nodes'] = grammar_info['categories']
        self.grammar.categorial_network['edges'] = grammar_info['categorial-links']
        self.grammar.configuration = grammar_info['configuration']

    def comprehend(self, utterance):
        """Comprehend utterance using the agent's PropBank grammar and extract the frames from the result."""
        frames = fcg.routes.comprehend_and_extract_frames(utterance, self.grammar.id)
        clean_frames = []
        if frames is not None:
            for frame in frames:
                roles = []
                frame_elements = frame['frame-elements']
                if frame_elements is not None:
                    for frame_element in frame_elements:
                        roles.append((frame_element['fe-role'], frame_element['fe-string'], frame_element['indices']))
                clean_frames.append({'roleset' : frame['frame-name'],
                                 'roles' : [('v', frame['frame-evoking-element']['fel-string'], frame['frame-evoking-element']['indices'])] + roles})
            return clean_frames
