"""
  1. load project_info file
  2. Extract 'type' facet from the config and parse it with a function that uses recursion
  3. going through items (one by one) use the rules from supported_types collection of classes
     and assemble two outputs -
     a.) defaults dict - this is to have pre-filled values for the interface to work correctly
     b.) nested_list.html - all elements properly parented and rendered according to their type
"""
from internal import supported_types
import copy

config = None
config_path = None
defaults = None
"""
  Some project-specific fields are not going into presets
"""
fields_to_skip = ['lab_priority', 'reference_for_species']

"""
  Load config, process the the facet with types
"""


class updateUi:
    """ We need only types part"""

    def __init__(self, config: dict):
        self.config = config
        self.defaults = {}  # Here we store defaults
        self.ui = None  # TODO fill when we have defaults loaded and vetted
        if 'types' in config.keys():
            self.defaults = self.vetted_defaults(config['types'])  # This may have to populate defaults, types and print ui
        else:
            print("The config file does not have types defined")

    """Getter function for defaults"""

    def get_defaults(self):
        return self.defaults

    """ This is for recursive update of presets """

    def vet_recursively(self, presets: dict, defaults: dict) -> object:
        """ We want add missing but avoid overriding existing values """
        for d in defaults.keys():
            if d not in presets.keys() and d not in fields_to_skip:
                print("Adding " + d)
                presets[d] = defaults[d]
        presets_copy = copy.deepcopy(presets)
        for current in presets.keys():
            if current not in defaults.keys():
                print("Removing " + current)
                presets_copy.pop(current, None)
            elif isinstance(presets[current], dict) and isinstance(defaults[current], dict):
                presets_copy[current] = self.vet_recursively(presets_copy[current], defaults[current])
        return presets_copy

    """ Function for vetting presets, returns presets compliant with config """

    def vetted_presets(self, presets: dict) -> object:
        """ Handle both adding and removing the keys! """
        vetted_presets = {'presets': {}}
        for preset in presets['presets'].keys():
            vetted_presets['presets'][preset] = self.vet_recursively(presets['presets'][preset], self.defaults)
        return vetted_presets

    """ Function for vetting defaults, returns a dict in-sync with config. Recursive"""

    def vetted_defaults(self, types: dict) -> object:
        vetted = {}
        for key, entry in types.items():
            if isinstance(entry, dict):
                if 'inner' in entry.keys() and 'fields' in entry['inner'].keys():
                    vetted[key] = self.vetted_defaults(entry['inner']['fields'])
                elif 'is' in entry.keys() and entry['is'] == 'algebraic':
                    vetted[key] = supported_types.get_default_value('algebraic', entry['union'])
            elif entry == 'msas':
                vetted[key] = self.config['defaults'][key]
            else:
                vetted[key] = supported_types.get_default_value(types[key], entry)
        return vetted

    """ Function for rendering UI - main function of this class """

    def render_ui(self):
        pass
