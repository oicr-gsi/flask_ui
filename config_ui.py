from __future__ import absolute_import
import copy
import json
import os
import re
import sys
from bs4 import BeautifulSoup as Bs
from flask import Flask, render_template, request
from internal import supported_types
from internal import update_ui


def create_app(debug=True):
    app = Flask(__name__)
    with app.app_context():
        app.config.from_envvar('UICONFIG_SETTINGS')
        return app


app = create_app()
project_list = []
preset_list = []
config = None
config_path = None
defaults = None
presets = None
config_updater = None

"""Get all projects, they are under values key in config object"""


def init():
    global project_list
    global preset_list
    global config
    global config_path
    global defaults
    global presets
    global config_updater
    preset_list = []

    if not project_list:
        app.config.from_envvar('UICONFIG_SETTINGS')
        config_path = app.config['CONFIG_PATH']
        preset_path = app.config['PRESET_PATH']
        with open(os.path.join(os.path.dirname(sys.argv[0]), config_path), 'r') as f:
            config = json.load(f)
        """ generate ui-updating object """
        config_updater = update_ui.updateUi(config)
        defaults = config_updater.get_defaults()
        with open(os.path.join(os.path.dirname(sys.argv[0]), preset_path), 'r') as pr:
            current_presets = json.load(pr)
        presets = config_updater.vetted_presets(current_presets)
        """ if presets were changed, save the updates to disk """
        if current_presets != presets:
            print("Presets were changed, writing to disk...")
            with open(os.path.join(os.path.dirname(sys.argv[0]), preset_path), 'w') as fp:
                json.dump(presets, fp, sort_keys=True, indent=2)
        refresh()
        for r in presets['presets']:
            preset_list.append(dict(id=r, title=r))


"""Reload project_list from global config"""


def refresh():
    global project_list
    global config
    project_list = []
    for p in config['values']:
        project_list.append(dict(id=p, title=p))


"""Check what we have enabled for a given project and return as a dict"""


def obtain_enabled(project_json: object, parent="") -> object:
    global config_updater

    boxes = []
    texts = []
    opts = []
    entry_types = config_updater.get_types()

    for entry in project_json.keys():
        if project_json.get(entry) is None:
            continue
        entry_id = parent + entry
        if isinstance(project_json[entry], dict):
            """Treat reference in a special way"""
            if entry_types[entry] == 'msas':
                for sp in range(0, len(project_json[entry])):
                    species = list(project_json[entry].keys())[sp]
                    assembly = project_json[entry][species][0]
                    opts.append(dict(id=f'{entry}_selector{sp}', value=species))
                    texts.append(dict(id=f'reference_assembly{sp}', value=assembly))
                continue
            if entry_types[entry] == 'algebraic':
                opts.append(dict(id='-'.join([entry, "type_selector"]),
                                 value=project_json[entry]['type']))
                boxes.append(dict(id=entry_id, status=True))
                if isinstance(project_json[entry]['contents'], list):
                    texts.append(dict(id=supported_types.SEP.join([entry, 'contents']),
                                      value=",".join(project_json[entry]['contents'][0])))
                continue
            boxes.append(dict(id=entry_id, status=True))
            nested = obtain_enabled(project_json[entry], entry + supported_types.SEP)
            boxes = boxes + nested[0]
            texts = texts + nested[1]
            opts = opts + nested[2]
        elif project_json[entry] == True:
            boxes.append(dict(id=entry_id, status=True))
        else:
            if type(project_json[entry]) in [str, int, float]:
                texts.append(dict(id=entry_id, value=project_json[entry]))
            if isinstance(project_json[entry], list):
                texts.append(dict(id=entry_id, value=",".join(project_json[entry][0])))

    return boxes, texts, opts


""" De-serialize parent/child ids, make another level of dict for entries with parent """


def parseUpdate(update_object):
    parsed_dict = {}
    for key, value in update_object.items():
        """ hard-coded, but can be kept as is - we define these names in base.html"""
        if key in ['Project', 'updatedProject', 'selected_preset', 'json_review', 'update_button']:
            continue
        if isinstance(value, str) and value == 'on':
            value = True
        parent_child = key.split(supported_types.SEP)
        if len(parent_child) == 2:
            if parsed_dict.get(parent_child[0]) and isinstance(parsed_dict[parent_child[0]], dict):
                parsed_dict[parent_child[0]].update({parent_child[1]: value})
            else:
                parsed_dict[parent_child[0]] = {parent_child[1]: value}
        elif len(parent_child) == 1:
            parsed_dict[parent_child[0]] = value
        else:
            print("Broken parent_child key")
    return parsed_dict


"""
  Small utility to translate form data into proper dict flags
  ATTENTION: if a string with commas is passed, it will be converted to list
"""


