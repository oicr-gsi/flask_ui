#!/bin/bash

#
# Activate virtual environment and export variables for FLASK
# This is for launching the app locally !!!

# type 'flask run' in project's dir to serve the app on localhost

export FLASK_APP=config_ui.py
export FLASK_ENV=development
export UICONFIG_SETTINGS="$HOME/secrets/ui_config.cfg"
source venv/bin/activate

