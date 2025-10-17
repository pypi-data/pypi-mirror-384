import os
from typing import Union, List, Optional
import json
import regex as re
import ast
import random

def fix_json(input_str):
    # Add double quotes around keys using regex
    fixed_str = re.sub(r'(\w+):', r'"\1":', input_str)
    
    # Add double quotes around string values if necessary and wrap int/float values in []
    def format_value(match):
        key, value, comma = match.groups()
        value = value.strip()
        # Check if value is an integer or float
        if re.match(r'^-?\d+(\.\d+)?$', value):
            value = f'[{value}]'
        # Check if value is a boolean or null
        elif re.match(r'^(true|false|null)$', value, re.IGNORECASE):
            pass  # leave as is
        else:
            # Add quotes around string values
            value = f'"{value}"'
        return f'{key}: {value}{comma}'
    
    fixed_str = re.sub(r'(".*?"):(.*?)(,|})', format_value, fixed_str)
    
    return fixed_str

def repair_reasoning_field_robust(json_str: str) -> str:
    """
    使用正则表达式和先行断言，健壮地修复 "reasoning" 字段内部未转义的双引号。
    此方法可以处理 "reasoning" 字段不是最后一个字段的情况。

    Args:
        json_str: 可能包含格式错误的JSON字符串。

    Returns:
        修复后的JSON字符串。
    """
    # 1. 定义新的正则表达式，使用正向先行断言来定位 "reasoning" 值的结束位置
    # re.DOTALL 标志让 '.' 可以匹配包括换行符在内的任意字符
    pattern = re.compile(
        # --- 第1个捕获组: reasoning 字段的 "前缀" ---
        r'("reasoning"\s*:\s*")'
        
        # --- 第2个捕获组: reasoning 字段的 "内容" ---
        r'(.*?)'
        
        # --- 正向先行断言: 寻找值的结束边界，但不消耗它 ---
        # 匹配到 "reasoning" 值的结束双引号，这个双引号后面必须跟着一个逗号或一个右花括号
        r'(?="\s*[,}])',
        
        re.DOTALL
    )

    # 2. 定义一个更简单的替换函数
    def replacer(match):
        # 提取出两个捕获组
        prefix = match.group(1)      # 例如: '"reasoning" : "'
        content = match.group(2)     # 例如: 'Overall building...'
        
        # 只在 "内容" 部分进行替换，将所有双引号转义
        fixed_content = content.replace('"', '\\"')
        
        # 重新组合。注意：我们不需要处理后缀，因为它没有被匹配和消耗掉。
        return prefix + fixed_content

    # 3. 使用 re.sub 执行查找和替换
    repaired_str = pattern.sub(replacer, json_str)
    
    return repaired_str

