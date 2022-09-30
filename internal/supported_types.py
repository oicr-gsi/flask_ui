"""

 These are classes for handling entry types which are supported by flask_ui

 classes provide methods for rendering html elements and hold the internal
 values for displaying in UI


"""
SEP = '$'


def get_default_value(entryType: str, entryValue=None):
    if entryType == 'b':
        return B.get_default()
    if entryType == 'qi':
        return QI.get_default()
    if entryType == 's':
        return S.get_default()
    if entryType == 'algebraic':
        return ALGEBRAIC.get_default(entryValue)
    if entryType == 'i':
        return I.get_defaults()
    if entryType == 'msas':
        return MSAS.get_default(entryValue)


class QI:
    def __init__(self, value: int, my_id: str, parent=None):
        self.value = value
        self.my_id = my_id
        self.parent = parent
        if self.parent is not None:
            self.parented_id = SEP.join([self.my_id, self.parent])
        else:
            self.parented_id = self.my_id

    def render_element(self):
        return f'<li class="inline field" placeholder="Enter Value"> \
                   <div class="ui right pointing label"> \
                     {self.my_id} \
                   </div> \
                   <input type="text" id="{self.parented_id}" name="{self.my_id}" size="3"> \
                  </li>'

    @staticmethod
    def get_default():
        return None


class B:
    def __init__(self, value: bool, my_id: str, parent=None):
        self.value = value
        self.my_id = my_id
        self.parent = parent
        if self.parent is not None:
            self.parented_id = SEP.join([self.my_id, self.parent])
        else:
            self.parented_id = self.my_id

    def render_element(self):
        return f'<li class="ui_checkbox"> \
                  <input type="checkbox" id="{self.parented_id}" name="{self.my_id}" class="subOption"> \
                  <label>{self.my_id}</label> \
                </li>'

    @staticmethod
    def get_default():
        return False


class S:
    def __init__(self, value: str, my_id: str, parent: str, placeholder: str):
        self.value = value
        self.my_id = my_id
        self.parent = parent
        self.placeholder = placeholder
        if self.parent is not None:
            self.parented_id = SEP.join([self.my_id, self.parent])
        else:
            self.parented_id = self.my_id

    def render_element(self):
        return f'<li class="inline field"> \
                   <div class="ui right pointing label"> \
                     {self.my_id} \
                   </div> \
                   <input type="text" id="{self.parented_id}" name="{self.parented_id}" size="8" placeholder="{self.placeholder}"> \
                 </li>'

    @staticmethod
    def get_default():
        return "Enter Value"


class ALGEBRAIC:
    def __init__(self, value: str, my_id: str, parent: str, placeholder: str):
        self.value = value
        self.my_id = my_id
        self.parent = parent
        self.placeholder = placeholder
        if self.parent is not None:
            self.parented_id = SEP.join([self.my_id, self.parent])
        else:
            self.parented_id = self.my_id

    def render_element(self):
        return f'<li class="ui checkbox"> \
                <input type="checkbox" id="{self.parented_id}" name="{self.parented_id}" class="option"> \
                <label>{self.my_id}</label> \
                </li> \
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
                    <input type="text" id="{self.my_id}{SEP}type" size="8" name="{self.my_id}{SEP}type" placeholder="{self.placeholder}"> \
                </li> \
                </ul>'

    @staticmethod
    def get_default(entry):
        last_element = "NOTSET"
        """Set last_element to id of the last entry with value null"""
        for key, value in entry.items():
            if value == "null" or value is None:
                last_element = key
        return {"contents": None, "type": last_element}


class I:
    def __init__(self, value: int, my_id: str, parent: str):
        self.value = value
        self.my_id = my_id
        self.parent = parent
        if self.parent is not None:
            self.parented_id = SEP.join([self.my_id, self.parent])
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


class MSAS:
    def __init__(self, value: int, my_id: str, parent: str):
        self.value = value
        self.my_id = my_id
        self.parent = parent
        if self.parent is not None:
            self.parented_id = SEP.join([self.my_id, self.parent])
        else:
            self.parented_id = self.my_id

    def render_element(self): # TODO : need to fix this
        return f'<li class="ui right labeled input" style="width: 150px"> \
                 <input type="text" id="reference_assembly" name="reference_assembly" placeholder="hg38" style="resize: none;"> \
                 <div class="ui dropdown label" id="select-org"> \
                 <div class="text" id="reference_for_species">HOMO SAPIENS</div> \
                 <input type="hidden" id="hidden_reference_for_species" name="reference_for_species"> \
                 <i class="dropdown icon"></i> \
                 <div class="menu" onselect="static/js/menu_select.js"> \
                   <div class="item" name="HOMO SAPIENS">HOMO SAPIENS</div> \
                   <div class="item" name="MUS MUSCULUS">MUS MUSCULUS</div> \
                   <div class="item" name="ARABIDOPSIS THALIANA">ARABIDOPSIS THALIANA</div> \
                   <div class="item" name="GASTEROSTEUS ACULEATUS">GASTEROSTEUS ACULEATUS</div> \
                   <div class="item" name="LEPUS AMERICANUS">LEPUS AMERICANUS</div> \
                   <div class="item" name="SCHIZOSACCHAROMYCES POMBE">SCHIZOSACCHAROMYCES POMBE</div> \
                 </div> \
                 </div> \
                 </li>'

