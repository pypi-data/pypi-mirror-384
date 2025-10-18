import collections
import json
import os
import sys
import yaml


def load_json(json_path):
    if not os.path.exists(json_path):
        return

    with open(json_path, "r") as fp:
        json_data = json.load(fp, object_pairs_hook=collections.OrderedDict)
    return json_data

def load_yaml(yaml_path):
    if not os.path.exists(yaml_path):
        return

    with open(yaml_path, "r") as fp:
        json_data = yaml.safe_load(fp)
    return json_data


def get_json_indent_level(json_path):
    with open(json_path, "r") as fp:
        first_couple_of_characters = fp.readline(8)

    if len(first_couple_of_characters) > 2:
        return None

    with open(json_path, "r") as fp:
        fp.readline()  # read first line so we can get to the second one

        next_line = fp.readline()
        indent_number = len(next_line) - len(next_line.lstrip())
    return indent_number


def save_json(json_data, json_path, indent=2):
    with open(json_path, "w+") as fp:
        json.dump(json_data, fp, indent=indent)


def save_yaml(yaml_data, yaml_path):
    with open(yaml_path, "w+") as fp:
        yaml.dump(yaml_data, fp)
