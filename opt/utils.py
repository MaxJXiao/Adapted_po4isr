import random
import time
import openai
import re
import json

def extract_json_simple_replace(response_text):
    """
    Extracts a JSON object from a string that has a "===JSON_START===" separator.

    This function isolates the JSON by finding the first '{' and last '}'
    to ensure it works correctly even with markdown fences or extra whitespace.

    Args:
        response_text (str): The full string containing the separator and JSON.

    Returns:
        dict: The parsed JSON object as a Python dictionary, or None if an error occurs.
    """
    try:
        # 1. Get the text after the separator
        json_part = response_text.split("===JSON_START===")[1]

        # 2. Find the boundaries of the JSON object
        first_brace = json_part.find('{')
        last_brace = json_part.rfind('}')

        # 3. Slice the string to get only the valid JSON
        # This will fail gracefully in the json.loads() if a brace isn't found
        json_string = json_part[first_brace : last_brace + 1]

        # 4. Parse the clean string
        parsed_json = json.loads(json_string)
        # print("I'M GOING")
        return parsed_json

    except IndexError:
        print("Error: The separator '===JSON_START===' was not found.")
        return None
    except json.JSONDecodeError:
        print("Error: Could not find or parse a valid JSON object after the separator.")
        return None


def extract_bundle_score(response):
    json_schema = extract_json_simple_replace(response)
    if json_schema is not None:
        try:
            given_score = float(json_schema['score'])
        except:
            given_score = None
    else:
        given_score = None
    
    return given_score


def detect_error(bundle_score, target_score, mode='improve'):
    
    threshold = 1.1

    if bundle_score is not None:
        if mode == 'improve':
            if abs(bundle_score - target_score) > threshold:
                return False
            elif abs(bundle_score - target_score) <= threshold:
                return True
        elif mode == 'select':
            return True
    else:
        return False


# def detect_error(response, target, mode='improve'):
#     result_list = extract_item_list(response, target)
#     if not result_list:
#         return False
#     else:
#         if mode == 'improve':
#             threshold = 10
#             rank = int(result_list[-1])
#             if rank >= threshold:
#                 return False
#             else:
#                 return True
#         elif mode == 'select':
#             return True

# def extract_item_list(response, target):
#     try:
#         response = response.replace(" ", " ")
#         target = target.replace(" ", " ").replace("&amp;", "&").replace("&reg;","®")
#         index = response.rfind(target)
#         if index != -1:
#             preceding_text = response[:index].strip()
#             numbers = re.findall(r'\d+', preceding_text)
#             if numbers:
#                 result_list = numbers
#             else:
#                 result_list = []
#         else:
#             result_list = []
#     except:
#         result_list = []
#     return result_list


def extract_edit_prompt(response):
    pattern = r'<START>\s*(.*?)\s*<END>'
    result_list = re.findall(pattern, response, re.DOTALL)
    if len(result_list) == 0:
        pattern = r'<START>(.*?)<END>'
        result_list = re.findall(pattern, response, re.DOTALL)
    return result_list 

def load_eval_data(config):
    with open(f"{config['data_path']}{config['dataset']}/ID/test_seed_{config['seed']}.json", 'r') as json_file:
        test_data = json.load(json_file)
    return test_data


