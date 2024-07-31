import argparse
import os
import re
import sys


def preprocess_content(content):
    var_pattern = re.compile(r"\$\{(.*?)\}")
    return var_pattern.sub("default", content)


function_patterns = {
    "icmp": re.compile(r"\$\(\s*icmp\(\s*(.*?),\s*(.*?)\s*\)\s*\)"),
    "regexcontains": re.compile(
        r"\$\((\s*(!?)\s*)regexcontains\(\s*(.*?),\s*(.*?)\s*\)\s*\)"
    ),
    "obj": re.compile(r"\$\(\s*obj\((.*?)\)\)((\.\w+)*)"),
    "obj_end": re.compile(r"\$\(\s*obj_end\((.*?)\)\)((\.\w+)*)"),
    "glob": re.compile(r"\$\(\s*glob\((.*?)\)\s*\)"),
    "list_get": re.compile(r"\$\(\s*list_get\(\s*(.*?),\s*(\d+)\s*\)\s*\)"),
    "list_set": re.compile(r"\$\(\s*list_set\(\s*(.*?),\s*(\d*),\s*(.*?)\s*\)\s*\)"),
    "list_add": re.compile(r"\$\(\s*list_add\(\s*(.*?),\s*(\d*),\s*(.*?)\s*\)\s*\)"),
    "list_del": re.compile(r"\$\(\s*list_del\(\s*(.*?),\s*(\d+)\s*\)\s*\)"),
    "list_size": re.compile(r"\$\(\s*list_size\(\s*(.*?)\s*\)\s*\)"),
    "list_sub": re.compile(r"\$\(\s*list_sub\(\s*(.*?),\s*(\d*),\s*(.*?)\s*\)\s*\)"),
    "subst": re.compile(r"subst\(\s*(.*?),\s*(.*?),\s*(.*?)\s*\)"),
    "upper": re.compile(r"upper\(\s*(.*?)\s*\)"),
    "lower": re.compile(r"lower\(\s*(.*?)\s*\)"),
    "contains": re.compile(
        r"(\s*(!?)\s*)contains(\(\[\s*(.*?)\s*\]\s*,\s*(.*?)\s*\)|\(\s*(.*?)\s*,\s*(.*?)\s*\))"
    ),
    "join": re.compile(
        r"(?:join\(\[\s*(.*?)\s*\]\s*,\s*(.*?)\s*\)|join\(\s*(.*?)\s*,\s*(.*?)\s*\))"
    ),
    "concat": re.compile(r"concat\(\s*(.*?)\s*\)"),
    "strip": re.compile(r"strip\(\s*(.*?)\s*\)"),
    "startswith": re.compile(r"(\s*(!?)\s*)startswith\(\s*(.*?),\s*(.*?)\s*\)"),
    "endswith": re.compile(r"(\s*(!?)\s*)endswith\(\s*(.*?),\s*(.*?)\s*\)"),
    "arithop": re.compile(r"arithop\(\s*(.*?)\s*\)"),
    "npack": re.compile(r"npack\(\s*(.*?)\s*\)"),
    "npack_installdir": re.compile(r"npack_installdir\(\s*(.*?)\s*\)"),
}


def check_and_log_invalid_functions(file_path, directory):
    with open(os.path.join(directory, file_path), "r") as f:
        line_number = 0
        for line in f:
            line_number += 1
            if not line.startswith("#"):
                processed_line = preprocess_content(line.rstrip("\n"))
                func_name_pattern = re.compile(r"\$\((.*?)\(")
                possible_func_names = set(re.findall(func_name_pattern, processed_line))
                possible_func_names = [name.strip() for name in possible_func_names]

                for func_name in possible_func_names:
                    if func_name in function_patterns:
                        keyword_pattern = function_patterns[func_name]
                        if (
                            keyword_pattern.search(processed_line) is None
                            and func_name in processed_line
                        ):
                            print(
                                f"In file {os.path.join(directory, file_path)}, on line {line_number}, found keyword '{func_name}', but could not match the corresponding function pattern."
                            )
                        else:
                            continue
                    elif func_name.replace("!", "").strip() in function_patterns:
                        func_name = func_name.replace("!", "").strip()
                        keyword_pattern = function_patterns[func_name]
                        if (
                            keyword_pattern.search(processed_line) is None
                            and func_name in processed_line
                        ):
                            print(
                                f"In file {os.path.join(directory, file_path)}, on line {line_number}, found keyword '{func_name}', but could not match the corresponding function pattern."
                            )
                        else:
                            continue
                    else:
                        print(func_name)
                        print(
                            f"In file {os.path.join(directory, file_path)}, on line {line_number}, found an unrecognized function name '{func_name}'."
                        )


def check_functions_in_dir(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file == "npk.yml":
                check_and_log_invalid_functions(file, root)


def main():
    parser = argparse.ArgumentParser(description="NPK格式校验工具")
    parser.add_argument("path", help="要校验的npk.yml文件或目录路径")
    parser.add_argument("-log", "--logfile", help="结果写入文件路径")
    args = parser.parse_args()

    npk_path = args.path

    if os.path.isfile(npk_path) and npk_path.endswith(".yml"):
        directory = os.path.dirname(npk_path)
        check_and_log_invalid_functions(npk_path, directory)
    elif os.path.isdir(npk_path):
        check_functions_in_dir(npk_path)
    else:
        print(f"错误：'{npk_path}' 不是一个有效的目录或yml文件。 ")


if __name__ == "__main__":
    main()
