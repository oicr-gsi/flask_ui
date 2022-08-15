from flask import Flask, render_template, request
import json
import os
import sys
import copy

app = Flask(__name__)
project_list = []
preset_list = []
config = None
config_path = None
defaults = None
defaults_path = None
presets = None

'''Get all projects, they are under values key in config object'''


def init():
    global project_list
    global preset_list
    global config
    global config_path
    global defaults
    global defaults_path
    global presets
    preset_list = []

    if not project_list:
        app.config.from_envvar('UICONFIG_SETTINGS')
        config_path = app.config['CONFIG_PATH']
        preset_path = app.config['PRESET_PATH']
        defaults_path = app.config['DEFAULTS_PATH']
        with open(os.path.join(os.path.dirname(sys.argv[0]), config_path), "r") as f:
            config = json.load(f)
        with open(os.path.join(os.path.dirname(sys.argv[0]), preset_path), "r") as pr:
            presets = json.load(pr)
        with open(os.path.join(os.path.dirname(sys.argv[0]), defaults_path), "r") as dp:
            defaults = json.load(dp)
        refresh()
        for r in presets["presets"]:
            preset_list.append(dict(id=r, title=r))


'''Reload project_list from global config'''


def refresh():
    global project_list
    global config
    project_list = []
    for p in config["values"]:
        project_list.append(dict(id=p, title=p))


'''Check what we have enabled for a given project and return as a dict'''


def obtain_enabled(project_json: object, parent=""):
    boxes = []
    texts = []
    opts = []
    for entry in project_json.keys():
        if project_json.get(entry) is None:
            continue
        entry_id = parent + entry
        if (type(project_json[entry]) is dict):
            '''Treat reference in a special way, may instead check for type in config['default']'''
            if entry == "reference_for_species":
                species = list(project_json[entry].keys())[0]
                assembly = project_json[entry][species][0]
                opts.append(dict(id="select-org", value=species))
                texts.append(dict(id="reference_assembly", value=assembly))
                continue
            boxes.append(dict(id=entry_id, status=True))
            nested = obtain_enabled(project_json[entry], entry + "$")  #TODO: fix, this is hard-coded
            boxes = boxes + nested[0]
            texts = texts + nested[1]
            opts = opts + nested[2]
        elif project_json[entry] == True:
            boxes.append(dict(id=entry_id, status=True))
        else:
            if type(project_json[entry]) in [str, int, float]:
                texts.append(dict(id=entry_id, value=project_json[entry]))
            if isinstance(project_json[entry], list):
                texts.append(dict(id=entry_id, value=project_json[entry][0]))

    return boxes, texts, opts


"""Make another level of dict for entries with parent"""


def parseUpdate(update):
    parsedDict = {}
    for key, value in update.items():
        if key in ["Project", "updatedProject", "selected_preset", "json_review", "update_button"]:
            continue
        if isinstance(value, str) and value == 'on':  # TODO: this is hard-coded
            value = True
        parentChild = key.split('$')  # TODO: this is hard-coded
        if len(parentChild) == 2:
            if parsedDict.get(parentChild[0]) and isinstance(parsedDict[parentChild[0]], dict):
                parsedDict[parentChild[0]].update({parentChild[1]: value})
            else:
                parsedDict[parentChild[0]] = {parentChild[1]: value}
        elif len(parentChild) == 1:
            parsedDict[parentChild[0]] = value
        else:
            print("Broken parentChild key")
    return parsedDict


"""Small utility to translate form data into proper dict flags"""


def parse_override(value):
    if value == '':
        return None
    elif value == 'on':
        return True
    elif value in (True, False):
        return value
    elif value.isnumeric():
        return int(value)
    elif value[0].isdigit():
        return float(value)
    else:
        return value


"""Subroutine to update a dict for inserting into main config"""


def update_project(to_update, overrides, master_overrides=None):
    """
    Update a nested dictionary or similar mapping.
    reference gets a special treatment. What is annoying is that for pipelines, values may be
    either Boolean or dict in this implementation. Hence more checks, not sure if this can be
    more compact.
    """
    if not master_overrides:
        master_overrides = overrides
    toReturn = copy.deepcopy(to_update)
    for key, value in to_update.items():
        """If we have a dict for an entry, recurse inside"""
        if key in overrides.keys():
            if key == 'reference_for_species':
                toReturn[key] = {}
                toReturn[key][overrides[key].upper()] = [overrides['reference_assembly']]
            elif isinstance(value, dict):
                if key in master_overrides.keys():
                    if isinstance(master_overrides[key], dict):
                        toReturn[key] = update_project(value, master_overrides[key], master_overrides)
                    else:
                        toReturn[key] = update_project(value, master_overrides, master_overrides)
                else:
                    continue
            else:
                toReturn[key] = parse_override(overrides[key])
        else:
            if isinstance(toReturn[key], dict):
                toReturn[key] = None
            else:
                toReturn[key] = False
    return toReturn



'''Index generation, the landing page to start an editing session'''


