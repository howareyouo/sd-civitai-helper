# -*- coding: UTF-8 -*-
# handle msg between js and python side
import os
import time
import re
import requests
from . import downloader
from . import model
from . import util

url_dict = {
    "downloadPrefix": "https://civitai.com/api/download/models/",
    "modelVersionId": "https://civitai.com/api/v1/model-versions/",
    "modelPage": "https://civitai.com/models/",
    "modelId": "https://civitai.com/api/v1/models/",
    "hash": "https://civitai.com/api/v1/model-versions/by-hash/"
}

model_type_dict = {
    "Checkpoint": "ckp",
    "TextualInversion": "ti",
    "Hypernetwork": "hyper",
    "LORA": "lora",
    "LoCon": "lora"
}


# get image with full size
# width is in number, not string
# return: url str
def get_full_size_image_url(image_url, width):
    return re.sub('/width=\\d+/', '/width=' + str(width) + '/', image_url)


# use this sha256 to get model info from civitai
# return: model info dict
# cahe result for 5 minutes
def get_model_info_by_hash(hash: str):
    if not hash:
        util.printD("hash is empty")
        return

    r = requests.get(url_dict["hash"] + hash, headers=util.def_headers)
    if not r.ok:
        if r.status_code == 404:
            # this is not a civitai model
            util.printD("Civitai does not have this model")
            return {}
        else:
            util.printD("Get error code: " + str(r.status_code))
            util.printD(r.text)
            return

    # try to get content
    try:
        content = r.json()
    except Exception as e:
        util.printD("Parse response json failed")
        util.printD(str(e))
        util.printD("response:")
        util.printD(r.text)
        return

    if not content:
        util.printD("error, content from civitai is None")
        return

    return content


# caching recent results
def get_model_info_by_id(id: str):
    if not id:
        util.printD("id is empty")
        return

    r = requests.get(url_dict["modelId"] + str(id), headers=util.def_headers)
    if not r.ok:
        if r.status_code == 404:
            # this is not a civitai model
            util.printD("Civitai does not have this model")
            return {}
        else:
            util.printD("Get error code: " + str(r.status_code))
            util.printD(r.text)
            return

    # try to get content
    try:
        content = r.json()
    except Exception as e:
        util.printD("Parse response json failed")
        util.printD(str(e))
        util.printD("response:")
        util.printD(r.text)
        return

    if not content:
        util.printD("error, content from civitai is None")
        return

    return content


def get_version_info_by_version_id(_id: str):
    util.printD("Request version info from civitai")

    if not _id:
        util.printD("id is empty")
        return

    r = requests.get(url_dict["modelVersionId"] + str(_id), headers=util.def_headers)
    if not r.ok:
        if r.status_code == 404:
            # this is not a civitai model
            util.printD("Civitai does not have this model version")
            return {}
        else:
            util.printD("Get error code: " + str(r.status_code))
            util.printD(r.text)
            return

    # try to get content
    try:
        content = r.json()
    except Exception as e:
        util.printD("Parse response json failed")
        util.printD(str(e))
        util.printD("response:")
        util.printD(r.text)
        return

    if not content:
        util.printD("error, content from civitai is None")
        return

    return content


def get_version_info_by_model_id(id: str):
    model_info = get_model_info_by_id(id)
    if not model_info:
        util.printD(f"Failed to get model info by id: {id}")
        return

    # check content to get version id
    if "modelVersions" not in model_info.keys():
        util.printD("There is no modelVersions in this model_info")
        return

    if not model_info["modelVersions"]:
        util.printD("modelVersions is None")
        return

    if len(model_info["modelVersions"]) == 0:
        util.printD("modelVersions is Empty")
        return

    def_version = model_info["modelVersions"][0]
    if not def_version:
        util.printD("default version is None")
        return

    if "id" not in def_version.keys():
        util.printD("default version has no id")
        return

    version_id = def_version["id"]

    if not version_id:
        util.printD("default version's id is None")
        return

    # get version info
    version_info = get_version_info_by_version_id(str(version_id))
    if not version_info:
        util.printD(f"Failed to get version info by version_id: {version_id}")
        return

    return version_info


# get model info file's content by model type and search_term
# parameter: model_type, search_term
# return: model_info
def load_model_info_by_search_term(model_type, search_term):
    if model_type not in model.folders.keys():
        util.printD("unknow model type: " + model_type)
        return

    # search_term = subfolderpath + model name + ext. And it always start with a / even there is no sub folder
    base, ext = os.path.splitext(search_term)
    model_info_base = base
    if base[:1] == "/":
        model_info_base = base[1:]

    model_folder = model.folders[model_type]
    model_info_filename = model_info_base + model.info_ext
    model_info_filepath = os.path.join(model_folder, model_info_filename)

    if not os.path.isfile(model_info_filepath):
        util.printD("Can not find model info file: " + model_info_filepath)
        return

    return model.load_model_info(model_info_filepath)


