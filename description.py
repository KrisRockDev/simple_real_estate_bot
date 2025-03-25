import os
import sys
from icecream import ic

def generate_description(lst, des_file):
    with open(des_file, mode="w", encoding="utf-8") as f:
        for file_path in lst:
            with open(file_path, mode="r", encoding="utf-8") as file:
                text = file.read()
                tp = ''
                type_file = {
                    ".py" : "Python",
                }
                if file_path.endswith(".py"):
                    tp = type_file[".py"]
                f.write(f"{file_path.replace(os.getcwd(), '')}\n```{tp}\n{text}\n```\n\n")

def get_ignor(current_directory):
    file = os.path.join(current_directory, '.gitignore')
    with open(file=file, mode='r', encoding='utf-8') as f:
        ignor_list = f.readlines()
    ignor_list_clean = []
    for ignor_item in ignor_list:
        if '#' not in ignor_item:
            ignor_item = ignor_item.strip()
            if ignor_item != '':
                if ignor_item[-1] == r'/':
                    ignor_item = ignor_item[:-1]
                if ignor_item[0] == r'.':
                    ignor_item = ignor_item[1:]

                ignor_list_clean.append(ignor_item)
    # ic(ignor_list_clean)
    return ignor_list_clean


def des_creator():
    current_directory = os.getcwd()
    dir_list = os.listdir(current_directory)

    ignor_list = [
        current_file := os.path.basename(__file__),
        file_md:=f"{current_file.split('.')[0]}.md",
        'README.md'
    ]
    if '.gitignore' in dir_list:
        ignor_list += get_ignor(current_directory)
    ic(ignor_list)

    res_list = []
    for item in dir_list:
        if item not in ignor_list:
            ic(item)
            item_path = os.path.join(current_directory, item)
            if os.path.isfile(item_path) and item_path.endswith(".py"):
                res_list.append(item_path)
    ic(res_list)
    generate_description(lst=res_list, des_file=file_md)

if __name__ == '__main__':
    des_creator()