@app.route("/")
def index():
    global project_list
    global preset_list
    global config
    project = project_list[0]['id']
    """We need to pass only the enabled pipelines, js script will put the checkmarks accordingly"""
    json_snippet = config["values"][project]
    enabled_workflows = obtain_enabled(json_snippet)
    json_text = json.dumps(json_snippet, sort_keys=True, indent=2)
    return render_template('base.html', project_list=project_list,
                           preset_list=preset_list,
                           selected_project=project,
                           json_snippet=json_text,
                           checkbox_list=enabled_workflows[0],
                           texts_list=enabled_workflows[1],
                           opts_list=enabled_workflows[2])


'''Upon selection of a project or preset update the values in the form'''


@app.route('/select', methods=['POST'])
def select():
    global project_list
    global preset_list
    global config
    global defaults

    if request.method == 'POST':
        project = request.form.get("selected_project")  # parse project
        preset = request.form.get("selected_preset")  # parse preset
        updated_project = request.form.get("updated_project")
        messages = []

        '''Prepare the data for rendering:'''
        if preset and project == updated_project:
            preset_snippet = presets["presets"][preset]
            json_snippet = config["values"][project]
            json_snippet.update(preset_snippet)
            config["values"][project].update(json_snippet)
            messages.append(dict(title="Warning", body="Preset " + preset + " was applied to project " + project))
        json_snippet = config["values"][project]
        enabled_workflows = obtain_enabled(json_snippet)
        json_text = json.dumps(json_snippet, sort_keys=True, indent=2)

        return render_template('base.html', project_list=project_list,
                               preset_list=preset_list,
                               selected_project=project,
                               selected_preset=preset,
                               json_snippet=json_text,
                               messages=messages,
                               checkbox_list=enabled_workflows[0],
                               texts_list=enabled_workflows[1],
                               opts_list=enabled_workflows[2])


'''Clone a project'''


@app.route("/clone", methods=["POST"])
def clone():
    global project_list
    global preset_list
    global config

    project = request.form.get("project")
    cln = request.form.get("clone")
    if cln:
        config["values"][cln] = copy.deepcopy(config["values"][project])
        '''Order projects alphabetically'''
        od = {k: v for k, v in sorted(config["values"].items())}
        config["values"] = copy.deepcopy(od)
        refresh()
        messages = [dict(title="Warning", body="Project " + project + " cloned into " + cln)]
    else:
        messages = [dict(title="Warning", body="You need to specify a name of the project to clone to")]
    print(messages[0]['body'])
    json_snippet = config["values"][cln] if cln else config["values"][project_list[0]['id']]
    enabled_workflows = obtain_enabled(json_snippet)
    json_text = json.dumps(json_snippet, sort_keys=True, indent=2)

    return render_template('base.html',
                           project_list=project_list,
                           preset_list=preset_list,
                           selected_project=cln,
                           json_snippet=json_text,
                           messages=messages,
                           checkbox_list=enabled_workflows[0],
                           texts_list=enabled_workflows[1],
                           opts_list=enabled_workflows[2])


'''Update a project'''


@app.route("/update/<string:project>", methods=["POST"])
def update(project):
    global project_list
    global preset_list
    global config
    global config_path

    messages = []
    '''Handle clicks on various update buttons'''
    if request.form['update_button'] == "clone":
        messages = [dict(title="", body="Project " + project + "Is being cloned")]
        return render_template('clone.html', selected_project=project, messages=messages)
    elif request.form['update_button'] == "reset":
        del project_list[:]
        del config
        print("Configuration was restored...")
        messages = [dict(title="Warning", body="Configuration was restored from disk")]
        init()
    elif request.form['update_button'] == "write":
        print("Saving changes...")
        with open(config_path, "w") as f:
            json.dump(config, f, sort_keys=True, indent=2)
        messages = [dict(title="Warning", body="Changes were written to disk, review and prepare a Pull Request")]
    elif request.form['update_button'] == "delete":
        del config["values"][project]
        refresh()
        messages = [dict(title="Warning", body="Project " + project + " was Deleted...")]
        print(messages[0]['body'])
        project = project_list[0]['id']
    elif request.form.get('update_button') and request.form['update_button'] == "record":
        form_data = request.form
        form_dict = form_data.to_dict(flat=True)
        updated_config = update_project(defaults, parseUpdate(form_dict))
        preset_list = []
        """
        Debug messages, uncomment if needed
        
        print("Updated JSON:")
        myJSON = json.dumps(updatedConfig, indent=4)
        print(myJSON) 
        
        Main Updating step below:
       
        """
        config["values"][project].update(updated_config)
        messages.append(dict(title="Warning", body="Changes NOT dumped to disk but retained in memory"))
    else:
        print("I received some unknown request")
    json_snippet = config["values"][project]
    enabled_workflows = obtain_enabled(json_snippet)
    json_text = json.dumps(json_snippet, sort_keys=True, indent=2)
    return render_template('base.html',
                           project_list=project_list,
                           preset_list=preset_list,
                           selected_project=project,
                           json_snippet=json_text,
                           messages=messages,
                           checkbox_list=enabled_workflows[0],
                           texts_list=enabled_workflows[1],
                           opts_list=enabled_workflows[2])


''' The App starts here, check if have project_list and if NOT, initialize the app'''
if not project_list or len(project_list) == 0:
    init()

if __name__ == "__main__":
    app.run(debug=True)
