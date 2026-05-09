"""
   Script based on gsiOlive code. Scan olives and return the information as a hash
   keyed by instance, i.e. scanned = {'research': ['o1', 'o2', 'o3'], 'clinical': ['o4', 'o5', 'o6']}
"""

import glob
import os
import re
import subprocess
from os.path import basename

'''Main function to call from outside'''
def scan_olives(olive_dir: str, instances: list, blacklist: list):
    olives = {}
    for inst in instances:
        olive_list = collect_olives(olive_dir, inst, blacklist, [])
        olives[inst] = parse_olives(olive_list)
    return olives

"""
   Find olives, return dict with lists of files
"""
def collect_olives(repo_dir: str, instance: str, blacklist: list, aliases: dict) -> list:
    olive_list = []
    if repo_dir and os.path.isdir(repo_dir):
        subdir = "/".join([repo_dir, instance])
        olive_files = glob.glob("/".join([subdir, "vidarr*.shesmu"]))
        if len(olive_files) == 0 and instance in aliases.keys():
            subdir = "/".join([repo_dir, "shesmu", aliases[instance]])
            olive_files = glob.glob("/".join([subdir, "vidarr*.shesmu"]))
        print(f'INFO: We have {len(olive_files)} .shesmu files for {instance}')
        if len(olive_files) > 0:
            olive_list = []
        for oli in olive_files:
            if len(blacklist) == 0 or basename(oli) not in blacklist:
                olive_list.append(oli)
    return olive_list

"""
   Parse Olive: return a dict with tags (versions of workflow)
   { olive_name: [tags] }
"""
def parse_olives(olive_files: list) -> dict:
    """ Return a list of Olive data structure(s) """
    parsed_olives = {}
    ''' extract versions of the Workflow, names and modules'''
    for m_olive in olive_files:
        vetted_tags = []
        vetted_names = []
        try:
            run_lines = subprocess.check_output(f"grep 'Run ' '{m_olive}'", shell=True).decode().strip()
            run_lines = run_lines.split("\n")
            if not isinstance(run_lines, list):
                run_lines = [run_lines]
        except subprocess.CalledProcessError:
            print(f'WARNING: No Run lines in the Olive {m_olive}')
            run_lines = []

        for rl in run_lines:
            next_tag = re.search(r"v(\d+_\d+_*\d*\w*)$", rl)
            next_name = re.search(r"(\S+)_v\d+_\d+_*\d*\w*$", rl)
            if next_tag is not None:
                vetted_tags.append(next_tag.group(1).replace("_", "."))
            if next_name is not None:
                vetted_names.append(next_name.group(1))

        for name in vetted_names:
            if name in parsed_olives.keys():
                parsed_olives[name] = list(set(parsed_olives[name] + vetted_tags))
            else:
                parsed_olives[name] = list(set(vetted_tags))
    return parsed_olives
