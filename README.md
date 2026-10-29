# Gongxu-Lens · 供需透镜 v0

**作者与维护者：[Aisiweiyang](https://github.com/Aisiweiyang)**

一个探索再生材料供需匹配、采购组合与净减排核算的开源项目。

**当前处于 v0 开源维护阶段，最近一次代码更新为 2026-10-30 的输入可靠性修复。**
后续不定期更新，逐步完善功能、文档与使用体验。
欢迎反馈问题、提出建议或参与贡献。

[English](README.en.md) | 简体中文

![供需透镜演示界面](docs/e2e-shots/site-1440.png)

## 最近更新 · 2026-10-30

- **明确选择需求**：多条需求须用 `--demand-id` 指定；编号不存在时直接报错。
- **本地输入异常即停止**：文件不齐或结构错误时提示修正，避免误用虚构演示数据。
- **统一 CSV 校验**：命令行与工作台共用结构检查，支持 UTF-8 BOM，拒绝重复或空表头、缺列、行列数不齐和引号错误。
- **补全供给模板**：包含运输距离、含运费标记、收率及证据字段，便于填写实际输入。

本次更新聚焦输入与导入可靠性；正常输入的算法、核算口径与冻结数值保持不变。详情见 [变更日志](CHANGELOG.md)。

## 项目介绍

供需透镜尝试回答：现有的再生材料供给能否满足采购需求？如何组合不同批次，并看清成本、运输、证据缺口与环境收益之间的取舍？

当前以非食品接触类工业包装、周转制品中的再生 PP 颗粒替代原生 PP 为演示场景。
输入需求、供给批次与核算因子后，系统进行筛选、方案比较和情景核算，输出报告与决策护照。

项目使用 Python 3.12+、PyYAML 与 OR-Tools，支持本地离线计算和基于 SQLite 的试点工作台。

## 已有功能

- 供需筛选：区分“可比较 / 待核验 / 不符合”，缺少证据不会默认通过。
- 采购组合：比较成本、净减排与供给集中风险，支持断供压力测试。
- 情景核算：展示计算依据，支持因子区间与确定性扰动检查。
- 多需求撮合：对共享供给池生成匹配建议与建议单。
- 试点工作台：管理需求、供给、证据、预留和交付反馈，支持权限、审计与备份恢复。
- 结果导出：生成报告、离线仪表盘和 JSON 决策护照。

## 快速开始

安装 Python 3.12+，下载或克隆仓库，在项目目录中打开终端。

```bash
git clone https://github.com/Aisiweiyang/Gongxu-Lens.git
cd Gongxu-Lens
```

Windows PowerShell：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py --industry 再生PP --data-mode demo
.\.venv\Scripts\python.exe serve.py --port 8765
```

Linux/macOS：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run.py --industry 再生PP --data-mode demo
.venv/bin/python serve.py --port 8765
```

浏览器打开 `http://127.0.0.1:8765/` 查看演示。Windows 也可先运行 `安装环境.bat`，再运行 `启动演示网站.bat`。

若使用试点工作台，将最后一条命令中的 `serve.py` 替换为 `pilot/start_pilot.py`。
首次访问时初始化管理员账号，无默认密码。演示服务与工作台分别启动即可。

## 数据与验证

默认提供虚构演示数据。使用自己的数据时：

1. 新建 `data/input/`，从 [templates/](templates/) 复制 `material_supply.csv` 与 `material_demand.csv`，保留文件名和表头。
2. 将示例行替换为已核实的供给、需求与证据；供给中的 `distance_km`、`price_includes_freight`、`yield_pct` 等字段也需按实际资料填写。
3. 使用 `--data-mode local` 运行。需求文件包含多条记录时，必须用 `--demand-id` 指定其中一条；将下例的 `YOUR_DEMAND_ID` 替换为文件内的真实编号。

Windows PowerShell：

```powershell
.\.venv\Scripts\python.exe run.py --industry 再生PP --data-mode local --demand-id YOUR_DEMAND_ID
```

Linux/macOS：

```bash
.venv/bin/python run.py --industry 再生PP --data-mode local --demand-id YOUR_DEMAND_ID
```

| 数据模式 | 行为 |
|---|---|
| `demo` | 使用内置虚构数据，仅供演示。 |
| `local` | 读取两份本地 CSV；文件缺失、结构错误或需求编号不存在时停止。 |
| `auto`（默认） | 本地 CSV 优先；仅两份文件均不存在且未指定需求编号时使用演示数据。 |

CSV 使用 UTF-8 编码（支持 BOM），列名须非空且唯一，每行列数须与表头一致，含逗号的单元格应加双引号。工作台预览与正式导入使用相同校验；存在结构错误的批次不会写入数据库。
缺少价格、距离或因子时会标记待补证或不可计算，不用零代替。命令行每次分析一条需求；共享供给池的多需求撮合通过工作台使用。

使用虚拟环境中的 Python 安装 `requirements-test.txt`，再运行 `scripts/check_project.py`，可执行全量测试和独立核验。
2026-10-30 代码更新的已登记验收为 Linux Python 3.14 下 **303 项测试、63 个子测试通过，零跳过**，独立穷举核验覆盖 1 个演示案例与 6 组随机案例；Windows Python 3.12 验证了本次新增用例，详见 [变更日志](CHANGELOG.md)。
复验方法与平台限制见 [贡献指南](CONTRIBUTING.md)，初次开源的历史结果见 [验收记录](docs/开源准备验收-20261008.md)。

## 文档与维护

方法、部署与工程说明见 [文档索引](docs/INDEX.md)，更新记录见 [变更日志](CHANGELOG.md)。
**v0 是首个公开版本。** 历史文档中的 `v10`–`v27.1` 为开源前的内部迭代编号，算法与 Schema 另有各自版本号。
后续不定期更新和维护，暂无固定更新周期，具体变更以仓库记录为准。

## 使用边界

当前版本用于探索、演示与试点验证。演示数据与假设因子不能用于真实采购决策；净减排是给定边界下的情景估算，不能作为实测减排或碳抵消依据。
正式使用前需核实输入、检测报告、核算因子和商务条款。安全问题请按 [安全政策](SECURITY.md) 私密报告。

## 致谢

感谢 **秦仲远** 和 **杨笑墨** 在项目中的协助工作。

## 许可证

项目采用 [MIT 许可证](LICENSE)。第三方依赖与来源资料的许可见 [第三方声明](THIRD_PARTY_NOTICES.md)。
