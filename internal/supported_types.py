"""

 These are classes for handling entry types which are supported by flask_ui
 classes provide methods for rendering html elements and hold the internal
 values for displaying in UI

"""

RESOURCE_KEYS = ['gencode', 'reference']
SUPPORTED_OVERVIEW_MODES = [{"id": "fromFile", "title": "Current configuration (.jsonconfig file)"},
                            {"id": "fromState", "title": "Updated configuration (memory)"}]

def get_supported():
    return ['s', 'object']

"""
   Flatten nested array and return string in array if needed
   This function handles 'as' type at present but should go into AS class
   eventually. Also, other classes may use validate_value() function
   which would ensure correct formatting of the dict structure
   that goes into project_config_info.jsonfile
"""
def flatten(entry):
    if entry is None:
        return None
    if isinstance(entry, list):
        return [item for sublist in entry for item in sublist]
    elif isinstance(entry, str):
        return [entry]
    return None

"""This function will return a default value for an interface element depending on type"""
def get_rendered(element_id: str, entry_type: str):
    if entry_type == 's':
        my_element = S(element_id)
        return my_element.render_element()
    if entry_type == 'object':
        my_element = OBJECT(element_id)
        return my_element.render_element()
    return None


class S:
    def __init__(self, my_id: str):
        self.my_id = my_id

    def render_element(self):
        return f'<li class="ui checkbox"> \
                  <input type="checkbox" id="{self.my_id}" name="{self.my_id}" class="subOption"> \
                  <label>{self.my_id}</label> \
                </li> \
                <br>'

    @staticmethod
    def get_default():
        return False

'''This is exclusively for rendering reference box'''
class OBJECT:
    def __init__(self, my_id: str):
        self.my_id = my_id

    def render_element(self):
        return f'<li class="inline field"> \
             <div class="ui right pointing label"> \
             {self.my_id} \
             </div> \
             <input type="text" id="{self.my_id}" name="{self.my_id}" size="8"> \
             </li>'

    @staticmethod
    def get_default():
        return "Enter value"