# get model file names by model type
# parameter: model_type - string
# parameter: filter - dict, which kind of model you need
# return: model name list
def get_model_names_by_type_and_filter(model_type: str, filter: dict) -> list:
    model_folder = model.folders[model_type]

    # set filter
    # only get models don't have a civitai info file
    no_info_only = False
    empty_info_only = False

    if filter:
        if "no_info_only" in filter.keys():
            no_info_only = filter["no_info_only"]
        if "empty_info_only" in filter.keys():
            empty_info_only = filter["empty_info_only"]

    # get information from filter
    # only get those model names don't have a civitai model info file
    model_names = []
    for root, dirs, files in os.walk(model_folder, followlinks=True):
        for filename in files:
            item = os.path.join(root, filename)
            # check extension
            base, ext = os.path.splitext(item)
            if ext in model.exts:
                # find a model

                # check filter
                if no_info_only:
                    # check model info file
                    info_file = base + model.info_ext
                    if os.path.isfile(info_file):
                        continue

                if empty_info_only:
                    # check model info file
                    info_file = base + model.info_ext
                    if os.path.isfile(info_file):
                        # load model info
                        model_info = model.load_model_info(info_file)
                        # check content
                        if model_info:
                            if "id" in model_info.keys():
                                # find a non-empty model info file
                                continue

                model_names.append(filename)

    return model_names


def get_model_names_by_input(model_type, empty_info_only):
    return get_model_names_by_type_and_filter(model_type, {"empty_info_only": empty_info_only})


# get modelId, modelVersionId from url
def get_model_id_from_url(url: str) -> list:
    if not url:
        util.printD("url or model id can not be empty")
        return

    if url.isnumeric():
        # is already an id
        return None, url

    parts = url.split('/')
    last_part = parts[-1]

    if url.startswith(url_dict["downloadPrefix"]):
        return None, last_part

    modelVersionId = None
    if 'modelVersionId' in last_part:
        modelId, modelVersionId = last_part.split('?modelVersionId=')
    else:
        modelId = parts[4]

    return modelId, modelVersionId


# get preview image by model path
# image will be saved to file, so no return
def get_preview_image_by_model_path(model_path: str, max_size_preview, skip_nsfw_preview):
    if not model_path or not os.path.isfile(model_path):
        util.printD("model_path is not a file: " + model_path)
        return

    base, ext = os.path.splitext(model_path)
    for ext in model.preview_extensions:
        if os.path.isfile(base + ".preview." + ext) or os.path.isfile(base + "." + ext):
            return

    short_path = util.shorten(model_path)
    # util.printD("Missing preview: " + short_path)

    # load model_info file
    info_file = base + model.info_ext
    if not os.path.isfile(info_file): return

    model_info = model.load_model_info(info_file)
    if not model_info:
        util.printD("Empty model info: " + short_path)
        return

    images = model_info["images"]
    if not images: return
    for img_dict in images:
        if (img_dict.get("nsfw", False) or img_dict.get("nsfwLevel", 1) > 4) and skip_nsfw_preview: 
            continue

        img_url = img_dict["url"]
        if img_url:
            ext = os.path.splitext(img_url)[1]
            if img_dict["type"] == "video":
                ext = ".mp4"
            else:
                img_url = get_full_size_image_url(img_url, img_dict["width"])

            image_preview = base + ext
            preview_path = downloader.download(img_url, image_preview)
            if not preview_path:
                continue
            util.printD("Preview saved: " + util.shorten(preview_path))
            break # we only need 1 preview image


# search local model by version id in 1 folder, no subfolder
# return - model_info
def search_local_model_info_by_version_id(folder: str, version_id: int):
    util.printD(f"Searching local model by version id: [{version_id}]")
    util.printD(f"Searching in folder: [{folder}]")

    if not folder or not os.path.isdir(folder):
        util.printD("folder is not a dir")
        return

    if not version_id:
        util.printD("version_id is none")
        return

    # search cwivitai model info file
    for filename in os.listdir(folder):
        # check ext
        base, ext = os.path.splitext(filename)

        # find civitai info file
        if ext == model.info_ext:
            path = os.path.join(folder, filename)
            model_info = model.load_model_info(path)
            if not model_info:
                continue

            if "id" not in model_info.keys():
                continue

            id = model_info["id"]
            if not id:
                continue

            # util.printD(f"Compare version id, src: {id}, target:{version_id}")
            if str(id) == str(version_id):
                # find the one
                return model_info
    return