def parse_override(value):
    if value == '':
        return None
    elif value == 'on':
        return True
    elif value in (True, False):
        return value
    elif isinstance(value, str) and ',' in value:
        return [value.split(',')]
    elif value.isnumeric():
        return int(value)
    elif value[0].isdigit():
        return float(value)
    else:
        return value


"""
 text inputs get submitted even if there are no values entered. 
 This function filters entries which only have empty strings.
 Everything else is Ok
"""


def not_only_empty(entry, to_check: dict) -> bool:
    global config_updater
    passed_filter = False
    if entry in config_updater.get_types().keys() and config_updater.get_types()[entry] != 'object':
        return True
    for key in to_check.keys():
        if key in config_updater.get_types().keys():
            if config_updater.get_types()[key] != 's':
                passed_filter = True
            elif to_check[key] != '':
                passed_filter = True
    return passed_filter


"""Subroutine to update a dict for inserting into main config"""


def update_project(to_update, overrides, master_overrides=None):
    """
    Update a nested dictionary or similar mapping.
    reference_for_species gets a special treatment.
    """
    if not master_overrides:
        master_overrides = overrides
    to_return = copy.deepcopy(to_update)
    if isinstance(to_update, dict):
        for key in to_update.keys():
            if key == supported_types.REF_KEY:
                updated_refs = {}
                for over_key in overrides.keys():
                    if over_key.startswith(supported_types.REF_KEY):
                        if re.search('\d+$', over_key):
                            ref_idx = re.search('\d+$', over_key).group(0)
                            if overrides[f'reference_assembly{ref_idx}']:
                                updated_refs[overrides[over_key].upper()] = [overrides[f'reference_assembly{ref_idx}']]
                if len(updated_refs) > 0:
                    to_return[supported_types.REF_KEY] = updated_refs
            elif isinstance(to_update[key], dict):
                if isinstance(overrides, dict):
                    if key in overrides.keys():
                        if isinstance(master_overrides, dict):
                            if key in master_overrides.keys() and not_only_empty(key, to_update[key]):
                                to_return[key] = update_project(to_update[key],
                                                                master_overrides[key],
                                                                master_overrides)
                            elif not_only_empty(key, to_update[key]):
                                to_return[key] = update_project(to_update[key],
                                                                {},
                                                                master_overrides)
                        else:
                            continue
                    else:
                        to_return[key] = None
                else:
                    to_return[key] = update_project(to_update[key], overrides, master_overrides)
            elif isinstance(overrides, dict) and key in overrides.keys():
                to_return[key] = update_project(to_update[key], overrides[key], master_overrides)
    else:
        """ Update a single value """
        to_return = parse_override(overrides)
    return to_return


""" Special function for inserting references into dynamically generated HTML UI """


def append_refs(project: str):
    global config
    global config_updater

    ui = config_updater.get_ui()

    my_refinfo = config['values'][project][supported_types.REF_KEY]
    """ We just need to know how many at this point, javascript will fill these in """
    if isinstance(my_refinfo, dict):
        my_addon = ""
        my_refs = config_updater.get_assemblies()
        for sp in range(0, len(my_refinfo)):
            my_addon += supported_types.get_rendered(None, supported_types.REF_KEY, 'msas', sp, my_refs)
            """ One break b/w species selectors is needed but with two the UI looks better """
            if sp < (len(my_refinfo) - 1):
                my_addon += "<br/><br/>"
        ui = ui.replace("REFERENCE_FOR_SPECIES_TAG", my_addon)
    soup = Bs(ui, "html.parser")
    pretty_ui = soup.prettify()
    return pretty_ui


""" Index generation, the landing page to start an editing session """


@app.route("/")
def index():
    global project_list
    global preset_list
    global config
    project = project_list[0]['id']
    """We need to pass only the enabled pipelines, js script will put the checkmarks accordingly"""
    json_snippet = config['values'][project]
    enabled_workflows = obtain_enabled(json_snippet)
    json_text = json.dumps(json_snippet, sort_keys=True, indent=2)
    nested_list = append_refs(project)
    return render_template('base.html', project_list=project_list,
                           preset_list=preset_list,
                           selected_project=project,
                           nested_list=nested_list,
                           json_snippet=json_text,
                           checkbox_list=enabled_workflows[0],
                           texts_list=enabled_workflows[1],
                           opts_list=enabled_workflows[2])


""" Upon selection of a project or preset update the values in the form """


