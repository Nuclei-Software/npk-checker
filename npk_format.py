import argparse
import os
import sys
import jsonschema
from yaml import load, Loader


with open("npk_schema.yml", "r") as f:
    npk_schema = load(f, Loader=Loader)


def validate_file(file_path):
    with open(file_path, "r") as f:
        try:
            npk_data = load(f, Loader=Loader)
        except Exception as exc:
            if hasattr(exc, "problem_mark"):
                mark = exc.problem_mark
                error_message = getattr(exc, "problem", str(exc))
                print(
                    f"{file_path} 解析失败: 行 {mark.line + 1}, 列 {mark.column + 1},{error_message}"
                )
            else:
                print(f"{file_path} 解析失败: {exc}")
            return
    try:
        jsonschema.validate(npk_data, npk_schema)
    except Exception as e:
        log = f"{file_path}： "
        mes = e.message
        if "is a required" in mes:
            if "owner" in mes or "version" in mes:
                print(log + f"{mes}")
            else:
                print(log + f"{mes}")
        elif "Additional properties are not allowed" in mes:
            print(log + f"{mes}")
        else:
            print(log + f"{mes}")


def validate_all(directory):
    isprint = False
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file in ("npk.yml", "npk_template.yml"):
                isprint = True
                file_path = os.path.join(root, file)
                validate_file(file_path)
    if isprint == False:
        print("错误：非npk组件包.")


def main():
    parser = argparse.ArgumentParser(description="NPK格式校验工具")
    parser.add_argument("path", help="要校验的npk.yml文件或目录路径")
    parser.add_argument("-log", "--logfile", help="结果写入文件路径")
    args = parser.parse_args()

    npk_path = args.path

    if os.path.isfile(npk_path) and npk_path.endswith(".yml"):
        validate_file(npk_path)
    elif os.path.isdir(npk_path):
        validate_all(npk_path)
    else:
        print(f"错误：'{npk_path}' 不是一个有效的目录或yml文件。 ")


if __name__ == "__main__":
    main()
