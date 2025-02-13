# Digital Forensics Triage Tool

A lightweight digital forensics triage tool designed for quick initial analysis of directories and files. This tool collects metadata, calculates file hashes, and provides a structured report of findings.

## Features

- Fast directory scanning with metadata collection
- SHA-256 hash calculation for files
- Detailed logging of all operations
- JSON output format for easy parsing
- Configurable file size limits for hash calculation
- Error handling and reporting

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/DFT-Tool.git
cd DFT-Tool
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Basic usage:
```bash
python backend/forensics_triage_tool.py /path/to/scan
```

With options:
```bash
python backend/forensics_triage_tool.py /path/to/scan --output-dir ./my_results --max-file-size 1000000
```

### Command Line Options

- `directory`: Required. The directory to scan
- `--output-dir`: Optional. Directory for output files (default: ./forensics_output)
- `--max-file-size`: Optional. Maximum file size in bytes for hash calculation

## Output

The tool generates:
1. A JSON file containing scan results with:
   - File paths
   - File sizes
   - Creation, modification, and access timestamps
   - SHA-256 hashes (for files under the size limit)
   - Any errors encountered

2. A log file with detailed information about the scan process

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## CLI Commands

- **Run the Application**:
  ```sh
  python backend/forensics_triage_tool.py
  ```

- **Run Tests**:
  ```sh
  python -m pytest --maxfail=1 --disable-warnings -q
  ```

- **Run Benchmark**:
  ```sh
  python benchmark/benchmark_dft.py
  ```
