"""

 These are classes for handling entry types which are supported by flask_ui

 classes provide methods for rendering html elements and hold the internal
 values for displaying in UI


"""
SEP = '$'
REF_KEY = 'reference_for_species'


def get_supported():
    return ['qi', 'b', 'i', 's', 'algebraic', 'msas', 'object']


"""This function will return a default value for an interface element depending on type"""


def get_default_value(entry_type: str, entry_value=None):
    if entry_type == 'b':
        return B.get_default()
    if entry_type == 'i':
        return I.get_defaults()
    if entry_type == 'qi':
        return QI.get_default()
    if entry_type == 's':
        return S.get_default()
    if entry_type == 'algebraic':
        return ALGEBRAIC.get_default(entry_value)
    if entry_type == 'msas':
        return MSAS.get_default()
    if entry_type == 'object':
        return OBJECT.get_default()


"""This function will return a default value for an interface element depending on type"""


def get_rendered(element, element_id: str, entry_type: str, index=0, drop_items=None, parent=None):
    if entry_type == 'b':
        my_element = B(element_id, parent)
        return my_element.render_element()
    if entry_type == 'i':
        my_element = I(element_id, parent)
        return my_element.render_element()
    if entry_type == 'qi':
        my_element = QI(element_id, parent)
        return my_element.render_element()
    if entry_type == 's':
        my_element = S(element_id, parent)
        return my_element.render_element()
    if entry_type == 'algebraic':
        my_element = ALGEBRAIC(element, element_id, parent)
        return my_element.render_element()
    if entry_type == 'msas':
        my_element = MSAS(element_id, index, drop_items, parent)
        return my_element.render_element()
    if entry_type == 'object':
        my_element = OBJECT(element_id, parent)
        return my_element.render_element()


class QI:
    def __init__(self, my_id: str, parent=None):
        self.my_id = my_id
        self.parent = parent
        if self.parent is not None:
            self.parented_id = SEP.join([self.parent, self.my_id])
        else:
            self.parented_id = self.my_id

    def render_element(self):
        return f'<li class="inline field"> \
                   <div class="ui right pointing label"> \
                     {self.my_id} \
                   </div> \
                   <input type="text" id="{self.parented_id}" name="{self.parented_id}" size="3"> \
                  </li>'

    @staticmethod
    def get_default():
        return None


class B:
    def __init__(self, my_id: str, parent=None):
        self.my_id = my_id
        self.parent = parent
        if self.parent is not None:
            self.parented_id = SEP.join([self.parent, self.my_id])
        else:
            self.parented_id = self.my_id

    def render_element(self):
        return f'<li class="ui checkbox"> \
                  <input type="checkbox" id="{self.parented_id}" name="{self.parented_id}" class="subOption"> \
                  <label>{self.my_id}</label> \
                </li> \
                <br>'

    @staticmethod
    def get_default():
        return False


class S:
    def __init__(self, my_id: str, parent: str):
        self.my_id = my_id
        self.parent = parent
        if self.parent is not None:
            self.parented_id = SEP.join([self.parent, self.my_id])
        else:
            self.parented_id = self.my_id

    def render_element(self):
        return f'<li class="inline field"> \
             <div class="ui right pointing label"> \
             {self.my_id} \
             </div> \
             <input type="text" id="{self.parented_id}" name="{self.parented_id}" size="8"> \
             </li>'

    @staticmethod
    def get_default():
        return "Enter value"


