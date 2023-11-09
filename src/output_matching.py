import re
import logging
import json
from pprint import pprint

re_dialogue_manager = re.compile("\{[\s\n]*\"next action\":[\s\n]*\".+\",[\s\n]*\"chunk to work on\":[\s\n]*(\".+\"|null)[\s\n]*\}")
re_question_extraction = re.compile("\{[\s\n]*\"summary\":[\s\n]*\".+\"[\s\n]*\}")
re_question_grouping = re.compile("\{[\s\n]*(\"[^\}]+\":[\s\n]*\[[^\}]+\][\s\n]*,{0,1}[\s\n]*)*[\s\n]*\}")
re_question_generation = re.compile("\{[\s\n]*\"question\"[\s\n]*:[\s\n]*\".+\"[\s\n]*,[\s\n]*\"fields\"[\s\n]*:[\s\n]*\[.+\][\s\n]*\}")
re_answer_parsing = re.compile("\{[\s\n]*\"next action\"[\s\n]*:[\s\n]*\".+\"[\s\n]*\}")
re_chunk_filling = re.compile("\{[\s\n]*\"next action\"[\s\n]*:[\s\n]*\".+\"[\s\n]*\}")
re_form_filling = re.compile("\{.*\}")
re_fill_validation = re.compile("\{.*\}")

re_information_extraction = re.compile("\{([\s\n]*,{0,1}[\s\n]*\".+\"[\s\n]*:[\s\n]*\".*\"[\s\n]*[\s\n]*)*\}")
re_follow_up_question = re.compile("\{[\s\n]*\"question\"[\s\n]*:[\s\n]*\".+\"[\s\n]*\}")
re_repeat_question = re.compile("\{[\s\n]*\"new question\"[\s\n]*:[\s\n]*\".+\"[\s\n]*\}")

re_user = re.compile("\{[\s\n]*\"answer\"[\s\n]*:.*\}")



# form_filling should be the same as the input form section with potential changes to 'answer' fields
# same for fill validation


module_match = {
    'cfil': re_chunk_filling,
    'dman': re_dialogue_manager,
    'qext': re_question_extraction,
    'qgen': re_question_generation,
    'qgrp': re_question_grouping,
    'apar': re_answer_parsing,
    'ffil': re_form_filling,
    'fval': re_fill_validation,
    'iext': re_information_extraction,
    'fupq': re_follow_up_question,
    'repq': re_repeat_question,
    'user': re_user
}


def match_output(output, module):
    expression = module_match.get(module, None)
    if module in ['ffil', 'fval']:
        span, group =  extract_nested_content(output)
    else:
        if not expression:
            logging.warning('could not match the module output since there is no regular expression for `%s`', module)
            return (0,len(output)), output
        output = remove_nl(output)
        tmp = expression.finditer(output)
        lst_tmp = [i for i in tmp]
        # print(lst_tmp)
        if not lst_tmp:
            # print(1)
            return None, output
        res = lst_tmp[-1]
        span = res.span()
        group = res.group()

    try:
        loaded = json.loads(group)
        if module == 'user':
            if isinstance(loaded['answer'], dict):
                loaded['answer'] = json.dumps(loaded['answer'])
                group = json.dumps(loaded)
                # print(2)
    except json.decoder.JSONDecodeError as e:
        logging.warning(str(e))
        # print(3)
        return None, output
    
    return span, group


def extract_nested_content(string):
    opened = 0
    start = None
    end = None
    for i in range(len(string)):
        if string[i] == '{':
            opened += 1
            if start is None:
                start = i
        elif string[i] == '}':
            opened -= 1
            if not opened:
                end = i
                break
    if start is None or end is None:
        return None, string
    if end+1 < len(string):
        new_span, new_group = extract_nested_content(string[end+1:])
        if new_span is not None:
            return new_span, new_group
    return (start, end+1), string[start:end+1]

def remove_nl(output):
    in_str = False
    for i in range(len(output)):
        if output[i] == '"':
            in_str = not in_str
        if output[i] == "\n" and in_str:
            output = output[:i] + "; " + output[i+1:]
    return output


                

# sanity checks
if __name__ == '__main__':
    # print('Dialogue Manager:')
    # print(bool(re_dialogue_manager.search('{"next action": "fill_chunk", "chunk to work on": null}?')))
    # print('Question Extraction:')
    # print(re_question_extraction.search('{"question": "Please provide the name to be shown on the card, including the first name, full middle name (if applicable), and last name. If the full name at birth is different than the name on the card, please provide the full name at birth as well. Additionally, if you have used any other names, please enter them here, separating them by a comma (,)."}'))
    # print('Question Grouping:')
    # print(re_question_grouping.search('{"Group 1": ["1", "2", "11", "12", "13"]}{"Group 2": ["3", "4", "14"], "Group 3": ["5", "6", "7", "8"], "Group 4": ["9"], "Group 5": ["10"], "Group 6": ["15"], "Group 7": ["16"], "Group 8": ["17"], "Group 9": ["18"]}'))
    # print('Question Generation:')
    # print(re_question_generation.search('{ "question": "What is the full name you would like to appear on the card?" }'))
    # print('Answer Parsing:')
    # print(re_answer_parsing.search('{"full name": "Yan Eric Weiser", "fuller name": "also yan"}'))

    test_s = """{"Social Security Information": ["11", "12", "13", "14", "15", "16", "17", "18"],
"Personal Information": ["11", "12", "13", "14", "15", "16", "17", "18"]}"""

    # span, group = match_output(test_s, 'user')
    # print(span)
    print(test_s)
    print()
    # test_s = test_s.replace('\n', '\\n')
    test_s = remove_nl(test_s)
    # test_s = test_s.replace('[nl]', '\n')
    # x = json.loads(test_s)
    # pprint(json.dumps(x))
  
    # print(x)
    print(test_s)
    print()
    # print(re_user.pattern)
    # print()
    mat = re_question_grouping.search(test_s)
    print(mat.group())
    x = json.loads(mat.group())
    print()
    pprint(x)