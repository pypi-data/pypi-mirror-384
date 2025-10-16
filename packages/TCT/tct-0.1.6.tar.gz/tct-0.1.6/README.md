Introduction
==================================

## What is TCT?
Translator Component Toolkit is a python library that allowing users to explore and use KGs in the Translator ecosystem.
Users can check out the key function documentations here: https://ncatstranslator.github.io/Translator_component_toolkit/ 

## Key features for TCT
Allowing users to select APIs, predicates according to the user's intention. <br>
Parallel and fast querying of the selected APIs.<br>
Providing reproducible results by setting constraints.<br>
Allowing testing whether a user defined API follows a [TRAPI](https://github.com/NCATSTranslator/ReasonerAPI) standard or not. <br>
Faciliting to explore knowledge graphs from both Translator ecosystem and user defined APIs.<br>
Connecting large language models to convert user's questions into TRAPI queries. <br>

## How to use TCT

### Install Requirements

To install TCT as a python library:

```bash
pip install TCT
```

**This the recommended approach for installation.**


#### Development Installation

The TCT is continuously updated, if you would like to use the latest functions, you can clone this repository and install it in development mode:

**Using UV (recommended for development):**
```bash
git clone https://github.com/NCATSTranslator/Translator_component_toolkit.git
cd Translator_component_toolkit
uv sync
```

**Using pip:**
```bash
git clone https://github.com/NCATSTranslator/Translator_component_toolkit.git
cd Translator_component_toolkit
pip install -e .
```

#### Building and Deployment

**Using UV:**
- Build: `uv build`
- Install dependencies: `uv sync`
- Run in UV environment: `uv run python your_script.py`

**Using pip:**
- Build: `python -m build`
- Install dependencies: `pip install -e .`


### Please follow the example notebooks (four utilities) below to explore the Translator APIs.

#### KG overview
Explore different KGs **[KG overview](https://github.com/gloriachin/Translator_component_toolkit/tree/main/notebooks/overview_of_KGs.ipynb)**

#### Neighborhood finder
Example notebook for **[NeighborhoodFinder](https://github.com/gloriachin/Translator_component_toolkit/tree/main/notebooks/Neighborhood_finder.ipynb)**

#### Path finder
Example notebook for **[PathFinder](https://github.com/gloriachin/Translator_component_toolkit/tree/main/notebooks/Path_finder.ipynb)**

#### Network finder
Example notebook for **[NetworkFinder](https://github.com/gloriachin/Translator_component_toolkit/tree/main/notebooks/Network_finder.ipynb)**

#### Translate users' questions into TRAPI queries
Example notebook for translating users' questions into TRAPI queries can be found [here](https://github.com/gloriachin/Translator_component_toolkit/tree/main/notebooks/Question2Query_chatGPT.ipynb). 

#### Connecting to a user's API
API should be developed following the standard from [TRAPI](https://github.com/NCATSTranslator/ReasonerAPI). <br>
An example notebook for add a user's API can be found [here](https://github.com/gloriachin/Translator_component_toolkit/tree/main/notebooks/Connecting_userAPI.ipynb).<br>
**Warning: It does not work if no user' API is established**<br>

## Key Translator components
Connecting to key Translator components can be found [here](https://github.com/gloriachin/Translator_component_toolkit/tree/main/TranslatorComponentsIntroduction.md)

### Contributing
TCT is a tool that helps to explore knowledge graphs developed in the Biomedical Data Translator Consortium. Consortium members and external contributors are encouraged to submit issues and pull requests. 

### Contact info
Guangrong Qin, guangrong.qin@isbscience.org
