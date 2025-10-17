import requests
from requests import JSONDecodeError
import json
import pyfcg.fcg_go_bridge as fcg_go

endpoints = {'test_connection': '/fcg-test-connection',
             'lisp_eval': '/fcg-read-eval-print',
             'start_web_interface': "/fcg-start-web-interface",
             'activate_monitors': "/fcg-activate-monitors",
             'load_demo_grammar': "/fcg-load-demo-grammar",
             'comprehend': "/fcg-comprehend",
             'comprehend_all': "/fcg-comprehend-all",
             'formulate': "/fcg-formulate",
             'formulate_all': "/fcg-formulate-all",
             'add_cxn': "/fcg-add-cxn",
             'delete_cxn': "/fcg-delete-cxn",
             'register_grammar': "/fcg-initialise-grammar",
             'clear_grammar': "/fcg-clear-grammar",
             'deactivate_all_monitors': "/fcg-deactivate-all-monitors",
             'show_construction_in_web_interface': "/fcg-show-construction-in-web-interface",
             'show_grammar_in_web_interface': "/fcg-show-grammar-in-web-interface",
             'fcg_eval': "/fcg-apply-fn",
             'set_cxn_score': "/fcg-set-cxn-score",
             'gensym': "/fcg-gensym",
             'add_category': "/fcg-add-category",
             'add_link': "/fcg-add-link",
             'learn_propbank_grammar': "/fcg-learn-propbank-grammar",
             'comprehend_and_extract_frames': "/fcg-comprehend-and-extract-frames",
             'load_grammar_image': "/fcg-load-grammar-image",
             'save_grammar_image': "/fcg-store-grammar-image",
             'add_element': "/fcg-add-element",
             'set_feature_types': "/fcg-set-feature-types",
             'set_grammar_configuration' : "/fcg-set-grammar-configuration",
             'set_grammar_visualization_configuration' : "/fcg-set-grammar-visualization-configuration"}


# Get and post requests #
#########################

class FcgError(Exception):
    pass


def get (endpoint, params=None):
    response = requests.get('http://' + fcg_go.server_address + ':' + str(fcg_go.server_port) + endpoint,params=params)
    if response.status_code == 200:
        return response.json()
    else:
        try:
            error_message = response.json()['error-message']
        except JSONDecodeError:
            error_message = response.text
        raise FcgError(error_message)


