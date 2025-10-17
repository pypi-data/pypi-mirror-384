import pyfcg as fcg
import json
import os

__all__ = [
    'Grammar',
    ]

#: 
DEFAULT_GRAMMAR_CONFIGURATION = {"heuristics": [":cxn-score"],
                                 "parse-goal-tests": [":no-applicable-cxns", ":no-sequence-in-root"],
                                 "production-goal-tests": [":no-applicable-cxns", ":no-meaning-in-root"],
                                 "render-mode": ":render-sequences",
                                 "de-render-mode": ":de-render-sequence-predicates",
                                 "draw-meaning-as-network": True,
                                 "cxn-supplier-mode": ":all-cxns",
                                 "construction-inventory-processor-mode": ":heuristic-search",
                                 "node-expansion-mode": ":full-expansion",
                                 "search-algorithm": ":best-first",
                                 "heuristic-value-mode": ":sum-heuristics-and-parent",
                                 "node-tests": [":check-duplicate", ":restrict-nr-of-nodes", ":restrict-search-depth"],
                                 "max-search-depth": 25,
                                 "max-nr-of-nodes": 250,
                                 "category-linking-mode": ":neighbours",
                                 "initial-categorial-link-weight": 0.0}

#: 
DEFAULT_GRAMMAR_VISUALIZATION_CONFIGURATION = {"hide-features": ["footprints"],
                                               "show-constructional-dependencies": True}

#: 
DEFAULT_FEATURE_TYPES = [['form', 'set-of-predicates', ':handle-regex-sequences'],
                         ['meaning', 'set-of-predicates'],
                         ['form-args', 'sequence'],
                         ['meaning-args', 'sequence'],
                         ['subunits', 'set'],
                         ['args', 'sequence'],
                         ['footprints', 'set']]

#: 
DEFAULT_CXN_ATTRIBUTES = {'score': 0.5,
                          'label': 'cxn'}

#:
DEFAULT_HIERARCHY_FEATURES = ['subunits']


