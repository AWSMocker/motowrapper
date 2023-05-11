import yaml
import json
from yaml.loader import SafeLoader


# Open the file and load the file
def __convert_to_json(file_location):
    with open(file_location) as f:
        return yaml.load(f, Loader=SafeLoader)


# def __convert_to_list(item):
#     return [item] if isinstance(item, dict) else item


def __create_json_dict(file_location, file_type="yaml"):
    if file_type.lower() == "yaml":
        json_stack = __convert_to_json(file_location)
    else:
        with open(file_location) as f:
            json_stack = json.load(f)

    # for key in json_stack:
    #     outer_key = __convert_to_list(json_stack.get(key))
    #     for sec_layer_key in outer_key:
    #         service = __convert_to_list(json_stack.get(sec_layer_key))
    #         for iter in service:

              
    print(json_stack)



__create_json_dict("test.yaml", "yaml")


