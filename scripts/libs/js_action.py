# -*- coding: UTF-8 -*-
# handle msg between js and python side
import os
import json
import webbrowser
import subprocess
from . import util
from . import model
from . import civitai
from . import model_action
from . import msg_handler
from . import downloader
from . import setting

# get civitai's model url and open it in browser
# parameter: model_type, search_term
# output: python msg - will be sent to hidden textbox then picked by js side
def open_model_url(model_type, search_term, open_url_with_js=False):
    model_info = civitai.load_model_info_by_search_term(model_type, search_term)
    if not model_info:
        util.printD(f"Failed to get model info for {model_type} {search_term}")
        return ""

    if "modelId" not in model_info.keys():
        util.printD(f"Failed to get model id from info file for {model_type} {search_term}")
        return ""

    model_id = model_info["modelId"]
    if not model_id:
        util.printD(f"model id from info file of {model_type} {search_term} is None")
        return ""

    model_version_id = model_info["id"]
    url = civitai.url_dict["modelPage"] + str(model_id) + "?modelVersionId=" + str(model_version_id)
    
    open_url_with_js = setting.data["open_url_with_js"]
    if not open_url_with_js:
        util.printD("Open model url: " + url)
        # open url
        webbrowser.open_new_tab(url)

    return msg_handler.build_py_msg("open_model_url", {"url": url, "open_url_with_js": open_url_with_js})


# add trigger words to prompt
# parameter: model_type, search_term, prompt
# return: [new_prompt, new_prompt] - new prompt with trigger words, return twice for txt2img and img2img
def add_trigger_words(model_type, search_term, prompt):
    model_info = civitai.load_model_info_by_search_term(model_type, search_term)
    if not model_info:
        util.printD(f"Failed to get model info for {model_type} {search_term}")
        return [prompt, prompt]

    if "trainedWords" not in model_info.keys():
        util.printD(f"Failed to get trainedWords from info file for {model_type} {search_term}")
        return [prompt, prompt]

    trainedWords = model_info["trainedWords"]
    if not trainedWords:
        util.printD(f"No trainedWords from info file for {model_type} {search_term}")
        return [prompt, prompt]

    if len(trainedWords) == 0:
        util.printD(f"trainedWords from info file for {model_type} {search_term} is empty")
        return [prompt, prompt]

    # get ful trigger words
    trigger_words = ""
    for word in trainedWords:
        trigger_words = trigger_words + word + ", "

    new_prompt = prompt + " " + trigger_words

    # add to prompt
    return [new_prompt, new_prompt]


# use preview image's prompt as prompt
# parameter: model_type, model_name, prompt, neg_prompt
# return: [new_prompt, new_neg_prompt, new_prompt, new_neg_prompt,] - return twice for txt2img and img2img
def use_preview_prompt(model_type, search_term, prompt, neg_prompt):
    model_info = civitai.load_model_info_by_search_term(model_type, search_term)
    if not model_info:
        util.printD(f"Failed to get model info for {model_type} {search_term}")
        return [prompt, neg_prompt, prompt, neg_prompt]

    if "images" not in model_info.keys():
        util.printD(f"Failed to get images from info file for {model_type} {search_term}")
        return [prompt, neg_prompt, prompt, neg_prompt]

    images = model_info["images"]
    if not images:
        util.printD(f"No images from info file for {model_type} {search_term}")
        return [prompt, neg_prompt, prompt, neg_prompt]

    if len(images) == 0:
        util.printD(f"images from info file for {model_type} {search_term} is empty")
        return [prompt, neg_prompt, prompt, neg_prompt]

    # get prompt from preview images' meta data
    preview_prompt = ""
    preview_neg_prompt = ""
    for img in images:
        if "meta" in img.keys():
            if img["meta"]:
                if "prompt" in img["meta"].keys():
                    if img["meta"]["prompt"]:
                        preview_prompt = img["meta"]["prompt"]

                if "negativePrompt" in img["meta"].keys():
                    if img["meta"]["negativePrompt"]:
                        preview_neg_prompt = img["meta"]["negativePrompt"]

                # we only need 1 prompt
                if preview_prompt:
                    break

    if not preview_prompt:
        util.printD(f"There is no prompt of {model_type} {search_term} in its preview image")
        return [prompt, neg_prompt, prompt, neg_prompt]

    return [preview_prompt, preview_neg_prompt, preview_prompt, preview_neg_prompt]


# download model's new verson by model path, version id and download url
# output is a md log
def dl_model_new_version(msg, max_size_preview, skip_nsfw_preview):
    util.printD("Start dl_model_new_version")

    output = ""
    result = msg_handler.parse_js_msg(msg)
    if not result:
        output = "Parsing js ms failed"
        util.printD(output)
        return output

    model_path = result["model_path"]
    version_id = result["version_id"]
    download_url = result["download_url"]

    util.printD("model_path: " + model_path)
    util.printD("version_id: " + str(version_id))
    util.printD("download_url: " + download_url)

    # check data
    if not model_path:
        output = "model_path is empty"
        util.printD(output)
        return output

    if not version_id:
        output = "version_id is empty"
        util.printD(output)
        return output

    if not download_url:
        output = "download_url is empty"
        util.printD(output)
        return output

    if not os.path.isfile(model_path):
        output = "model_path is not a file: " + model_path
        util.printD(output)
        return output

    # get model folder from model path
    model_folder = os.path.dirname(model_path)

    # no need to check when downloading new version, since checking new version is already checked
    # check if this model is already existed
    # r = civitai.search_local_model_info_by_version_id(model_folder, version_id)
    # if r:
    #     output = "This model version is already existed"
    #     util.printD(output)
    #     return output

    # download file
    new_model_path = downloader.dl(download_url, model_folder, None, None)
    if not new_model_path:
        output = "Download failed, check console log for detail. Download url: " + download_url
        util.printD(output)
        return output

    # get version info
    version_info = civitai.get_version_info_by_version_id(version_id)
    if not version_info:
        output = "Model downloaded, but failed to get version info, check console log for detail. Model saved to: " + new_model_path
        util.printD(output)
        return output

    # now write version info to file
    base, ext = os.path.splitext(new_model_path)
    info_file = base + model.info_ext
    model.write_model_info(info_file, version_info)

    # then, get preview image
    civitai.get_preview_image_by_model_path(info_file, max_size_preview, skip_nsfw_preview)

    output = "File downloaded: " + new_model_path
    util.printD(output)
    return output

def open_model_folder(model_filepath):
    subprocess.Popen(f'explorer /select, "{model_filepath}"')
    return


def do_action(msg):
    result = msg_handler.parse_js_msg(msg)
    if not result:
        util.printD("Parsing js ms failed")
        return
    
    model_type = result["model_type"]
    search_term = result["search_term"]
    action = result["action"]

    if action == "add_trigger_words":
        result =  add_trigger_words(model_type, search_term, result["prompt"])
    
    elif action == "use_preview_prompt":
        result =  use_preview_prompt(model_type, search_term, result["prompt"], result["neg_prompt"])

    elif action == "open_model_url":
        result = open_model_url(model_type, search_term)

    elif action == "delete_model":
        result = model_action.delete_model_by_search_term(model_type, search_term)
    
    elif action == "open_model_folder":
        result = open_model_folder(result["model_filepath"])

    return result