class ALGEBRAIC:
    def __init__(self, value: dict, my_id: str, parent: str):
        self.value = value
        self.my_id = my_id
        self.parent = parent
        self.drop_items = list(value['union'].keys())
        self.default_drop_item = self.drop_items[0]
        """We put the last item with value null as a default"""
        for key, value in value['union'].items():
            if value is None:
                self.default_drop_item = key
        if self.parent is not None:
            self.parented_id = SEP.join([self.parent, self.my_id])
        else:
            self.parented_id = self.my_id

    def render_element(self):
        drop_divs = ""
        for di in self.drop_items:
            drop_divs += f'<div class="item" data-value="{di}">{di}</div>' + "\n"
        return f'<li class="ui checkbox"> \
                <input type="checkbox" id="{self.parented_id}" name="{self.parented_id}" class="option"> \
                <label>{self.my_id}</label> \
                <ul class="nested" style="list-style: none;"> \
                <li class="inline field"> \
                    <div class="ui right pointing label"> \
                        contents \
                    </div> \
      <input type="text" id="{self.my_id}{SEP}contents" size="8" name="{self.my_id}{SEP}contents" placeholder="null"> \
                </li> \
                <li class="inline field"> \
                    <div class="ui right pointing label"> \
                        type \
                    </div> \
                    <div class="ui dropdown" id="{self.my_id}-type_selector"> \
                       <input type="hidden" id="hidden_{self.my_id}{SEP}type" name="{self.my_id}{SEP}type"> \
                       <i class="dropdown icon"></i> \
                       <div class="default text" id="{self.my_id}{SEP}type">{self.default_drop_item}</div> \
                       <div class="menu"> \
                         {drop_divs} \
                       </div> \
                    </div> \
                </li> \
                </ul> \
                </li>'

    @staticmethod
    def get_default(entry):
        last_element = "NOTSET"
        """Set last_element to id of the last entry with value null"""
        for key, value in entry.items():
            if value == "null" or value is None:
                last_element = key
        return {"contents": None, "type": last_element}


class OBJECT:
    def __init__(self, my_id: str, parent=None):
        self.my_id = my_id
        self.parent = parent
        if self.parent is not None:
            self.parented_id = SEP.join([self.parent, self.my_id])
        else:
            self.parented_id = self.my_id

    """Note that we assume downstream elements, so <li> and <ul> tags must be closed elsewhere"""

    def render_element(self):
        return f'<li class="ui checkbox"> \
                 <input type="checkbox" id="{self.parented_id}" name="{self.parented_id}" class="option"> \
                 <label>{self.my_id}</label> \
                 <ul class="nested" style="list-style: none;">'

    @staticmethod
    def get_default():
        return None


class I:
    def __init__(self, my_id: str, parent: str):
        self.my_id = my_id
        self.parent = parent
        if self.parent is not None:
            self.parented_id = SEP.join([self.parent, self.my_id])
        else:
            self.parented_id = self.my_id

    def render_element(self):
        return f'<li class="inline field"> \
                   <div class="ui right pointing label"> \
                     {self.my_id} \
                   </div> \
                   <input type="text" id="{self.parented_id}" name="{self.parented_id}" size="2" placeholder="0"> \
                  </li>'

    @staticmethod
    def get_defaults():
        return 0


""" This is the only object for which we will call render_element() when a project selected """


class MSAS:
    def __init__(self, my_id: str, idx: int, drop_items: list, parent: str):
        self.my_id = my_id
        self.parent = parent
        self.idx = idx
        self.drop_items = drop_items
        if self.parent is not None:
            self.parented_id = SEP.join([self.parent, self.my_id])
        else:
            self.parented_id = self.my_id

    def render_element(self):
        drop_divs = ""
        for species in self.drop_items:
            drop_divs += f'<div class="item" name="{species}">{species}</div>' + "\n"
        return f'<li class="ui right labeled input" style="width: 150px"> \
        <input type="text" id="reference_assembly{self.idx}" name="reference_assembly{self.idx}" placeholder="hg38" style="resize: none;"> \
        <div class="ui dropdown label" id="{REF_KEY}_selector{self.idx}"> \
        <div class="text" id="{self.parented_id}{self.idx}">{list(self.drop_items)[0]}</div> \
        <input type="hidden" id="hidden_{self.my_id}{self.idx}" name="{self.my_id}{self.idx}"> \
        <i class="dropdown icon"></i> \
        <div class="menu"> \
         {drop_divs} \
        </div> \
        </li>'

    @staticmethod
    def get_default():
        return None
