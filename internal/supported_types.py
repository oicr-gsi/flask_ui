"""

 These are classes for handling entry types which are supported by flask_ui

 classes provide methods for rendering html elements and hold the internal
 values for displaying in UI

"""
SEP = '$'


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
                <label>linkout_to_simpsonlab</label> \
                </li> \
                <ul class="nested" style="list-style: none;"> \
                <li class="inline field"> \
                    <div class="ui right pointing label"> \
                        contents \
                    </div> \
                    <input type="text" id="{self.my_id}{SEP}contents" size="8" name="{self.my_id}{SEP}$contents" placeholder="null"> \
                </li> \
                <li class="inline field"> \
                    <div class="ui right pointing label"> \
                        type \
                    </div> \
                    <input type="text" id="{self.my_id}{SEP}type" size="8" name="{self.my_id}{SEP}type" placeholder="SKIP"> \
                </li> \
                </ul>'


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

