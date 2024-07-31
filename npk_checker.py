import argparse
import sys
import os
import zipfile
import importlib
import subprocess
import shutil
import hashlib
import math
from pathlib import Path
import time
import re

npk_info = None
type = True
any_missing = False

SCRIPTS_TO_RUN = [
    "npk_format.py",
    "npk_variables.py",
    "npk_function.py",
    "npk_dependent.py",
]

MODULES_TO_CHECK = [
    ('semantic_version', 'semantic-version'),
    ('yaml', 'PyYAML'),
    ('jsonschema', 'jsonschema')
]

class Logger:
    def __init__(self, filename=None):
        self.terminal = sys.stdout
        self.log = open(filename, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        # 调用flush确保所有输出都写入到文件
        self.terminal.flush()
        self.log.flush()

    def close(self):
        # 关闭文件
        self.log.close()

def check_module_installed(module_name,install_name):
    global any_missing
    try:
        importlib.import_module(module_name)
    except ImportError:
        print(f"{install_name} is NOT installed.")
        any_missing = True
        
def run_external_script(script_path, directory, logfile_path):
    global npk_info
    command = [sys.executable, script_path, directory]
    if logfile_path is not None:
        command.extend(["--logfile", logfile_path])
    process = subprocess.run(command, check=False, capture_output=True, text=True)
    out = process.stdout.strip().splitlines()
    if process.stderr is not None:
        print("Run %s failed: %s" % (script_path, process.stderr))
        type = False
    if out is not None and out != "":
        for line in out:
            if "[NPKInfo]" in line:
                num = line.find("[NPKInfo]")
                npk_info = line[num:].replace(",", "\n")
            elif line:
                if "_zip_" in line:
                    line = re.sub(r"_zip_.*?_zip_", "", line)
                print(line)


def zip_dir(dir_path, output_zip_path):
    dir_path = os.path.abspath(dir_path)

    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:

        for root, dirs, files in os.walk(dir_path):
            relative_root = os.path.relpath(root, start=dir_path)

            for filename in files:
                abs_path = os.path.join(root, filename)
                arcname = os.path.join(relative_root, filename)

                zipf.write(abs_path, arcname=arcname)


def format_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "{} {}".format(s, size_name[i])
    

def main():
    
    for module, install_name in MODULES_TO_CHECK:
        check_module_installed(module, install_name)
        
    if any_missing:
        print("Detected missing Python dependency libraries. Please install all required modules to proceed.")
        sys.exit(1) 
        
    parser = argparse.ArgumentParser(description="NPK组件包校验工具")
    parser.add_argument("path", help="要校验的目录或文件路径,文件只支持*.zip和*.yml")
    parser.add_argument("-log", "--logfile", help="结果写入文件路径")

    args = parser.parse_args()
    logfile_path = args.logfile
    if logfile_path is None:
        logfile_path = "npk_check.log"
    if os.path.exists(logfile_path):
        os.remove(logfile_path)
    sys.stdout = Logger(logfile_path)

    input_path = args.path
    if os.path.isabs(input_path):
        pass
    else:
        input_path = os.path.abspath(input_path)
    print("[NPKVerificationResult]")
    zipsize = None
    md5sum = None
    hash_object = hashlib.md5()

    if os.path.isfile(input_path):
        zipsize = format_size(os.stat(input_path).st_size)
        with open(input_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_object.update(chunk)
        md5sum = hash_object.hexdigest()
        if zipfile.is_zipfile(input_path):
            zipdir = Path(input_path).parent
            zipname = "_zip_" + str(time.time()) + "_zip_" + Path(input_path).name
            temp_dir = zipdir / zipname
            try:
                with zipfile.ZipFile(input_path, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)
                for script in SCRIPTS_TO_RUN:
                    run_external_script(script, temp_dir, logfile_path)
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
        elif input_path.endswith(".yml"):
            for script in SCRIPTS_TO_RUN:
                run_external_script(script, input_path, logfile_path)
        else:
            print(f"错误：'{input_path}' 不是一个有效的zip文件或yml文件!")
    elif os.path.isdir(input_path):
        for script in SCRIPTS_TO_RUN:
            run_external_script(script, input_path, logfile_path)
        if type:
            while True:
                logger_instance = (
                    sys.stdout
                )  # 假设 Logger 类有一个全局实例或者可以通过某种方式访问当前的实例
                sys.stdout = sys.__stdout__
                user_input = input("是否执行打包操作？(y/n,回车略过): ").strip().lower()
                sys.stdout = logger_instance  # 恢用回日志写入
                if user_input == "y":
                    zipdir = Path(input_path)
                    zippath = zipdir.parent / (zipdir.name + str(time.time()) + ".zip")
                    zip_dir(input_path, zippath)
                    print(f"打包完成，输出路径：{zippath}")
                    zipsize = format_size(os.stat(zippath).st_size)
                    hash_object = hashlib.md5()
                    with open(zippath, "rb") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hash_object.update(chunk)
                    md5sum = hash_object.hexdigest()
                    break
                elif user_input == "n" or not user_input:
                    pass
                    break
                else:
                    print("无效的输入，请输入'y'或'n'!")
    else:
        print(f"错误：'{input_path}' 不是一个有效的文件或目录!")

    if npk_info:
        print(f"{npk_info}\nzipsize: {zipsize}\nmd5sum: {md5sum}")


if __name__ == "__main__":
    main()
