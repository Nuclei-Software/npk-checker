
# 功能概述

本组件检查工具旨在自动化评估和确保代码质量，其核心功能聚焦于代码风格、变量命名、函数结构以及依赖关系的合规性检查，专为检测npk组件包的合法性而设计。  
该工具兼容**Python 3.11.1**环境。

关于 `NPK`的设计文档目前请参见: https://github.com/Nuclei-Software/nuclei-sdk/wiki/Nuclei-Studio-NPK-Introduction

## 必需的第三方库

为了启用此工具的所有特性，您需要确保以下第三方库已被安装：

- `semantic-version`: 用于语义化版本号的解析与比较。
- `PyYAML`: 支持YAML格式文件的读取与解析。
- `jsonschema`: 实现JSON Schema的验证功能，确保数据结构的一致性与完整性。

## 安装指导

在您的项目目录中打开终端，执行以下命令以安装必需的第三方库：

```shell
# 如果你有python3的环境，这里pip可能需要换成 pip3
pip install semantic-version PyYAML jsonschema
```

## 使用指南

### 启动检查

运行检查工具，只需指定目标目录或ZIP文件的路径，工具将自动分析其中的组件包，评估其编码风格与规范遵守情况。

```shell
python npk_checker.py <目录路径或zip文件路径>
```

- `<目录路径或zip文件路径>`: 指定待检查的组件包所在目录或压缩包的完整路径。

### 示例

假设您的项目位于 `~/projects/my_project` 目录下，您希望检查名为 `my_component` 的子目录，命令如下：

```shell
cd ~/projects/my_project
python npk_checker.py ./my_component
```

或者，若组件以ZIP格式打包，存放于同一目录下，检查流程同样简洁：

```shell
python npk_checker.py ./my_component.zip
```

返回内容说明：

`[NPKVerificationResult]` 包含脚本检测到的各种警告或错误信息，
`[NPKInfo]` 为所检测组件包的包信息。下面以**sdk-n100_sdk**为例。

```
C:\nuclei-studio-ci\npk_pacakge_verification_tool>python npk_checker.py C:\Users\chendong\nuclei-pack-npk-v2\NPKs\nuclei\Software_Development_Kit\sdk-n100_sdk\0.1.0

[NPKVerificationResult]
C:\Users\chendong\nuclei-pack-npk-v2\NPKs\nuclei\Software_Development_Kit\sdk-n100_sdk\0.1.0\nuclei-sdk-n100-0.1.0\SoC\evalsoc\Board\nuclei_fpga_eval\npk.yml： 'version' is a required property
C:\Users\chendong\nuclei-pack-npk-v2\NPKs\nuclei\Software_Development_Kit\sdk-n100_sdk\0.1.0\nuclei-sdk-n100-0.1.0\SoC\evalsoc\Common\npk.yml： 'version' is a required property
Directory 'C:\Users\chendong\nuclei-pack-npk-v2\NPKs\nuclei\Software_Development_Kit\sdk-n100_sdk\0.1.0' contains invalid variables: workspace_loc:/${ProjName
未能找到匹配的npk文件：名称:sdk-nuclei_sdk, 版本:, 拥有者:
是否执行打包操作？(y/n,回车略过): n
[NPKInfo]
npkpacagename: sdk-n100_sdk
owner: nuclei
version: 0.1.0
type: sdk
os: None
dependencies:
  name:sdk-nuclei_sdk version: owner:
zipsize: None
md5sum: None
```