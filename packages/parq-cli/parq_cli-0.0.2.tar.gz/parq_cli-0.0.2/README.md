# parq-cli

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

一个强大的 Apache Parquet 文件命令行工具 🚀

## ✨ 特性

- 📊 **元数据查看**: 快速查看 Parquet 文件的元数据信息（行数、列数、文件大小、压缩类型等）
- 📋 **Schema 展示**: 美观地展示文件的列结构和数据类型
- 👀 **数据预览**: 支持查看文件的前 N 行或后 N 行
- 🔢 **行数统计**: 快速获取文件的总行数
- 🗜️ **压缩信息**: 显示文件压缩类型和文件大小
- 🎨 **美观输出**: 使用 Rich 库提供彩色、格式化的终端输出
- 📦 **智能显示**: 自动检测嵌套结构，显示逻辑列数和物理列数

## 📦 安装

### 从源码安装

```bash
git clone https://github.com/yourusername/parq-cli.git
cd parq-cli
pip install -e .
```

### 使用 pip 安装（即将支持）

```bash
pip install parq-cli
```

## 🚀 快速开始

### 基本用法

```bash
# 查看文件元数据
parq data.parquet

# 显示 schema 信息
parq data.parquet --schema

# 显示前 10 行
parq data.parquet --head 10

# 显示后 5 行
parq data.parquet --tail 5

# 显示总行数
parq data.parquet --count
```

### 组合使用

```bash
# 同时显示 schema 和行数
parq data.parquet --schema --count

# 显示前 5 行和 schema
parq data.parquet --head 5 --schema
```

## 📖 命令参考

### 主命令

```
parq FILE [OPTIONS]
```

**参数:**
- `FILE`: Parquet 文件路径（必需）

**选项:**
- `--schema, -s`: 显示 schema 信息
- `--head N`: 显示前 N 行
- `--tail N`: 显示后 N 行
- `--count, -c`: 显示总行数
- `--version, -v`: 显示版本信息
- `--help`: 显示帮助信息

## 🎨 输出示例

### 元数据展示

**普通文件（无嵌套结构）：**

```bash
$ parq data.parquet
```

```
╭─────────────────────── 📊 Parquet File Metadata ───────────────────────╮
│ file_path: data.parquet                                                │
│ num_rows: 1000                                                         │
│ num_columns: 5 (logical)                                               │
│ file_size: 123.45 KB                                                   │
│ compression: SNAPPY                                                    │
│ num_row_groups: 1                                                      │
│ format_version: 2.6                                                    │
│ serialized_size: 126412                                                │
│ created_by: parquet-cpp-arrow version 18.0.0                          │
╰────────────────────────────────────────────────────────────────────────╯
```

**嵌套结构文件（显示物理列数）：**

```bash
$ parq nested.parquet
```

```
╭─────────────────────── 📊 Parquet File Metadata ───────────────────────╮
│ file_path: nested.parquet                                              │
│ num_rows: 500                                                          │
│ num_columns: 3 (logical)                                               │
│ num_physical_columns: 8 (storage)                                      │
│ file_size: 2.34 MB                                                     │
│ compression: ZSTD                                                      │
│ num_row_groups: 2                                                      │
│ format_version: 2.6                                                    │
│ serialized_size: 2451789                                               │
│ created_by: parquet-cpp-arrow version 21.0.0                          │
╰────────────────────────────────────────────────────────────────────────╯
```

### Schema 展示

```bash
$ parq data.parquet --schema
```

```
                    📋 Schema Information
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Column Name ┃ Data Type     ┃ Nullable ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ id          │ int64         │ ✗        │
│ name        │ string        │ ✓        │
│ age         │ int64         │ ✓        │
│ city        │ string        │ ✓        │
│ salary      │ double        │ ✓        │
└─────────────┴───────────────┴──────────┘
```

## 🛠️ 技术栈

- **[PyArrow](https://arrow.apache.org/docs/python/)**: 高性能的 Parquet 读取引擎
- **[Typer](https://typer.tiangolo.com/)**: 现代化的 CLI 框架
- **[Rich](https://rich.readthedocs.io/)**: 美观的终端输出

## 🧪 开发

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest
```

### 运行测试（带覆盖率）

```bash
pytest --cov=parq --cov-report=html
```

### 代码格式化和检查

```bash
# 使用 Ruff 检查和自动修复

ruff check --fix parq tests
```

## 🗺️ 路线图

- [x] 基础元数据查看
- [x] Schema 展示
- [x] 数据预览（head/tail）
- [x] 行数统计
- [x] 文件大小和压缩信息显示
- [x] 嵌套结构智能识别（逻辑列数 vs 物理列数）
- [ ] SQL 查询支持
- [ ] 数据统计分析
- [ ] 格式转换（CSV, JSON, Excel）
- [ ] 文件对比
- [ ] 云存储支持（S3, GCS, Azure）

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- 灵感来源于 [parquet-cli](https://github.com/chhantyal/parquet-cli)
- 感谢 Apache Arrow 团队提供强大的 Parquet 支持
- 感谢 Rich 库为终端输出增添色彩

## 📮 联系方式

- 作者: Jinfeng Sun
- 项目地址: https://github.com/Tendo33/parq-cli

---

**⭐ 如果这个项目对你有帮助，请给个 Star！**