@app.route('/select', methods=['POST'])
def select():
    global project_list
    global preset_list
    global config
    global defaults

    if request.method == 'POST':
        project = request.form.get('selected_project')  # parse project
        preset = request.form.get('selected_preset')  # parse preset
        updated_project = request.form.get('updated_project')
        messages = []

        """ Prepare the data for rendering: """
        if preset and project == updated_project:
            preset_snippet = presets['presets'][preset]
            json_snippet = config['values'][project]
            json_snippet.update(preset_snippet)
            config['values'][project].update(json_snippet)
            messages.append(dict(title="Warning",
                                 body="Preset " + preset + " was applied to project " + project))
        json_snippet = config['values'][project]
        enabled_workflows = obtain_enabled(json_snippet)
        json_text = json.dumps(json_snippet, sort_keys=True, indent=2)
        nested_list = append_refs(project)
        return render_template('base.html', project_list=project_list,
                               preset_list=preset_list,
                               selected_project=project,
                               selected_preset=preset,
                               nested_list=nested_list,
                               json_snippet=json_text,
                               messages=messages,
                               checkbox_list=enabled_workflows[0],
                               texts_list=enabled_workflows[1],
                               opts_list=enabled_workflows[2])


""" Clone a project """


@app.route("/clone", methods=["POST"])
def clone():
    global project_list
    global preset_list
    global config

    project = request.form.get("project")
    cln = request.form.get("clone")
    if cln:
        config['values'][cln] = copy.deepcopy(config['values'][project])
        """ Order projects alphabetically """
        od = {k: v for k, v in sorted(config['values'].items())}
        config['values'] = copy.deepcopy(od)
        refresh()
        messages = [dict(title="Warning", body="Project " + project + " cloned into " + cln)]
    else:
        messages = [dict(title="Warning", body="You need to specify a name of the project to clone to")]
    print(messages[0]['body'])
    json_snippet = config['values'][cln] if cln else config['values'][project_list[0]['id']]
    enabled_workflows = obtain_enabled(json_snippet)
    json_text = json.dumps(json_snippet, sort_keys=True, indent=2)
    nested_list = append_refs(project)
    return render_template('base.html',
                           project_list=project_list,
                           preset_list=preset_list,
                           selected_project=cln,
                           nested_list=nested_list,
                           json_snippet=json_text,
                           messages=messages,
                           checkbox_list=enabled_workflows[0],
                           texts_list=enabled_workflows[1],
                           opts_list=enabled_workflows[2])


""" Update a project """


@app.route("/update/<string:project>", methods=["POST"])
def update(project):
    global project_list
    global preset_list
    global config
    global config_path

    messages = []
    """ Handle clicks on various update buttons """
    if request.form['update_button'] == "clone":
        messages = [dict(title="",
                         body="Project " + project + "Is being cloned")]
        return render_template('clone.html', selected_project=project, messages=messages)
    elif request.form['update_button'] == "reset":
        del project_list[:]
        del config
        print("Configuration was restored...")
        messages = [dict(title="Warning",
                         body="Configuration was restored from disk")]
        init()
    elif request.form['update_button'] == "write":
        print("Saving changes...")
        with open(config_path, "w") as f:
            json.dump(config, f, sort_keys=True, indent=2)
        messages = [dict(title="Warning",
                         body="Changes were written to disk, review and prepare a Pull Request")]
    elif request.form['update_button'] == "delete":
        del config['values'][project]
        refresh()
        messages = [dict(title="Warning",
                         body="Project " + project + " was Deleted...")]
        print(messages[0]['body'])
        project = project_list[0]['id']
    elif request.form.get('update_button') and request.form['update_button'] == "record":
        form_data = request.form
        form_dict = form_data.to_dict(flat=True)
        parsed_update = parseUpdate(form_dict)
        updated_config = update_project(defaults, parsed_update)

        """
        Debug messages, uncomment if needed
        form_json = json.dumps(form_dict)
        print("That is what we have submitted:")
        print(form_json) 

        print("Updated JSON:")
        myJSON = json.dumps(updated_config, indent=4)
        print(myJSON) 
        
        Main Updating step below:
       
        """

        config['values'][project].update(updated_config)
        messages.append(dict(title="Warning",
                             body="Changes NOT dumped to disk but retained in memory"))
    else:
        print("I received some unknown request")
    json_snippet = config['values'][project]
    enabled_workflows = obtain_enabled(json_snippet)
    json_text = json.dumps(json_snippet, sort_keys=True, indent=2)
    nested_list = append_refs(project)
    return render_template('base.html',
                           project_list=project_list,
                           preset_list=preset_list,
                           selected_project=project,
                           nested_list=nested_list,
                           json_snippet=json_text,
                           messages=messages,
                           checkbox_list=enabled_workflows[0],
                           texts_list=enabled_workflows[1],
                           opts_list=enabled_workflows[2])


""" The App starts here, check if have project_list and if NOT, initialize the app"""
if not project_list or len(project_list) == 0:
    init()

if __name__ == "__main__":
    app.run(debug=True)
