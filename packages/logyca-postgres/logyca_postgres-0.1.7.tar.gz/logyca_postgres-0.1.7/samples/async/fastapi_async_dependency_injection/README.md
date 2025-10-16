# Project Documentation

## Testing the Python Code

Before running or testing the project, make sure all dependencies are installed.

### 1. Install Requirements

All required packages are listed in the `requirements.txt` file.  
You can install them manually with:

```bash
pip install -r requirements.txt
```

### 2. Automated Virtual Environment Setup

To simplify the testing process, the creation and configuration of the virtual environment (venv) has been automated using VS Code Tasks.

The configuration files are located in the `.vscode/` directory:

- tasks.json — Automates environment setup and cleanup.

- Creates a virtual environment `(venv)`.

- Deletes temporary or cache files.

- Can be run manually with the command:

```mathematica
Ctrl + Shift + P → Tasks: Run Task
```

### 3. Run in Debug Mode

Once the environment is set up, you can start debugging by pressing:

```mathematica
F5  →  Run and Debug
```

