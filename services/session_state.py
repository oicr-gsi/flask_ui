"""
   This is a class for holding our staging configuration. It should be populated with olive versions
   just before writing to the disk

   config - our current assay_info copy, mutable and updatable
   assay_list - generated each time, synchronized with config
   preset_list - we store it though it should not be modified from flask UI
"""
import re
from collections import OrderedDict
from copy import deepcopy
from functools import reduce

class SessionState:
    def __init__(self):
        self.config = None
        self.assay_list = None
        self.preset_list = None

    '''This takes in account all changes to the config'''
    def get_assays(self) -> list:
        assay_list = []
        for a in self.config['values'].keys():
            assay_list.append({"id": a,
                               "title": a,
                               "versions": list(self.config['values'][a]['versions'].keys())})
        return assay_list

    @staticmethod
    def config_to_overview(data: dict) -> dict:
        assay_overview = {}
        try:
            for a in data['values'].keys():
                for v in data['values'][a]['versions'].keys():
                    for wf, wf_versions in data['values'][a]['versions'][v]['workflows'].items():
                        if wf not in assay_overview.keys():
                            assay_overview[wf] = {}
                        assay_key = a + ":" + v
                        if isinstance(wf_versions, list) and len(wf_versions) > 0:
                            assay_overview[wf][assay_key] = wf_versions
        except KeyError:
            print("ERROR: failed to parse configuration for overview generation")
        return assay_overview

    '''This builds a data structure for rendering an overview table of assays'''
    def get_assay_overview(self) -> dict:
        return SessionState.config_to_overview(self.config)

    def get_config(self):
        return self.config

    def get_presets(self):
        if self.preset_list is not None:
            if isinstance(self.preset_list, dict) and 'presets' in self.preset_list.keys():
                return self.preset_list
        return {'presets': {}}

    """Utility function for flattening arrays and other nested data structures"""
    @staticmethod
    def flat2gen(alist: list):
        for item in alist:
            if isinstance(item, list):
                for subitem in item:
                    yield subitem
            else:
                yield item

    @staticmethod
    def deepsort_dict(input_dict, key=lambda item: item[0]) -> dict:
        """
        Recursively sorts an OrderedDict and its nested OrderedDicts.
        Args:
            input_dict (OrderedDict or dict): The dictionary to sort.
            key (function): A function to extract a comparison key from each item.
                            Defaults to sorting by key (item[0]).
        Returns:
            OrderedDict: A new OrderedDict with deeply sorted contents.
        """
        if not isinstance(input_dict, (OrderedDict, dict)):
            return input_dict  # Not a dictionary, return as is
        sorted_items = []
        for k, v in sorted(input_dict.items(), key=key):
            if isinstance(v, (OrderedDict, dict)):
                sorted_items.append((k, SessionState.deepsort_dict(v, key)))
            else:
                sorted_items.append((k, v))
        return OrderedDict(sorted_items)

    """
       Perform a prefix check on assay, we are routing the selections of workflows (which can be instance-specific)
       depending on prefixes in assay names
    """
    @staticmethod
    def is_instance_specific(assay: str, filters: dict, instance: str):
        try:
            prefixes = [filters[instance]] if isinstance(filters[instance], str) else filters[instance]
            for p in prefixes:
                if re.match(p, assay):
                    return True
            return False
        except KeyError:
            return False

    """
        We need a vetted list of workflows, instance-specific. This is good only if the following is true:
        * we do not have any filters
        * OR we have N of filters = (N of instances) - 1
        * OR we have N of filters == N of instances
    """
    def get_filtered_wf_list(self, assay: str, olive_hash: dict, filters: dict):
        if len(filters) > 0:
            for inst in filters.keys():
                if self.is_instance_specific(assay, filters, inst) and inst in olive_hash.keys():
                    workflows = list(olive_hash[inst].keys())
                    return sorted(workflows)
            for inst in olive_hash.keys():
                if inst not in filters.keys():
                    workflows = list(olive_hash[inst].keys())
                    return sorted(workflows)
        else:
            return list(set(olive_hash.values()))

    """
       We can also produce a fully-fledged 'values' part of the config with versions of the workflows synchronized
       with a fresh olive scan (all new tags will be added automatically, later followed by manual approval)
       Optionally pass assay argument so that we synch only one assay when a workflow gets enabled in UI
       if we do not have any filters we update everything from a combined bucket of olives/versions
    """
    def get_updated_assays(self, config: dict, olive_hash: dict, filters: dict, req_assay: None):
        updated = deepcopy(config)

        def merge_workflows(existing, extra):
            combined = reduce(lambda a, b: a + b, [existing, extra])
            unique = set(combined)
            return sorted(unique, key=lambda v: tuple(map(int, v.split('.'))))

        def find_instance_for_assay(assay):
            """Return the instance string that matches a specific assay."""
            return next(
                (inst for inst in filters
                 if inst in olive_hash and self.is_instance_specific(assay, filters, inst)),
                None
            )

        def update_assay_for_instance(assay, inst):
            """Apply workflow updates to the given assay & instance."""
            for ver in config[assay]["versions"].keys():
                ver_data = config[assay]["versions"][ver]
                for wf, existing_wf in ver_data["workflows"].items():
                    extra = olive_hash[inst].get(wf, [])
                    updated[assay]["versions"][ver]["workflows"][wf] = merge_workflows(existing_wf, extra)
                    '''Delete entries with empty version list'''
                    if len(updated[assay]["versions"][ver]["workflows"][wf]) == 0:
                        del updated[assay]["versions"][ver]["workflows"][wf]

        instance_for_assay = {assay: find_instance_for_assay(assay) for assay in config}
        updated_assays = {assay for assay, inst in instance_for_assay.items() if inst is not None}

        '''First: update assays matched by filters'''
        for assay, inst in instance_for_assay.items():
            if inst is not None:
                update_assay_for_instance(assay, inst)

        '''Second: update assays NOT matched by filters, using any olive_hash instance not in filters.'''
        for inst in olive_hash:
            if inst in filters:
                continue

            for assay in config:
                if assay not in updated_assays:
                    update_assay_for_instance(assay, inst)

        '''Optional return: specific assay only (all versions available)'''
        if req_assay is not None:
            return updated[req_assay]

        return updated


state = SessionState()
