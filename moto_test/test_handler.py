import yaml
import json
from yaml.loader import SafeLoader


def __s3_handler(payload):
    print("this is s3 handler")
    
def temp():
    print("we are working on this")

__service_handler_dict = {
    "S3": __s3_handler,
    "dynamodb": temp,
    "sqs": temp,
    "sns": temp
}


# Open the file and load the file
def __convert_to_json(file_location):
    with open(file_location) as f:
        return yaml.load(f, Loader=SafeLoader)


# def __convert_to_list(item):
#     return [item] if isinstance(item, dict) else item

def __service_handler(service, payload):
    print("service payload", service, payload)
    print("\n")
    __service_handler_dict.get(service)(payload)
    

def __create_json_dict(file_location, file_type):
    if file_type.lower() == "yaml":
        json_stack = __convert_to_json(file_location)
    else:
        with open(file_location) as f:
            json_stack = json.load(f)
            
    setup_list = json_stack.get("setup")
    for item_setup in setup_list:
        services = list(item_setup.keys())
        for service in services:
            __service_handler(service, item_setup.get(service))

              
    #print(json_stack)
    return json_stack


def moto_wrapper(**kwargs):
    def wrapper(func):
        print(kwargs)
        __create_json_dict(kwargs.get("file_location"), kwargs.get("file_type", "yaml"))
        return func
    return wrapper

@moto_wrapper(file_location="test.yaml")       
def foo():
    print("finished execution")
    
foo()