# parq-cli

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A powerful command-line tool for Apache Parquet files 🚀

[简体中文](README.md) | English

## ✨ Features

- 📊 **Metadata Viewing**: Quickly view Parquet file metadata (row count, column count, file size, compression type, etc.)
- 📋 **Schema Display**: Beautifully display file column structure and data types
- 👀 **Data Preview**: Support viewing the first N rows or last N rows of a file
- 🔢 **Row Count**: Quickly get the total number of rows in a file
- 🗜️ **Compression Info**: Display file compression type and file size
- 🎨 **Beautiful Output**: Use Rich library for colorful, formatted terminal output
- 📦 **Smart Display**: Automatically detect nested structures, showing logical and physical column counts

## 📦 Installation

### Install from Source

```bash
git clone https://github.com/yourusername/parq-cli.git
cd parq-cli
pip install -e .
```

### Install via pip (Coming Soon)

```bash
pip install parq-cli
```

## 🚀 Quick Start

### Basic Usage

```bash
# View file metadata
parq meta data.parquet

# Display schema information
parq schema data.parquet

# Display first 5 rows (default)
parq head data.parquet

# Display first 10 rows
parq head -n 10 data.parquet

# Display last 5 rows (default)
parq tail data.parquet

# Display last 20 rows
parq tail -n 20 data.parquet

# Display total row count
parq count data.parquet
```

## 📖 Command Reference

### View Metadata

```bash
parq meta FILE
```

Display Parquet file metadata (row count, column count, file size, compression type, etc.).

### View Schema

```bash
parq schema FILE
```

Display the column structure and data types of a Parquet file.

### Preview Data

```bash
# Display first N rows (default 5)
parq head FILE
parq head -n N FILE

# Display last N rows (default 5)
parq tail FILE
parq tail -n N FILE
```

### Statistics

```bash
# Display total row count
parq count FILE
```

### Global Options

- `--version, -v`: Display version information
- `--help`: Display help information

## 🎨 Output Examples

### Metadata Display

**Regular File (No Nested Structure):**

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

**Nested Structure File (Shows Physical Column Count):**

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

### Schema Display

```bash
$ parq schema data.parquet
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

## 🛠️ Tech Stack

- **[PyArrow](https://arrow.apache.org/docs/python/)**: High-performance Parquet reading engine
- **[Typer](https://typer.tiangolo.com/)**: Modern CLI framework
- **[Rich](https://rich.readthedocs.io/)**: Beautiful terminal output

## 🧪 Development

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Run Tests (With Coverage)

```bash
pytest --cov=parq --cov-report=html
```

### Code Formatting and Checking

```bash
# Check and auto-fix with Ruff

ruff check --fix parq tests
```

## 🗺️ Roadmap

- [x] Basic metadata viewing
- [x] Schema display
- [x] Data preview (head/tail)
- [x] Row count statistics
- [x] File size and compression information display
- [x] Nested structure smart detection (logical vs physical column count)
- [ ] SQL query support
- [ ] Data statistical analysis
- [ ] Format conversion (CSV, JSON, Excel)
- [ ] File comparison
- [ ] Cloud storage support (S3, GCS, Azure)

## 🤝 Contributing

Issues and Pull Requests are welcome!

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- Inspired by [parquet-cli](https://github.com/chhantyal/parquet-cli)
- Thanks to the Apache Arrow team for powerful Parquet support
- Thanks to the Rich library for adding color to terminal output

## 📮 Contact

- Author: Jinfeng Sun
- Project URL: https://github.com/Tendo33/parq-cli

---

**⭐ If this project helps you, please give it a Star!**

