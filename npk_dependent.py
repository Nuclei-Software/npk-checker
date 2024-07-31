import argparse
import sys
import os
import yaml
import json
from semantic_version import NpmSpec, Version

main_file = None


def check_package(npk_files):
    global main_file
    package_type = None
    component_order = ["tool", "sdk", "csp", "ssp", "bsp", "osp", "mwp", "bdp", "app"]
    for component in component_order:
        if any(file.type == component for file in npk_files):
            package_type = component
            break
    if package_type is None:
        print("错误提示：找不到有效的包类型。")
    else:
        package_type_files = [f for f in npk_files if f.type == package_type]
        if len(package_type_files) > 1:
            print(f"错误：组件包只能有一个主npk文件，该包存在多个{package_type}文件")
        else:
            main_file = package_type_files[0]

    ssp_files = [f for f in npk_files if f.type == "ssp"]
    bsp_files = [f for f in npk_files if f.type == "bsp"]
    app_files = [f for f in npk_files if f.type == "app"]

    if package_type == "sdk":
        if (
            not ssp_files
            or not any(
                bsp.depends_on_ssp(ssp_file)
                for bsp in bsp_files
                for ssp_file in ssp_files
            )
            or not app_files
        ):
            print(
                "不符合规范：sdk组件包至少包含一个ssp、一个依赖于该ssp的bsp以及至少一个app。"
            )

    elif package_type == "bdp":
        if len([f for f in npk_files if f.type == "bdp"]) != 1 or len(app_files) < 2:
            print("不符合规范：bdp组件包至少存在两个app.")

    elif package_type not in ["tool", "bdp", "sdk"]:
        main_files = [f for f in npk_files if f.type == package_type]
        if not all(app.depends_on_main(main_file) for app in app_files):
            print("不符合规范：非skd/bdp包必须对其主npk文件具有显式依赖关系。")
    return main_file


class NPKInfo:
    def __init__(self, type, data, path):
        self.type = type
        self.data = data
        self.name = data.get("name")
        self.version = data.get("version")
        self.owner = data.get("owner")
        self.dependencies = data.get("dependencies", [])
        self.os = data.get("os")

    def depends_on_ssp(self, ssp_file):
        ssp_name = None
        ssp_version = None
        ssp_owner = None
        if "name" in ssp_file.data:
            ssp_name = ssp_file.data["name"]
        if "version" in ssp_file.data:
            ssp_version = ssp_file.data["version"]
        if "owner" in ssp_file.data:
            ssp_owner = ssp_file.data["owner"]
        return any(
            dep.get("name") == ssp_name
            and (dep.get("version") is None or dep.get("version") == ssp_version)
            and (dep.get("owner") is None or dep.get("owner") == ssp_owner)
            for dep in self.dependencies
        )

    @staticmethod
    def depends_on_main(main_file):
        main_name = main_file.name
        main_version = main_file.version
        main_owner = main_file.owner
        return any(
            dep.get("name") == main_name
            and (not dep.get("version") or dep.get("version") == main_version)
            and (not dep.get("owner") or dep.get("owner") == main_owner)
            for dep in main_file.dependencies
        )


def get_all_npk_info(directory):
    npk_infos = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file == "npk.yml":
                file_path = os.path.join(root, file)
                with open(file_path, "r") as f:
                    try:
                        npk_data = yaml.safe_load(f)
                        npk_info = NPKInfo(npk_data.get("type"), npk_data, file_path)
                        npk_infos.append(npk_info)
                    except:
                        pass
    return npk_infos


def build_basic_info_set(npk_infos):
    basic_info_set = set()
    dependency_set = set()
    for npk_info in npk_infos:
        basic_data = (npk_info.name, npk_info.version or "", npk_info.owner or "")
        basic_info_set.add(basic_data)
        if npk_info.dependencies is not None:
            for dep in npk_info.dependencies:
                dep_data = (
                    dep.get("name"),
                    dep.get("version") or "",
                    dep.get("owner") or "",
                )
                dependency_set.add(dep_data)
    return basic_info_set, dependency_set


def satisfies_semver_range(version_range, version):
    spec = NpmSpec(version_range)
    return spec.match(Version.coerce(version))


def find_unmatched_dependencies(npk_infos):
    basic_info_set, dependency_set = build_basic_info_set(npk_infos)

    unmatched_dependencies = []
    for dependency in dependency_set:
        name, version, owner = dependency
        matching_elements = [
            info
            for info in basic_info_set
            if info[0] == name
            and (owner is None or owner == "" or info[2] is None or info[2] == owner)
        ]

        if not matching_elements:
            unmatched_dependencies.append(dependency)
            continue

        if all(
            version and not satisfies_semver_range(version, e[1])
            for e in matching_elements
        ):
            unmatched_dependencies.append(dependency)

    return unmatched_dependencies


def main():
    parser = argparse.ArgumentParser(description="NPK格式校验工具")
    parser.add_argument("path", help="要校验的npk.yml文件或目录路径")
    parser.add_argument("-log", "--logfile", help="结果写入文件路径")
    args = parser.parse_args()
    dep = ""

    npk_path = args.path

    if os.path.isfile(npk_path) and npk_path.endswith(".yml"):
        with open(npk_path, "r") as f:
            try:
                npk_data = yaml.safe_load(f)
                dependencies = npk_data.get("dependencies", [])
                if dependencies:
                    print(f"npk.yml 文件 '{npk_path}' 的依赖项如下:")
                    for dependency in dependencies:
                        dependency_info = f" 名称: {dependency.get('name', '未定义')}, 版本: {dependency.get('version', '未定义')}, 拥有者: {dependency.get('owner', '未定义')}"
                        print(dependency_info)
                else:
                    print(f"npk.yml 文件 '{npk_path}' 无依赖项.")
            except:
                pass
    elif os.path.isdir(npk_path):
        npk_infos = get_all_npk_info(npk_path)
        unmatched_deps = find_unmatched_dependencies(npk_infos)

        for dep_name, dep_version, dep_owner in unmatched_deps:
            dep = dep + f",  name:{dep_name} version:{dep_version} owner:{dep_owner}"
            print(
                f"未能找到匹配的npk文件：名称:{dep_name}, 版本:{dep_version}, 拥有者:{dep_owner}"
            )

        main_file = check_package(npk_infos)

        print(
            f"[NPKInfo],npkpacagename: {main_file.name},owner: {main_file.owner},version: {main_file.version},type: {main_file.type},os: {main_file.os},dependencies: {dep}"
        )
    else:
        print(f"错误：'{npk_path}' 不是一个有效的目录或yml文件。 ")


if __name__ == "__main__":
    main()
