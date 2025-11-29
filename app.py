"""
   This is the main code with Flask routes. It reads the config, scans the olives and produces interface
   ready to process requests
"""

from __future__ import absolute_import
import copy
import json
import os
import re
import sys
from copy import deepcopy

from flask import Flask, render_template, request, current_app
from internal import supported_types
from internal import update_ui
from services.olivescan_ops import scan_olives
from services.config_ops import get_config
from services.session_state import state, SessionState


def create_app(debug=True):
    app = Flask(__name__)
    '''We can store configuration elements in the app.config'''
    app.config.update(get_config(os.environ['UICONFIG_SETTINGS']))
    app.config["SUPPORTED_TYPES"] = ["json", "yaml", "toml"]
    app.config["MAIN_CONFIG"] = {"version": 1, "enabled": True}

    with app.app_context():
        app.config["SCAN_CACHE"] = scan_olives(current_app.config["data"]["local_olive_dir"],
                                               current_app.config["data"]["instances"],
                                               current_app.config["data"].get("blacklist", []))
        return app


""" For state: Load configuration file assay_info.jsonconfig using setting of the current app"""
def load_config() -> dict:
    assay_config = {}
    config_path = get_config(os.environ['UICONFIG_SETTINGS'])["data"]["assay_config_file"]
    with open(os.path.join(os.path.dirname(sys.argv[0]), config_path), 'r') as f:
        assay_config = json.load(f)
    return assay_config


""" For state: Load presets TODO: update them here if config changed"""
def load_presets() -> dict:
    preset_config = {}
    preset_path = get_config(os.environ['UICONFIG_SETTINGS'])["data"]["preset_path"]
    with open(os.path.join(os.path.dirname(sys.argv[0]), preset_path), 'r') as f:
        preset_config = json.load(f)
    return preset_config


my_app = create_app()
state.config = load_config()
state.preset_list = load_presets()

"""Pretty print json with arrays in single line"""
def pretty_json(json_text: str) -> str:
    jstring = re.sub(r'(\[)\n', r'\1', json_text)
    jstring = re.sub(r'(\d\")\s+', r'\1', jstring)
    jstring = re.sub(r'(\d\",)\s+', r'\1', jstring)
    jstring = re.sub(r'(\[)\s+', r'\1', jstring)
    jstring = re.sub(r'(\d\",)\n', r'\1', jstring)
    return jstring

"""ensure keys exist when making items in a nested dict"""
def ensure(d, *keys):
    for k in keys:
        d = d.setdefault(k, {})
    return d

"""Check what we have enabled for a given project and return as a dict"""
def obtain_enabled(project_json: dict) -> list:
    boxes = []
    for entry in project_json.keys():
        if isinstance(project_json[entry], list):
            boxes.append(dict(id=entry, status=True))
    return boxes


"""
   this will take a staging version of config, sort and prettify it for printing
"""
def save_config(conf_data: dict, output_file: str):
    try:
        vetted_od = SessionState.deepsort_dict(conf_data)
        with open(output_file, "w") as wfj:
            jstring = json.dumps(vetted_od, indent=2, ensure_ascii=False)
            jstring = re.sub(r'(\[)\n', r'\1', jstring)
            jstring = re.sub(r'(\d\")\s+', r'\1', jstring)
            jstring = re.sub(r'(\.\d\",)\s+', r'\1', jstring)
            jstring = re.sub(r'(\[)\s+', r'\1', jstring)
            jstring = re.sub(r'(\d\",)\n', r'\1', jstring)
            '''Take care of strings with reference'''
            pattern_string = supported_types.REF_KEY + r"\S+\s+\S+\d\","
            ptr = re.compile(f'({pattern_string})')
            jstring = re.sub(ptr, r'\1' + "\n", jstring)
            wfj.write(jstring)
            print(f"INFO: Saved staged assay configuration into a file {output_file}")
    except:
        print(f"ERROR: writing to a config file {output_file} failed")


""" 
    We need to stitch together workflows, and reference from from fresh scan together
    and return a dict for a given assay (we have reference on assay level, so we return all versions
    and the reference for an assay although only one version is being updated
"""
def parse_update(update_object, assay_config: dict, available_olives: list, version: str) -> dict:
    parsed_dict = deepcopy(assay_config)
    enabled_workflows = []
    for key, value in update_object.items():
        if key in available_olives and isinstance(value, str) and value == 'on':
            enabled_workflows.append(key)
        elif key == supported_types.REF_KEY and value != assay_config.get(supported_types.REF_KEY, "Not Set"):
            parsed_dict[supported_types.REF_KEY] = value
    for wf in enabled_workflows:
        if wf not in assay_config['versions'][version]['workflows'].keys():
            parsed_dict['versions'][version]['workflows'][wf] = []
    for wf in assay_config['versions'][version]['workflows'].keys():
        if wf not in enabled_workflows:
            del (parsed_dict['versions'][version]['workflows'][wf])
    return parsed_dict


