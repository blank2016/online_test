from __future__ import unicode_literals
import importlib
import json
import six  

# Local imports
from .settings import code_evaluators

registry = None
    
def get_registry():
    global registry
    if registry is None:
        registry = _LanguageRegistry()
    return registry

def unpack_json(json_data):
    data = json.loads(json_data)
    return data

def create_evaluator_instance(language, test_case_type, json_data, in_dir):
    """Create instance of relevant EvaluateCode class based on language"""
    registry = get_registry()
    cls = registry.get_class(language, test_case_type)
    instance = cls(in_dir)
    return instance

class _LanguageRegistry(object):
    def __init__(self):
        self._register = {}
        for language, module in six.iteritems(code_evaluators):
            self._register[language] = None

    # Public Protocol ##########
    def get_class(self, language, test_case_type):
        """ Get the code evaluator class for the given language """
        if not self._register.get(language):
            self._register[language] = code_evaluators.get(language)

        test_case_register = self._register[language]
        cls = test_case_register.get(test_case_type)
        module_name, class_name = cls.rsplit(".", 1)
        # load the module, will raise ImportError if module cannot be loaded
        get_module = importlib.import_module(module_name)
        # get the class, will raise AttributeError if class cannot be found
        get_class = getattr(get_module, class_name)
        return get_class

    def register(self, language, class_names):
        """ Register a new code evaluator class for language"""
        self._register[language] = class_names