def post (endpoint, data, params=None):
    response = requests.post('http://' + fcg_go.server_address + ':' + str(fcg_go.server_port) + endpoint, json=data, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        try:
            error_message = response.json()['error-message']
        except JSONDecodeError:
            error_message = response.text
        raise FcgError(error_message)

# System and testing #
#########################

def test_connection ():
    endpoint = endpoints['test_connection']
    return get(endpoint)


def lisp_eval (lisp_expression, package=None):
    """Execute arbitrary code in package."""
    endpoint = endpoints['lisp_eval']
    data = {'lisp-code' : lisp_expression, 'package': package}
    return post(endpoint, data)


def fcg_eval (*args, package=None):
    """Execute arbitrary code in package."""
    endpoint = endpoints['fcg_eval']
    data = {'function-name' : args[0],
            'args': args[1:],
            'package': package}
    return post(endpoint, data)


def gensym(string, variable=False, package=None):
    endpoint = endpoints['gensym']
    data = {'string' : string,
            'variable' : variable,
            'package': package}
    return post(endpoint, data)



# Web interface and monitors #
##############################

def start_web_interface (address='localhost', port=8010, open=True):
    """Start up the babel web interface."""
    endpoint = endpoints['start_web_interface']
    data = {'address': address, 'port': port, 'open': open}
    return post(endpoint, data)


def activate_monitors (list_of_monitors):
    """Activate all monitors in list_of_monitors."""
    endpoint = endpoints['activate_monitors']
    data = {'monitors': list_of_monitors}
    return post(endpoint, data)


def deactivate_all_monitors ():
    """Start up the babel web interface."""
    endpoint = endpoints['deactivate_all_monitors']
    return get(endpoint)
    

def add_element (html):
    """Pushes HTML to Babel web interface."""
    endpoint = endpoints['add_element']
    data = {'html': html}
    return post(endpoint, data)


def show_construction_in_web_interface(cxn_name, grammar_id):
    """Shows construction in grammar with id grammar_id with name cxn_grammer in FCG's web interface."""
    endpoint = endpoints['show_construction_in_web_interface']
    data = {
        'cxn-name': cxn_name,
        'grammar-id': grammar_id
        }
    return post(endpoint, data)


def show_grammar_in_web_interface(grammar_id):
    """Shows the grammar with id grammar_id in FCG's web interface."""
    endpoint = endpoints['show_grammar_in_web_interface']
    data = {
        'grammar-id': grammar_id,
        }
    return post(endpoint, data)


# Demo grammar #
################

def load_demo_grammar ():
    """Load an FCG demo grammar."""
    endpoint = endpoints['load_demo_grammar']
    return get(endpoint)


# FCG processing #
##################

def comprehend(utterance, grammar_id='*fcg-constructions*', package =None):
    endpoint = endpoints['comprehend']
    data = {'utterance': utterance,
            'grammar': grammar_id,
            'package': package}
    return post(endpoint, data)


def comprehend_all(utterance, grammar_id='*fcg-constructions*', package=None):
    endpoint = endpoints['comprehend_all']
    data = {'utterance': utterance,
            'grammar': grammar_id,
            'package':package}
    return post(endpoint, data)


def formulate(meaning, grammar_id='*fcg-constructions*', package=None):
    endpoint = endpoints['formulate']
    data = {'meaning': meaning,
            'grammar': grammar_id,
            'package':package}
    return post(endpoint, data)


def formulate_all(meaning, grammar_id='*fcg-constructions*', package=None):
    endpoint = endpoints['formulate_all']
    data = {'meaning': meaning,
            'grammar': grammar_id,
            'package':package}
    return post(endpoint, data)

# Grammars and constructions #
##############################

def add_cxn(cxn_spec):
    endpoint = endpoints['add_cxn']
    data = {'cxn': cxn_spec}
    return post(endpoint, data)


def delete_cxn(cxn_name, grammar_id):
    endpoint = endpoints['delete_cxn']
    data = {'cxn-name': cxn_name,
            'grammar': grammar_id}
    return post(endpoint, data)


def register_grammar(grammar, package=None):
    """Initialises an FCG grammar (without cxns) based on a grammar specification."""
    endpoint = endpoints['register_grammar']
    data = {'hashed' : grammar.hashed,
            'id': grammar.id,
            'feature-types': grammar.feature_types,
            'hierarchy-features': grammar.hierarchy_features,
            'configuration': grammar.configuration,
            'visualization-configuration': grammar.visualization_configuration,
            'categorial-network': grammar.categorial_network,
            'package': package}
    return post(endpoint, data)


def clear_grammar(grammar_id):
    endpoint = endpoints['clear_grammar']
    data = {'grammar': grammar_id}
    return post(endpoint, data)


def set_cxn_score(cxn_name, new_score, grammar_id='*fcg-constructions*'):
    endpoint = endpoints['set_cxn_score']
    data = {'cxn-name': cxn_name,
            'new-score': new_score,
            'grammar': grammar_id}
    return post(endpoint, data)


def set_feature_types(feature_types, grammar_id='*fcg-constructions*'):
    endpoint = endpoints['set_feature_types']
    data = {'feature-types': feature_types,
            'grammar': grammar_id}
    return post(endpoint, data)

def set_grammar_configuration(key, value, grammar_id='*fcg-constructions*'):
    endpoint = endpoints['set_grammar_configuration']
    data = {'key': key,
            'value': value,
            'grammar': grammar_id}
    return post(endpoint, data)

def set_grammar_visualization_configuration(key, value, grammar_id='*fcg-constructions*'):
    endpoint = endpoints['set_grammar_visualization_configuration']
    data = {'key': key,
            'value': value,
            'grammar': grammar_id}
    return post(endpoint, data)

# Categorial Network #
######################

def add_category(category, grammar_id):
    endpoint = endpoints['add_category']
    data = {
        'category': category,
        'grammar-id': grammar_id,
    }
    return post(endpoint, data)


def add_link(category_1, category_2, grammar_id):
    endpoint = endpoints['add_link']
    data = {
        'category-1': category_1,
        'category-2': category_2,
        'grammar-id': grammar_id,
    }
    return post(endpoint, data)


# PropBank routes   #
#####################

def learn_propbank_grammar(pathname, grammar_id, training_configuration, excluded_rolesets=None):
    endpoint = endpoints['learn_propbank_grammar']
    data = {'pathname': pathname,
            'grammar-id': grammar_id,
            'training-configuration': training_configuration,
            'excluded-rolesets' : excluded_rolesets}
    return post(endpoint, data)


def load_grammar_image(pathname, grammar_id):
    endpoint = endpoints['load_grammar_image']
    data = {'pathname': pathname,
            'grammar-id': grammar_id}
    return post(endpoint, data)


def save_grammar_image(pathname, grammar_id):
    endpoint = endpoints['save_grammar_image']
    data = {'pathname': pathname,
            'grammar-id': grammar_id}
    return post(endpoint, data)


def comprehend_and_extract_frames(utterance, grammar_id, package=None):
    endpoint = endpoints['comprehend_and_extract_frames']
    data = {'utterance': utterance,
            'grammar': grammar_id,
            'package':package}
    return post(endpoint, data)
