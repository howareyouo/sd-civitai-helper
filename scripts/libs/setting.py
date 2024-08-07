# -*- coding: UTF-8 -*-
# collecting settings to here
import json
import os
import modules.scripts as scripts
from . import util

name = "setting.json"
path = os.path.join(scripts.basedir(), name)

data = {
    "max_size_preview": True,
    "skip_nsfw_preview": False,
    "open_url_with_js": False,
}

# save setting
# return output msg for log
def save():
    print("Saving setting to: " + path)

    json_data = json.dumps(data, indent=4)
    output = ""
    try:
        # write to file
        with open(path, 'w') as f:
            f.write(json_data)
    except Exception as e:
        util.printD("Error when writing file:" + path)
        output = str(e)
        util.printD(str(e))
        return output

    output = "Setting saved to: " + path
    util.printD(output)

    return output


# load setting to global data
def load():
    # load data into globel data
    global data

    if not os.path.isfile(path):
        util.printD("No setting file, use default")
        return

    json_data = None
    with open(path, 'r') as f:
        json_data = json.load(f)

    # check error
    if not json_data:
        util.printD("load setting file failed")
        return

    data = json_data


# save setting from parameter
def save_from_input(max_size_preview, skip_nsfw_preview, open_url_with_js):
    global data
    data = {
        "max_size_preview": max_size_preview,
        "skip_nsfw_preview": skip_nsfw_preview,
        "open_url_with_js": open_url_with_js,
    }
    return save()