""" 
     Index generation, the landing page to start an editing session 
"""
@my_app.route("/")
def index():
    """Synchronize the configuration with olive versions to make sure we have all versions"""
    state.config['values'] = state.get_updated_assays(state.config['values'],
                                                      current_app.config.get("SCAN_CACHE", {}),
                                                      current_app.config.get("prefixes", {}), None)
    assay = state.get_assays()[0]['id']
    version = next(iter(state.config['values'][assay]['versions']))
    """vetted_workflows are instance-specific and retrieved from a fresh scan of deployed olives"""
    vetted_workflows = state.get_filtered_wf_list(assay,
                                                  current_app.config.get("SCAN_CACHE", {}),
                                                  current_app.config.get("prefixes", {}))
    reference = state.config['values'][assay].get("reference", "Not Set")
    """We need to pass only the enabled workflows, js script will put the checkmarks accordingly"""
    json_snippet = state.config['values'][assay]['versions'][version]['workflows']

    enabled_workflows = obtain_enabled(json_snippet)
    json_text = json.dumps(json_snippet, sort_keys=True, indent=2)
    ui_renderer = update_ui.updateUi(vetted_workflows, reference)
    return render_template('base.html',
                           project_list=state.get_assays(),
                           preset_list=list(state.get_presets()['presets'].keys()),
                           selected_project=assay,
                           selected_version=version,
                           nested_list=ui_renderer.get_ui(),
                           json_snippet=pretty_json(json_text),
                           checkbox_list=enabled_workflows,
                           texts_list=[{'id': "reference", 'value': reference}])


""" Upon selection of a project or preset update the values in the form """
@my_app.route('/select', methods=['POST'])
def select():
    if request.method == 'POST':
        assay = request.form.get('selected_project')  # parse project
        version = request.form.get('selected_version')  # parse version
        preset = request.form.get('selected_preset')  # parse preset
        updated_assay = request.form.get('updated_project')
        updated_version = request.form.get('updated_version')
        messages = []

        """ Prepare the data for rendering: """
        if version not in state.config['values'][assay]['versions'].keys():
            version = next(iter(state.config['values'][assay]['versions']))
        json_snippet = state.config['values'][assay]['versions'][version]['workflows']
        if preset and assay == updated_assay:
            preset_snippet = state.get_presets()['presets'][preset]
            json_snippet = {k: v for k, v in json_snippet.items() if k in preset_snippet.keys()}
            json_snippet.update({k: v for k, v in preset_snippet.items() if k not in json_snippet})
            updated_snippet = state.get_updated_assays({assay: {'versions': {version: {'workflows': json_snippet}}}},
                                                       current_app.config.get("SCAN_CACHE", {}),
                                                       current_app.config.get("prefixes", {}), assay)
            json_snippet = updated_snippet['versions'][version]['workflows']
            messages.append(dict(title="Warning",
                                 body="Preset " + preset + " applied to project " + assay + " v." + updated_version))
        reference = state.config['values'][assay].get("reference", "Not Set")
        enabled_workflows = obtain_enabled(json_snippet)
        """vetted_workflows are instance-specific and retrieved from a fresh scan of deployed olives"""
        vetted_workflows = state.get_filtered_wf_list(assay,
                                                      current_app.config.get("SCAN_CACHE", {}),
                                                      current_app.config.get("prefixes", {}))
        json_text = json.dumps(json_snippet, sort_keys=True, indent=2)
        ui_renderer = update_ui.updateUi(vetted_workflows, reference)
        return render_template('base.html',
                               project_list=state.get_assays(),
                               preset_list=list(state.get_presets()['presets'].keys()),
                               selected_project=assay,
                               selected_version=version,
                               selected_preset=preset,
                               nested_list=ui_renderer.get_ui(),
                               json_snippet=pretty_json(json_text),
                               messages=messages,
                               checkbox_list=enabled_workflows,
                               texts_list=[{'id': "reference", 'value': reference}])
    return None