class Grammar:
    """
    The Grammar class implements all functionality
    required to support FCG grammars in PyFCG.
    A grammar has an id, cxns, a configuration,
    a visualization_configuration and a categorial_network.
    """

    def __init__(self, grammar_id):
        self.id = grammar_id
        self.configuration = DEFAULT_GRAMMAR_CONFIGURATION
        self.visualization_configuration = DEFAULT_GRAMMAR_VISUALIZATION_CONFIGURATION
        self.feature_types = DEFAULT_FEATURE_TYPES
        self.hierarchy_features = DEFAULT_HIERARCHY_FEATURES
        self.cxns = {}
        self.categorial_network = {}
        self.hashed = False

        self.register_grammar()

    def __repr__(self):
        """String representation for printing grammar objects."""
        return "<Grammar: " + str(self.size()) + " constructions>"

    def register_grammar(self):
        """
        Register the grammar in FCG, with all configurations etc. but without constructions
        """
        fcg.routes.register_grammar(self)

    def load_grammar_image(self, pathname):
        """Load a grammar image saved under pathname."""
        grammar_info = fcg.routes.load_grammar_image(os.path.abspath(pathname), self.id)
        
        if grammar_info['construction-names']:
            for cxn_name in grammar_info['construction-names']:
                self.cxns[cxn_name] = fcg.Construction(cxn_name, conditional_pole=[])

        if grammar_info['categories']:
            self.categorial_network['nodes'] = grammar_info['categories']
        else:
            self.categorial_network['nodes'] = []

        if grammar_info['categorial-links']:
            self.categorial_network['edges'] = grammar_info['categorial-links']
        else:
            self.categorial_network['edges'] = []
            
        self.configuration = grammar_info['configuration']

    def save_grammar_image(self, pathname):
        "Save the grammar to a file (as a binary image)."
        return fcg.routes.save_grammar_image(os.path.abspath(pathname), self.id)

    def load_grammar_from_file(self, file_name):
        """Read an FCG grammar (in JSON format) from a file."""
        with open(file_name, 'r') as f:
            grammar_spec = json.load(f)
        # Make sure grammar_spec id is equal to Grammar id
        grammar_spec["id"] = self.id
        # Overwrite default settings if user specified configuration,
        # visualization-configuration, categorial-network or feature-types in grammar_spec
        if 'configuration' in grammar_spec:
            self.configuration = grammar_spec['configuration'] #to do: merge configurations!
        if 'visualization-configuration' in grammar_spec:
            self.visualization_configuration = grammar_spec['visualization-configuration'] #to do: merge configurations!
        if 'categorial-network' in grammar_spec:
            self.categorial_network = grammar_spec['categorial-network']
        if 'feature-types' in grammar_spec:
            self.feature_types = grammar_spec['feature-types']
        if 'hierarchy-features' in grammar_spec:
            self.hierarchy_features = grammar_spec['hierarchy-features']

        self.register_grammar()

        cxn_specs = grammar_spec.pop("cxns")
        for cxn_name, cxn_spec in cxn_specs.items():
            if 'feature-types' in cxn_spec:
                feature_types = cxn_spec['feature-types']
            else:
                feature_types = []

            if 'attributes' in cxn_spec:
                attributes = cxn_spec['attributes']
            else:
                attributes = DEFAULT_CXN_ATTRIBUTES

            if 'contributing-pole' in cxn_spec:
                contributing_pole = cxn_spec['contributing-pole']
            else:
                contributing_pole = []

            cxn = fcg.Construction(name=cxn_spec["name"],
                                   conditional_pole=cxn_spec["conditional-pole"],
                                   contributing_pole=contributing_pole,
                                   attributes=attributes,
                                   feature_types=feature_types)
            self.add_cxn(cxn)

    def comprehend(self, utterance):
        """Comprehend an utterance based on a grammar and return best solution."""
        return fcg.routes.comprehend(utterance, self.id)

    def comprehend_all(self, utterance):
        """Comprehend an utterance based on a grammar and return all solutions."""
        comprehension_result = fcg.routes.comprehend_all(utterance, self.id)
        return comprehension_result['meanings'], comprehension_result['applied-cxns']

    def formulate(self, meaning):
        """Formulate an utterance for a given meaning based on a grammar, returning the best solution."""
        return fcg.routes.formulate(meaning, self.id)

    def formulate_all(self, meaning):
        """Formulate an utterance for a given meaning based on a grammar, returning all solutions."""
        formulation_result = fcg.routes.formulate_all(meaning, self.id)
        return formulation_result['utterances'], formulation_result['applied-cxns']

    def comprehend_and_formulate(self,utterance):
        """Comprehend an utterance, instantiate all variables in the resulting meaning
        representation and return the result from formulating this meaning representation."""
        comprehension_result = self.comprehend(utterance)
        meaning_w_instantiated_vars = fcg.instantiate_variables(comprehension_result)
        return self.formulate(meaning_w_instantiated_vars)

    def formulate_and_comprehend(self,meaning):
        """Formulate a meaning representation and comprehend the resulting utterance."""
        formulation_result = self.formulate(meaning)
        return self.comprehend(formulation_result)

    def add_cxn(self, cxn):
        """Add a new construction to a grammar."""
        cxn.grammar_id = self.id
        self.cxns[cxn.name] = cxn
        cxn.feature_types = fcg.utils.inherit_feature_types(self.feature_types, cxn.feature_types)
        fcg.routes.add_cxn({"grammar-id" : self.id,
                            "name" : cxn.name,
                            "conditional-pole": cxn.conditional_pole,
                            "contributing-pole": cxn.contributing_pole,
                            "attributes": cxn.attributes,
                            "feature-types": cxn.feature_types})

    def delete_cxn(self, cxn):
        """Delete a construction from a grammar."""
        if type(cxn) is str:
            self.cxns.pop(cxn)
            fcg.routes.delete_cxn(cxn, self.id)
        else:
            self.cxns.pop(cxn.name)
            fcg.routes.delete_cxn(cxn.name, self.id)

    def size(self):
        """Return the size of the grammar (number of constructions)."""
        return len(self.cxns)

    def clear_cxns(self):
        """Clear all constructions from grammar."""
        self.cxns={}
        fcg.routes.clear_grammar(self.id)

    def find_cxn_by_name (self, cxn_name):
        """Find a construction by name."""
        return self.cxns[cxn_name]

    def show_in_web_interface (self):
        """Show grammar in FCG's web interface."""
        fcg.routes.show_grammar_in_web_interface(self.id)

    def add_category(self, category):
        """Add a category to a grammar's categorial network."""
        fcg.routes.add_category(category, self.id)
        self.categorial_network['nodes'].append(category)

    def add_link(self, category_1, category_2):
        """Add a link between two categories in a grammar's categorial network."""
        fcg.routes.add_link(category_1, category_2, self.id)
        self.categorial_network['edges'].append([category_1, category_2])

    def set_feature_types (self, feature_types, inherit_feature_types=True):
        """Set the feature types of the grammar."""
        if inherit_feature_types:
            self.feature_types = fcg.utils.inherit_feature_types(self.feature_types, feature_types)
        else:
            self.feature_types = feature_types

        fcg.routes.set_feature_types(self.feature_types, self.id)


    def set_feature_type (self, feature_name, feature_type, procedural_attachment=None):
        """Set a single feature type in the grammar."""
        if procedural_attachment:
            self.set_feature_types([[feature_name, feature_type, procedural_attachment]])
        else:
            self.set_feature_types([[feature_name, feature_type]])

    def set_grammar_configuration (self, key, value):
        """Set a configuration key in the grammar to a new value."""
        fcg.routes.set_grammar_configuration(key, value, self.id)
        self.configuration[key] = value

    def set_grammar_visualization_configuration(self, key, value):
        """Set a visualization configuration key in the grammar to a new value."""
        fcg.routes.set_grammar_visualization_configuration(key, value, self.id)
        self.visualization_configuration[key] = value