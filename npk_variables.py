import argparse
import os
import yaml
import re


def get_valid_variables(npk_data: dict) -> set:
    valid_variables = set()
    if npk_data.get("setconfig") is not None and isinstance(
        npk_data["setconfig"], list
    ):
        for setconfig_entry in npk_data["setconfig"]:
            if "config" in setconfig_entry:
                valid_variables.add(f"{setconfig_entry['config']}")

    if npk_data.get("configuration") is not None:
        for config_key, config_value in npk_data["configuration"].items():
            valid_variables.add(config_key)

            if "choices" in config_value:
                for choice in config_value["choices"]:
                    for choice_key, choice_value in choice.items():
                        valid_variables.add(f"{config_key}.{choice_key}")

                    if "info" in choice and isinstance(choice["info"], list):
                        for info_entry in choice["info"]:
                            if "name" in info_entry:
                                valid_variables.add(
                                    f"{config_key}.info.{info_entry['name']}"
                                )

    return valid_variables


def _extract_used_variables(obj: dict, path: list, used_variables: set) -> None:
    for key, value in obj.items():
        if isinstance(value, str):
            used_variables.update(re.findall(r"\$\{(.+?)\}", value))
        elif isinstance(value, dict):
            _extract_used_variables(value, path + [key], used_variables)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    _extract_used_variables(item, path + [str(i)], used_variables)
                elif isinstance(item, str):
                    used_variables.update(re.findall(r"\$\{(.+?)\}", item))


def validate_variables_in_directory(directory_path: str) -> None:
    all_used_variables = set()
    all_valid_variables = set()

    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file == "npk.yml":
                file_path = os.path.join(root, file)
                with open(file_path, "r") as f:
                    try:
                        npk_data = yaml.safe_load(f)
                        used_variables = set()
                        _extract_used_variables(npk_data, [], used_variables)
                        all_used_variables.update(used_variables)

                        valid_variables = get_valid_variables(npk_data)
                        valid_variables.add("name")
                        all_valid_variables.update(valid_variables)
                    except:
                        pass

    invalid_variables = all_used_variables.difference(all_valid_variables)
    if invalid_variables:
        print(
            f"Directory '{directory_path}' contains invalid variables: {', '.join(invalid_variables)}"
        )


def main():
    parser = argparse.ArgumentParser(description="NPK格式校验工具")
    parser.add_argument("path", help="要校验的npk.yml文件或目录路径")
    parser.add_argument("-log", "--logfile", help="结果写入文件路径")
    args = parser.parse_args()

    npk_path = args.path
    if os.path.isfile(npk_path) and npk_path.endswith(".yml"):
        with open(npk_path, "r") as f:
            try:
                npk_data = yaml.safe_load(f)
                used_variables = set()
                _extract_used_variables(npk_data, [], used_variables)
                valid_variables = get_valid_variables(npk_data)
                valid_variables.add("name")
                invalid_variables = used_variables.difference(valid_variables)
                if invalid_variables:
                    print(
                        f"Directory '{npk_path}' contains invalid variables: {', '.join(invalid_variables)}"
                    )
            except:
                pass
    elif os.path.isdir(npk_path):
        validate_variables_in_directory(npk_path)
    else:
        print(f"错误：'{npk_path}' 不是一个有效的目录或yml文件。 ")


if __name__ == "__main__":
    main()
