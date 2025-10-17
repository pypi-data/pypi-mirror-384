# SuperCore

**Letest Version:** 1.7  
**Developer:** @NacDevs  
**Git Repo:** [GitHub](https://github.com/yuvrajmodz/SuperCore)

SuperCore is a Python CLI tool to easily create and start Supervisor-managed processes in Linux.

## Installation & Usage (Global)

```bash
pip install supercore --break-system-packages
supercore <command>
```

## Installation & Usage (Python VENV)

```bash
pip install supercore
python3 supercore <command>
```

## Usage Examples

```bash
supercore python3 app.py
python3 supercore python3 app.py
```

## Optional installation

```bash
sudo apt update -y
sudo apt install supervisor -y
```