"""
  1. load assay_info file
  2. Scan available olives and use the Run lines to get all names
  3. going through items (one by one) use the rules from supported_types collection of classes
     and prepare data objects -
     a. list based on olive scan - all available (deployed) workflows
     b. types - a dict, names must be unique throughout so we don't have the same name
     c. assemblies - reference gets special treatment, we collect everything for drop selector
"""
from internal import supported_types
from bs4 import BeautifulSoup as Bs

"""
  Load workflow list, render UI
"""
class updateUi:

    def __init__(self, workflows: list, reference: str):
        self.ui = ""
        self.render_ui(workflows, reference)

    """Getter function for UI snippet"""
    def get_ui(self):
        return self.ui

    """ Render workflow selection UI here """
    def render_ui(self, workflows: list, reference: str):
        my_html = '<ul style="list-style: none;" xmlns:input="http://www.w3.org/1999/html">'
        for wf in workflows:
            '''Render checkboxes'''
            my_html += supported_types.get_rendered(wf, 's')
        '''Render a text box with reference'''
        my_html += supported_types.get_rendered(reference, 'object')
        soup = Bs(my_html, "html.parser")
        self.ui = soup.prettify()
