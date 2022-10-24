"""
  1. load project_info file
  2. Extract 'type' facet from the config and parse it with a function that uses recursion
  3. going through items (one by one) use the rules from supported_types collection of classes
     and prepare data objects -
     a.) defaults dict - this is to have pre-filled values for the interface to work correctly
     b.) list based on nested_list.html - all elements properly parented and rendered according to their type (ui)
     c.) types - a dict, names must be unique throughout so we don't have the same name
     d.) assemblies - reference_for_species gets special treatment, we collect everything for drop selector
"""
from internal import supported_types
from bs4 import BeautifulSoup as Bs
import copy

"""
  Some project-specific fields are not going into presets
"""
fields_to_skip = ['swgs_sequencer', 'lab_priority', supported_types.REF_KEY]
"""
  Load config, process the the facet with types
"""


class updateUi:
    """ We need only types part"""

    def __init__(self, ui_config: dict):
        self.config = ui_config
        self.defaults = {}
        self.entry_types = {}
        self.ui = None
        self.assemblies = {}
        if 'types' in ui_config.keys():
            self.defaults = self.vetted_defaults(ui_config['types'])  # populate defaults, types and print ui
            self.obtain_assemblies()
            self.render_ui()
        else:
            print("The config file does not have types defined")

    """Getter function for defaults"""

    def get_defaults(self):
        return self.defaults

    """Getter function for UI snippet"""

    def get_ui(self):
        return self.ui

    """Getter for types"""

    def get_types(self):
        return self.entry_types

    """Getter for all available assemblies"""

    def get_assemblies(self):
        return self.assemblies

    """ Get all reference values from config's values slot """

    def obtain_assemblies(self):
        for project in self.config['values'].keys():
            if supported_types.REF_KEY in self.config['values'][project].keys():
                next_chunk = self.config['values'][project][supported_types.REF_KEY]
                if isinstance(next_chunk, dict):
                    self.assemblies.update(next_chunk)

    """ This is for recursive update of presets """

    def vet_recursively(self, presets: dict, parameter_defaults: dict) -> dict:
        """ We want add missing but avoid overriding existing values """
        for d in parameter_defaults.keys():
            if d not in presets.keys() and d not in fields_to_skip:
                print("Adding " + d)
                presets[d] = parameter_defaults[d]
        presets_copy = copy.deepcopy(presets)
        for current in presets.keys():
            if current not in parameter_defaults.keys():
                print("Removing " + current)
                presets_copy.pop(current, None)
            elif isinstance(presets[current], dict) and isinstance(parameter_defaults[current], dict):
                presets_copy[current] = self.vet_recursively(presets_copy[current], parameter_defaults[current])
        return presets_copy

    """ Function for vetting presets, returns presets compliant with config """

    def vetted_presets(self, presets: dict) -> dict:
        """ Handle both adding and removing the keys! """
        vetted_presets = {'presets': {}}
        for preset in presets['presets'].keys():
            vetted_presets['presets'][preset] = self.vet_recursively(presets['presets'][preset], self.defaults)
        return vetted_presets

    """ Function for vetting defaults, returns a dict in-sync with config. Recursive"""

    def vetted_defaults(self, types: dict) -> dict:
        vetted = {}
        for key, entry in types.items():
            if isinstance(entry, dict):
                if 'inner' in entry.keys() and 'fields' in entry['inner'].keys():
                    self.entry_types[key] = entry['inner']['is']
                    vetted[key] = self.vetted_defaults(entry['inner']['fields'])
                elif 'is' in entry.keys() and entry['is'] == 'algebraic':
                    self.entry_types[key] = entry['is']
                    vetted[key] = supported_types.get_default_value('algebraic', entry['union'])
            elif entry == 'msas':
                self.entry_types[key] = entry
                vetted[key] = self.config['defaults'][key]
            else:
                self.entry_types[key] = entry
                vetted[key] = supported_types.get_default_value(types[key], entry)
        return vetted

    """ 
     Function for rendering UI - main function of this class 
     in special cases (such as msas for reference species) we put a tag instead of
     html code built from id and _TAG (all uppercase)
    """

    def add_recursively(self, content: dict, parent=None):
        html_strings = ""
        for key, value in content.items():
            if isinstance(value, dict):
                if self.entry_types[key] == 'object':
                    html_strings += supported_types.get_rendered(value, key, 'object', 0, None, parent)
                    html_strings += self.add_recursively(value['inner']['fields'], key)
                    html_strings += "</ul></li><br>"
                elif self.entry_types[key] == 'algebraic':
                    html_strings += supported_types.get_rendered(value, key, 'algebraic', 0, None, parent)
            elif self.entry_types[key] in supported_types.get_supported():
                if self.entry_types[key] == 'msas':
                    html_strings += "_".join([key.upper(), "TAG"])
                else:
                    html_strings += supported_types.get_rendered(value, key, self.entry_types[key], 0, None, parent)
        return html_strings

    def render_ui(self):
        my_html = '<ul style="list-style: none;" xmlns:input="http://www.w3.org/1999/html">'
        my_ui = my_html + self.add_recursively(self.config['types'])
        soup = Bs(my_ui, "html.parser")
        self.ui = soup.prettify()