def read_file_to_string(file_path):
    """
    Reads the contents of a text file and returns it as a string.

    :param file_path: The path to the text file.
    :return: A string containing the contents of the file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"The file {file_path} was not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def read_files_to_string(file_paths):
    """
    Reads the contents of multiple text files and returns them as a single string,
    with each file's contents separated by a newline.

    :param file_paths: A list of paths to text files.
    :return: A string containing the concatenated contents of the files.
    """
    all_contents = []  # List to hold the contents of each file

    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                all_contents.append(file.read())
        except FileNotFoundError:
            print(f"The file {file_path} was not found.")
        except Exception as e:
            print(f"An error occurred while reading {file_path}: {e}")

    # Join all the contents with a newline character
    return "\n".join(all_contents)

def get_file_path(filename: Union[str, os.PathLike], search_from: Union[str, os.PathLike] = "."):
    """
    Search for a file across a directory and return its absolute path.

    Args:
        filename (Union[str, os.PathLike]): The name of the file to search for.
        search_from (Union[str, os.PathLike], optional): The directory from which to start the search. Defaults to ".".

    Returns:
        str: Absolute path to the found file.

    Raises:
        FileNotFoundError: If the file is not found.
    """
    for root, dirs, files in os.walk(search_from):
        for name in files:
            if name == filename:
                return os.path.abspath(os.path.join(root, name))
    raise FileNotFoundError(filename, "not found.")



#+=========================================================================================
def verify(s, target_sequence):
    # Count the occurrences of the target sequence
    count = s.count(target_sequence)

    # Check if the target sequence appears exactly twice
    return count == 2


def is_int_between_0_and_10(s):
    try:
        num = int(s)
        return 0 <= num <= 10
    except ValueError:
        return False
    
def is_str_a_list_of_ints_0_to_10(s):
    try:
        # Attempt to parse the string as a Python literal (list, dict, etc.)
        parsed = ast.literal_eval(s)

        # Check if the parsed object is a list
        if not isinstance(parsed, list):
            return False

        # Check if all elements are integers and between 0 to 10
        return all(isinstance(item, int) and 0 <= item <= 10 for item in parsed)

    except (ValueError, SyntaxError):
        # If parsing fails or any other error occurs
        return False
    
def is_str_valid_score_format_brackets(s):
    try:
        # Removing brackets and splitting the string by commas
        content = s.strip("[]").split(',')

        length = len(content)

        # Parsing each element and checking the format and range
        scores = {}
        for item in content:
            key, value = item.split(':')
            key = key.strip()
            value = int(value.strip())

            # Check if the key starts with 'score' and the value is in the correct range
            if not key.startswith("score") or not 0 <= value <= 10:
                return False

            scores[key] = value

        fetch_words = [f"score{i+1}" for i in range(length)]
        # Check if at least 'score1' and 'score2' are present
        return all(key in scores for key in fetch_words)

    except (ValueError, SyntaxError):
        # If any parsing error occurs
        return False

def normalize_quotes(s: str) -> str:
    """
    Replace curly/smart quotes with normal ASCII quotes.
    """
    # 常见的几种智能引号 U+201C U+201D U+2018 U+2019
    return s.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")

def fallback_repair_json(input_str: str) -> str:
    """
    A last-resort JSON repair function.
    It tries to reconstruct a valid JSON object with the target structure:
        {"reasoning": "...", "score": [float, float]}
    even if the original input string is heavily corrupted.

    Args:
        input_str (str): Possibly malformed JSON string.

    Returns:
        str: A repaired and valid JSON string.
    """

    # 1. Try to extract the reasoning text between "reasoning" and "score"
    reasoning_match = re.search(
        r'"?reasoning"?\s*[:：]\s*["\']?(.*?)["\']?\s*,\s*"?score"?',
        input_str,
        re.DOTALL | re.IGNORECASE,
    )

    if reasoning_match:
        reasoning_text = reasoning_match.group(1).strip()
    else:
        # If not found, fallback to an empty string
        reasoning_text = ""

    # 2. Clean and normalize the reasoning content
    reasoning_text = reasoning_text.replace('\\"', '"')  # Unescape existing escapes
    reasoning_text = re.sub(r'["“”]', '"', reasoning_text)  # Normalize quotes
    reasoning_text = reasoning_text.strip()
    # Escape any remaining unescaped double quotes to avoid breaking JSON
    reasoning_text = reasoning_text.replace('"', '\\"')

    # 3. Try to extract the score list (two floats)
    score_match = re.search(
        r'"?score"?\s*[:：]\s*\[?([^\]]+)\]?', input_str, re.DOTALL | re.IGNORECASE
    )
    scores = []
    if score_match:
        # Extract numeric values using regex
        nums = re.findall(r"-?\d+(?:\.\d+)?", score_match.group(1))
        try:
            scores = [float(n) for n in nums[:2]]
        except ValueError:
            pass

    # Fill missing values with default zeros
    if len(scores) < 2:
        scores += [0.0] * (2 - len(scores))

    # 4. Construct the repaired JSON object
    repaired_obj = {"reasoning": reasoning_text, "score": scores}

    # 5. Return a valid JSON string
    return json.dumps(repaired_obj, ensure_ascii=False)

def robust_json_fix(s: str):
    try:
        return json.loads(s)
    except Exception:
        pass
    
    for fixer in [fix_json, repair_reasoning_field_robust]:
        s = fixer(s)
        try:
            return json.loads(s)
        except Exception:
            print(f"Error: Cannot fix {fixer.__name__} {s=}")
            continue

    try:
        repaired_str = fallback_repair_json(s)
        return json.loads(repaired_str)
    except Exception as e:
        print(f"Error: Cannot fix fallback_repair_json {s=} {e=}")
        return False

#+=========================================================================================
def mllm_output_to_dict(input_string, give_up_parsing=False, text_prompt=None, score_range: int = 10):
    """
    Args:
        input_string (str): actually the output of the mllm model to be parsed
        output_file_name (str): The name of the output file.
    """
    # Catch for gpt4v rate_limit_exceeded error
    if input_string == "rate_limit_exceeded":
        return "rate_limit_exceeded"

    if give_up_parsing:
        guessed_value = random.randint(0, score_range)
        json_content = {'score': [guessed_value, guessed_value], "reasoning": f"guess_if_cannot_parse | {input_string}"}
        return json_content
    
    # Define the delimiters
    delimiter = '||V^=^V||'

    if input_string.count(delimiter) == 2:
        if not verify(input_string, delimiter):
            print("The required delimiters were not found correctly in the string.", flush=True)
            return False
        # Extract the content between the delimiters
        start_index = input_string.find(delimiter) + len(delimiter)
        end_index = input_string.rfind(delimiter)
    else:
        # find the json mannually
        # some mllm tends not to output the delimiters, but it does output the json contents
        # so we will find the json content mannually
        start_index = input_string.find('{')
        end_index = input_string.rfind('}') + 1
        if start_index == -1 or end_index == 0:
            # json not found
            # some mllm tends to output only a list of scores like [6, 0], 
            # this time we will just get the scores and ignore the reasoning (other part of the json)
            start_index = input_string.find('[')
            end_index = input_string.rfind(']') + 1
            if re.match(r'^\[\d+, ?\d+\]$', input_string[start_index:end_index]):
                scores = json.loads(input_string[start_index:end_index])
                if not isinstance(scores, list):
                    scores = [scores]
                json_content = {'score': scores, "reasoning": "System: output is simply a list of scores"}
                json_str = json.dumps(json_content)
                input_string = json_str
                start_index = 0
                end_index = len(json_str)
            elif is_int_between_0_and_10(input_string): # if output is simply a number
                scores = [int(input_string)]
                json_content = {'score': scores, "reasoning": "System: output is simply a number"}
                json_str = json.dumps(json_content)
                input_string = json_str
                start_index = 0
                end_index = len(json_str)
            else:
                print(f"22 222 Failed to find the json content in the string. {text_prompt=} {input_string=}", flush=True)
                return False
    
    # Check if we found two delimiters
    if start_index != -1 and end_index != -1 and start_index != end_index:
        # Extract the JSON string
        json_str = input_string[start_index:end_index].strip()
        json_str = json_str.replace("\n", "")
        # Parse the JSON string into a dictionary
        try:
            json_str = normalize_quotes(json_str)
            new_data = json.loads(json_str)
            if not isinstance(new_data['score'], list):
                new_data['score'] = [new_data['score']]
        except Exception as e1:
            print(f"Now fixing: {e1=} {json_str=}")
            
            new_data = robust_json_fix(json_str)

            # try:
            #     new_data = json.loads(fix_json(json_str))
            #     return new_data
            # except Exception as e2:
            #     try:
            #         print(f"Now fixing: {e2=} {fix_json(json_str)=}")
            #         new_data = json.loads(repair_reasoning_field_robust(fix_json(json_str)))
            #         return new_data
            #     except Exception as e3:
            #         print(f"Error: Cannot fix {e3=} {repair_reasoning_field_robust(fix_json(json_str))=}")
            #         return False
        return new_data
    else:
        print("The required delimiters were not found correctly in the string.")
        return False

def write_entry_to_json_file(input_string, uid, prompt_input, vision_input, output_file_name, give_up_parsing=False):
    """
    Args:
        input_string (str): actually the output of the mllm model to be parsed
        uid (str): The unique identifier for the each item in the test data
        prompt_input (str): The prompt input for the entry. text prompt.
        vision_input (str): The vision input for the entry. image links.
        output_file_name (str): The name of the output file.
    """
    # Catch for gpt4v rate_limit_exceeded error
    if input_string == "rate_limit_exceeded":
        return "rate_limit_exceeded"

    # Define the delimiters
    delimiter = '||V^=^V||'

    if input_string.count(delimiter) == 2:
        if not verify(input_string, delimiter):
            print("The required delimiters were not found correctly in the string.")
            return False
        # Extract the content between the delimiters
        start_index = input_string.find(delimiter) + len(delimiter)
        end_index = input_string.rfind(delimiter)
    else:
        # find the json mannually
        # some mllm tends not to output the delimiters, but it does output the json contents
        # so we will find the json content mannually
        start_index = input_string.find('{')
        end_index = input_string.rfind('}') + 1
        if start_index == -1 or end_index == 0:
            # json not found
            # some mllm tends to output only a list of scores like [6, 0], 
            # this time we will just get the scores and ignore the reasoning (other part of the json)
            start_index = input_string.find('[')
            end_index = input_string.rfind(']') + 1
            if give_up_parsing: # if we want to give up parsing
                guessed_value = random.randint(0, 10)
                print(f"Failed to find the json content in the string. Guess a value : {guessed_value}.")
                json_content = {'score': [guessed_value], "reasoning": f"guess_if_cannot_parse | {input_string}"}
                json_str = json.dumps(json_content)
                input_string = json_str
                start_index = 0
                end_index = len(json_str)
            elif re.match(r'^\[\d+, ?\d+\]$', input_string[start_index:end_index]):
                scores = json.loads(input_string[start_index:end_index])
                json_content = {'score': scores, "reasoning": None}
                json_str = json.dumps(json_content)
                input_string = json_str
                start_index = 0
                end_index = len(json_str)
            elif is_int_between_0_and_10(input_string): # if output is simply a number
                scores = [int(input_string)]
                json_content = {'score': scores, "reasoning": None}
                json_str = json.dumps(json_content)
                input_string = json_str
                start_index = 0
                end_index = len(json_str)
            else:
                print("Failed to find the json content in the string.")
                return False
    
    # Check if we found two delimiters
    if start_index != -1 and end_index != -1 and start_index != end_index:
        # Extract the JSON string
        json_str = input_string[start_index:end_index].strip()
        json_str = json_str.replace("\n", "")
        try:
            # Parse the JSON string into a dictionary
            new_data = json.loads(json_str)
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(output_file_name), exist_ok=True)
            
            # Initialize or load existing data
            if os.path.exists(output_file_name):
                with open(output_file_name, 'r') as json_file:
                    data = json.load(json_file)
            else:
                data = {}
            
            # If the additional key is already in the data, add or update notes
            if uid in data:
                data[uid].update(new_data)  # Update with new data
                if prompt_input:  # If there are new notes, update or add them
                    data[uid]['prompt_input'] = prompt_input
                if vision_input:  # If there are new notes, update or add them
                    data[uid]['vision_input'] = vision_input
            else:
                # If it's a new key, add the entry to the dictionary
                data[uid] = new_data
                if prompt_input:
                    data[uid]['prompt_input'] = prompt_input
                if vision_input:
                    data[uid]['vision_input'] = vision_input
            
            # Write the updated data to the file
            with open(output_file_name, 'w') as json_file:
                json.dump(data, json_file, indent=4)
            
            print(f"Data was successfully updated in {output_file_name}")
            return True
        except json.JSONDecodeError as e:
            print(f"An error occurred while parsing the JSON content: {e}")
            return False
    else:
        print("The required delimiters were not found correctly in the string.")
        return False


def check_key_in_json(file_path, key):
    try:
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
        
        # Check if the key exists at the top level of the JSON structure
        if key in data:
            return True
        else:
            return False
    except FileNotFoundError:
        print(f"The file {file_path} was not found.")
    except json.JSONDecodeError as e:
        print(f"Error reading {file_path}: {e}")
    except Exception as e:
        print(f"An error occurred with {file_path}: {e}")
    return False