# check new version for a model by model path
# return (model_path, model_id, model_name, new_verion_id, new_version_name, description, download_url, img_url)
def check_model_new_version_by_path(model_path: str, delay: float = 2):
    if not model_path:
        util.printD("model_path is empty")
        return

    if not os.path.isfile(model_path):
        util.printD("model_path is not a file: " + model_path)
        return

    # get model info file name
    base, ext = os.path.splitext(model_path)
    info_file = base + model.info_ext

    if not os.path.isfile(info_file):
        return

    # get model info
    model_info_file = model.load_model_info(info_file)
    if not model_info_file:
        return

    if "id" not in model_info_file.keys():
        return

    local_version_id = model_info_file["id"]
    if not local_version_id:
        return

    if "modelId" not in model_info_file.keys():
        return

    model_id = model_info_file["modelId"]
    if not model_id:
        return

    # get model info by id from civitai
    model_info = get_model_info_by_id(model_id)
    # delay before next request, to prevent to be treat as DDoS 
    util.printD(f"delay {delay} second")
    time.sleep(delay)

    if not model_info:
        return

    if "modelVersions" not in model_info.keys():
        return

    modelVersions = model_info["modelVersions"]
    if not modelVersions:
        return

    if not len(modelVersions):
        return

    current_version = modelVersions[0]
    if not current_version:
        return

    if "id" not in current_version.keys():
        return

    current_version_id = current_version["id"]
    if not current_version_id:
        return

    util.printD(f"Compare version id, local: {local_version_id}, remote: {current_version_id} ")
    if current_version_id == local_version_id:
        return

    model_name = ""
    if "name" in model_info.keys():
        model_name = model_info["name"]

    if not model_name:
        model_name = ""

    new_version_name = ""
    if "name" in current_version.keys():
        new_version_name = current_version["name"]

    if not new_version_name:
        new_version_name = ""

    description = ""
    if "description" in current_version.keys():
        description = current_version["description"]

    if not description:
        description = ""

    downloadUrl = ""
    if "downloadUrl" in current_version.keys():
        downloadUrl = current_version["downloadUrl"]

    if not downloadUrl:
        downloadUrl = ""

    # get 1 preview image
    img_url = ""
    if "images" in current_version.keys():
        if current_version["images"]:
            if current_version["images"][0]:
                if "url" in current_version["images"][0].keys():
                    img_url = current_version["images"][0]["url"]
                    if not img_url:
                        img_url = ""

    return model_path, model_id, model_name, current_version_id, new_version_name, description, downloadUrl, img_url


# check model's new version
# parameter: delay - float, how many seconds to delay between each request to civitai
# return: new_versions - a list for all new versions, each one is (model_path, model_id, model_name, new_verion_id, new_version_name, description, download_url, img_url)
def check_models_new_version_by_model_types(model_types: list, delay: float = 2) -> list:
    util.printD("Checking models' new version")

    if not model_types:
        return []

    # check model types, which cloud be a string as 1 type
    mts = []
    if type(model_types) is str:
        mts.append(model_types)
    elif type(model_types) is list:
        mts = model_types
    else:
        util.printD(f"Unknow model types: {model_types}")
        return []

    # new version list
    new_versions = []

    # walk all models
    for model_type, model_folder in model.folders.items():
        if model_type not in mts:
            continue

        util.printD("Scanning path: " + util.shorten(model_folder))
        for root, dirs, files in os.walk(model_folder, followlinks=True):
            for filename in files:
                # check ext
                item = os.path.join(root, filename)
                base, ext = os.path.splitext(item)
                if ext in model.exts:
                    # find a model
                    r = check_model_new_version_by_path(item, delay)

                    if not r:
                        continue

                    model_path, model_id, model_name, current_version_id, new_version_name, description, downloadUrl, img_url = r
                    # check exist
                    if not current_version_id:
                        continue

                    # check this version id in list
                    is_already_in_list = False
                    for new_version in new_versions:
                        if current_version_id == new_version[3]:
                            # already in list
                            is_already_in_list = True
                            break

                    if is_already_in_list:
                        util.printD("New version is already in list")
                        continue

                    # search this new version id to check if this model is already downloaded
                    target_model_info = search_local_model_info_by_version_id(root, current_version_id)
                    if target_model_info:
                        util.printD("New version is already existed")
                        continue

                    # add to list
                    new_versions.append(r)

    return new_versions