""" Clone a project """
@my_app.route("/clone", methods=["POST"])
def clone():
    # TODO: Check that we are not cloning into existing entry
    assay = request.form.get("source_assay")
    version = request.form.get("source_version")
    cln = request.form.get("clone_assay")
    vrs = request.form.get("clone_version")

    if cln:
        if cln not in state.config['values'].keys() or vrs not in  state.config['values'][cln]['versions'].keys():
            ensure(state.config['values'], cln, "versions")[vrs] = {}
        state.config['values'][cln][supported_types.REF_KEY] = \
            state.config['values'][assay].get(supported_types.REF_KEY, "Not Set")
        state.config['values'][cln]['versions'][vrs].update(state.config['values'][assay]['versions'][version])
        """ Order assays alphabetically """
        od = {k: v for k, v in sorted(state.config['values'].items())}
        state.config['values'] = copy.deepcopy(od)
        messages = [dict(title="Warning", body="Assay " + assay + " cloned into " + cln + " v." + vrs)]
    else:
        messages = [dict(title="Warning", body="You need to specify a name of the assay to clone to")]
    print(messages[0]['body'])
    """vetted_workflows are instance-specific and retrieved from a fresh scan of deployed olives"""
    vetted_workflows = state.get_filtered_wf_list(assay,
                                                  current_app.config.get("SCAN_CACHE", {}),
                                                  current_app.config.get("prefixes", {}))
    reference = state.config['values'][assay].get("reference", "Not Set")
    json_snippet = state.config['values'][cln]['versions'][vrs]['workflows'] \
        if cln \
        else state.config['values'][assay]['versions'][version]['workflows']
    enabled_workflows = obtain_enabled(json_snippet)
    json_text = json.dumps(json_snippet, sort_keys=True, indent=2)
    ui_renderer = update_ui.updateUi(vetted_workflows, reference)
    return render_template('base.html',
                           project_list=state.get_assays(),
                           preset_list=list(state.preset_list['presets'].keys()),
                           selected_project=cln,
                           selected_version=vrs,
                           nested_list=ui_renderer.get_ui(),
                           json_snippet=pretty_json(json_text),
                           messages=messages,
                           checkbox_list=enabled_workflows,
                           texts_list=[{'id': "reference", 'value': reference}])


""" Update a project """
@my_app.route("/update/<path:assay>/<string:version>", methods=["POST"])
def update(assay, version):
    messages = []
    """ Handle clicks on various update buttons """
    if request.form['update_button'] == "clone":
        messages = [dict(title="",
                         body="Assay version " + version + " of Assay " + assay + "Is being cloned")]
        return render_template('clone.html',
                               selected_project=assay,
                               selected_version=version,
                               messages=messages)
    elif request.form['update_button'] == "reset":
        state.config = load_config()
        state.preset_list = load_presets()
        print("Configuration was restored...")
        messages = [dict(title="Warning",
                         body="Configuration was restored from disk")]
        assay = state.get_assays()[0]['id']
        version = next(iter(state.get_assays()[0]['versions']))
    elif request.form['update_button'] == "write":
        print("Saving changes...")
        message_title = "Warning"
        message_body = "Changes were written to disk, review and prepare a Pull Request"
        if "assay_stage_file" in current_app.config["data"].keys():
            save_config(state.get_config(), current_app.config["data"]["assay_stage_file"])
        else:
            message_title = "Error"
            message_body = "Could not write to the staging config file"
        messages = [dict(title=message_title, body=message_body)]
    elif request.form['update_button'] == "delete":
        if len(state.config['values'][assay]['versions']) > 1:
            del state.config['values'][assay]['versions'][version]
        else:
            del state.config['values'][assay]
        messages = [dict(title="Warning",
                         body="Version " + version + " of Assay " + assay + " was Deleted...")]
        print(messages[0]['body'])
        assay = state.get_assays()[0]['id']
        version = next(iter(state.get_assays()[0]['versions']))
    elif request.form.get('update_button') and request.form['update_button'] == "record":
        form_data = request.form
        form_dict = form_data.to_dict(flat=True)
        workflows_per_instance = list(list(v.keys()) for v in current_app.config.get("SCAN_CACHE", {}).values())
        available_workflows = list(set([item for sublist in workflows_per_instance for item in sublist]))
        parsed_update = parse_update(form_dict,
                                     state.get_config()['values'][assay],
                                     available_workflows,
                                     version)
        state.config['values'][assay] = parsed_update
        state.config['values'][assay] = state.get_updated_assays(state.config['values'],
                                                                 current_app.config.get("SCAN_CACHE", {}),
                                                                 current_app.config.get("prefixes", {}), assay)
        messages.append(dict(title="Warning",
                             body="Changes NOT dumped to disk but retained in memory"))
    else:
        print("I received some unknown request")
    vetted_workflows = state.get_filtered_wf_list(assay,
                                                  current_app.config.get("SCAN_CACHE", {}),
                                                  current_app.config.get("prefixes", {}))
    reference = state.config['values'][assay].get("reference", "Not Set")
    json_snippet = state.config['values'][assay]['versions'][version]['workflows']
    enabled_workflows = obtain_enabled(json_snippet)
    json_text = json.dumps(json_snippet, sort_keys=True, indent=2)
    ui_renderer = update_ui.updateUi(vetted_workflows, reference)
    return render_template('base.html',
                           project_list=state.get_assays(),
                           preset_list=list(state.preset_list['presets'].keys()),
                           selected_project=assay,
                           selected_version=version,
                           nested_list=ui_renderer.get_ui(),
                           json_snippet=pretty_json(json_text),
                           messages=messages,
                           checkbox_list=enabled_workflows,
                           texts_list=[{'id': "reference", 'value': reference}])


""" The App starts here """
if __name__ == "__main__":
    my_app.run(debug=True)
