import random
import pyfcg as fcg

__all__ = [
    'start_web_interface',
    'activate_monitors',
    'activate_monitor',
    'deactivate_all_monitors',
    'merge_dicts',
    'generate_word_form',
    'inherit_feature_types',
    'instantiate_variables',
    'predicate_network_to_penman',
    'predicate_network_to_penman_triples',
    'amr_penman_top',
    'penman_to_predicate_network',
    'penman_triples_to_predicate_network',
    ]

######################################################
# A collection of useful functions for using FCG     #
######################################################


def start_web_interface(address='localhost', port=8010, open=True):
    """Start up the Babel web interface."""
    fcg.routes.start_web_interface(address, port, open)


def activate_monitors (list_of_monitors):
    """Activate all monitors in list_of_monitors."""
    fcg.routes.activate_monitors(list_of_monitors)


def activate_monitor (monitor):
    """Activate monitor."""
    fcg.routes.activate_monitors([monitor])


def deactivate_all_monitors ():
    """Deactivate all monitors."""
    fcg.routes.deactivate_all_monitors()


def merge_dicts(backoff_dict, main_dict):
    """ Merge the two dicts, the second dict taking precedence in case of conflicts. """
    return {**backoff_dict, **main_dict}


def generate_word_form(nr_of_syllables=3):
    """ Generate a new random word form."""
    vowels = ["a", "e", "i", "o", "u"]
    consonants = ["b", "d", "f", "g", "k", "l", "m",
                  "n", "p", "r", "s", "t", "v", "w", "x", "z"]
    word_form = []
    for i in range(nr_of_syllables):
        word_form.append(random.choice(consonants))
        word_form.append(random.choice(vowels))
    new_word_form = ''.join(word_form)
    return new_word_form


def inherit_feature_types(feature_types_cxn_inventory, feature_types_cxn):
    """Merge feature types from cxn inventory with feature types from cxn."""

    # Create a dictionary from feature_types_cxn for quick lookup by first element
    feature_types_cxn_dict = {lst[0]: lst for lst in feature_types_cxn}

    # Start with feature_types_cxn items if they match, otherwise keep the original from list1
    merged = []
    seen_keys = set()

    for lst in feature_types_cxn_inventory:
        key = lst[0]
        if key in feature_types_cxn_dict:
            merged.append(feature_types_cxn_dict[key])
        else:
            merged.append(lst)
        seen_keys.add(key)

    # Add any remaining items from feature_types_cxn that weren't already merged
    for lst in feature_types_cxn:
        key = lst[0]
        if key not in seen_keys:
            merged.append(lst)

    return merged


def instantiate_variables(structure):
    """Recursively instantiates variables."""
    if isinstance(structure, str):
        if structure[0] == '?':
            return structure[1:]
        else:
            return structure
    elif len(structure) == 1:
        return [instantiate_variables(structure[0])]
    else:
        return [instantiate_variables(structure[0])] + instantiate_variables(structure[1:]) 



# Penman Notation #
####################

import penman
from penman.models.noop import model as noop_model


def predicate_network_to_penman(predicate_network, indent=5):
    """Returns a Penman string based on a predicate network."""
    instantiated_meaning = instantiate_variables(predicate_network)
    triples, top = predicate_network_to_penman_triples(instantiated_meaning)
    graph = penman.graph.Graph(triples)
    return penman.encode(graph, indent=indent, top=top)


def predicate_network_to_penman_triples(predicate_network):
    """Returns a predicate network as a list of triples compatible with the penman module."""
    triples = []
    for predicate in predicate_network:
        if len(predicate) == 2:
            triples.append(tuple([predicate[1], ':instance', predicate[0]]))
        else:
            triples.append(tuple([predicate[1], predicate[0], predicate[2]]))
    return triples, amr_penman_top(triples)


def amr_penman_top(penman_triples):
    """Returns the variable of the top-level predicate in penman_triples."""
    for triple in penman_triples:
        if triple[1] == ':instance':
            found_as_argument = None
            for other_triple in penman_triples:
                if triple[0] == other_triple[2]:
                    found_as_argument = True
                    break
            if not found_as_argument:
                return triple[0]
            

def penman_to_predicate_network(penman_serialized_graph):
    """Returns a predicate network based on a penman string."""
    graph = penman.decode(penman_serialized_graph, model = noop_model)
    return penman_triples_to_predicate_network(graph.triples)


def penman_triples_to_predicate_network(triples):
    """Returns an FCG predicate network for a list of triples."""
    predicate_network = []
    for arg1, relation, arg2 in triples:
        if relation == ':instance':
            predicate_network.append([arg2, arg1])
        else:
            predicate_network.append([relation, arg1, arg2])
    return predicate_network
