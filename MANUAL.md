## Manual for Flask UI app

In this document we will cover the general workflow and some topics which may not be too obvious.
Working with configuration file **asay_info.jsonconfig** may include such things as adding assays or
adding assay versions, also making changes to the configurations of existing assays. All of this
changes are better be done incrementally and isolated to one assay only, sweeping changes like
removing a workflow from configuration may be done in a text editor (i.e. vim)


### Purpose of this app

Flask UI is meant to be a light-weight application for enabling and disabling workflows in the
assay-based configuration file (assay_info.jsonconfig). It has the following features:
- automatic version updates (see below)
- ability to isolate configurations to specific instances (using prefixes in assay names)
- creation of a draft configuration file with staged changes
- changes preview in UI
- Overview of the existing configuration (the existing configuration)

### Installation and Configuring

See README.md file for instructions on launching flask UI. In this section we review the elements
of the .toml configuration file which app uses to find various bits of data it needs.

#### data section

Here we have a collection of parameters helping flask UI to find such items as
- local_olive_dir: directory where the instance-specific sub-directories
- assay_config_file: path to your local copy of assay_info.jsonconfig
- assay_stage_file: path to the staged configuration file, can be set to point to assay_info.jsonconfig too
- preset_path: we use presets, this is the path to your assay_presets.conf
- instances: instances we scan ("research", "production-cap")
- blacklist: here we can put names of olive files to exclude from scanning

#### prefixes section

In this section we can list prefixes to identify instance-specific assays. This may change in a future, but
at this point we use regex to identify assays which are supposed to use instance-specific olives 

### Creating new assay

Creating new assay is normally done with Clone button. Pressing the button will bring up a page where we set name
and version of a new assay based on the existing assay we are cloning. This is also used to create new versions of existing 
assays. It is very often that the next version of assay is only slightly different, so cloning is a very
natural way to bump up a version.

### Configuring workflows

Enabling or disabling workflows for an assay is very straightforward and only requires checking or un-checking boxes
in the UI. At the moment, we also control what reference an assay is using but in most of the cases this will be
human genome reference such as hg38. Also note, that the menu of select-able workflows is generated after the app scans
the instance-specific directories with olive files. Therefore, selection menu depends on the settings in prefixes section.
If it is empty, flask UI will use all available olives for configuring an assay. However, we are currently using 
assays which are supposed to be isolated to a specific instance. The defaults for prefixes section in the provided
sample .toml file need to be used.

### Changes are not recorded automatically

Pay attention to the flow of your session. Changes to assay configurations are not recorded automatically and if a user
navigates away from the currently selected assay, all changes will be lost. To confirm changes, please use Record button.
Pressing Record button will tell flask UI to keep the changes in memory. When you happy with all the changes that were made,
press Write to Disk button so save your changes into a file (this will go into the file specified as assay_stage_file in your
.toml configuration).

### Workflow versions

Workflow versions will be updated automatically for the latest version of each assay (which we recognize as the active version).
Older versions of the same assay are expected to be superseded by the latest version, but we track all previously ran versions of
workflows. One of the functions of the assay_info.jsonconfig is to keep records of these past settings. Automatic updates happen 
when olive files receive updates and some workflows get their versions incremented. These changes are going into the latest version
of an assay, as mentioned above. Having a staging configuration file allows reviewing of all changes by comparing staged file with
changes to the original assay_info.jsonconfig

