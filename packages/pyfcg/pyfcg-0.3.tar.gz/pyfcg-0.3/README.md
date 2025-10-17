# PyFCG

*A Python interface to FCG and Babel, built on FCG Go.*

<!-- start -->
## Installation

The Python integration of FCG (aka PyFCG) is distributed as a pip-installable package.
To install this package from PyPI, run the following command.

```bash
$ pip install pyfcg
```

## Use

Once pip-installed, PyFCG can readily be imported as a module into Python programs. 
It is customary to define `fcg` as an alias for the PyFCG module, so that all functionality is available within the `fcg` namespace (functions and variables are thereby prefixed with fcg.)

You initialise PyFCG as follows:

```python
>>> import pyfcg as fcg
>>> fcg.init()
```

Many FCG functions depend on the fcg-go precompiled binary, which you loaded (or download if necessary) by calling the `init()` function. 
On macOS, you will need to accept opening the application bundle by clicking "open" in the popup window.

**Example: Creating an FCG Agent**

The `Agent` class will usually be your main entry point. 
The idea is that an agent has a grammar (of type `Grammar`), which in turn holds constructions (of type `Construction`). 
In PyFCG, a grammar will always be tied to an agent.
Upon creation, an agent is automatically initialised with an empty grammar, i.e. a grammar that holds zero constructions.

```python
>>> demo_agent = fcg.Agent()

>>> demo_agent
<Agent: agent (id: agent-42) ~ 0 constructions>

>>> demo_agent.grammar.size()
0
```

<!-- walkthrough-tutorials -->
## Walkthrough Tutorials

A more in-depth showcase of PyFCG's functionalities can be found in the following interactive notebooks.
Each of them walks you through the process of integrating PyFCG in a typical use case of FCG.

- Tutorial 1: [Grammar Formalisation and Testing](https://gitlab.ai.vub.ac.be/ehai/pyfcg/-/blob/main/docs/source/walkthrough_tutorials/grammar_writing.ipynb?ref_type=heads)
- Tutorial 2: [Learning Grammars from Corpora](https://gitlab.ai.vub.ac.be/ehai/pyfcg/-/blob/main/docs/source/walkthrough_tutorials/learning_grammars.ipynb?ref_type=heads)
- Tutorial 3: [The Canonical Naming Game](https://gitlab.ai.vub.ac.be/ehai/pyfcg/-/blob/main/docs/source/walkthrough_tutorials/naming_game.ipynb?ref_type=heads)
- Tutorial 4: [Modelling Emergent Communication](https://gitlab.ai.vub.ac.be/ehai/pyfcg/-/blob/main/docs/source/walkthrough_tutorials/grounded_naming_game.ipynb?ref_type=heads)



## Documentation

The tecnical documentation of PyFCG is available at [Read the Docs](https://pyfcg.readthedocs.io).

<!-- how-to-cite -->
## How to Cite

<!-- Van Eecke, P., & Beuls, K. (2025). [PyFCG: Fluid Construction Grammar in Python](https://arxiv.org/abs/2505.12920). *arXiv preprint*.

```bibtex
@article{vaneecke2025pyfcg,
    author = {Paul {Van Eecke} and Katrien Beuls},
    title = {PyFCG: Fluid Construction Grammar in Python},
    year = {2025},
    journal = {arXiv preprint arXiv:},
    doi = {10.48550/arXiv.2505.12920},
}
```
-->
Temporarily anonymised for reviewing purposes (but ArXiv's your friend).