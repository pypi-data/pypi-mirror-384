# Abstract IDE

[![PyPI version](https://badge.fury.io/py/abstract-ide.svg)](https://badge.fury.io/py/abstract-ide)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)

**Abstract IDE** is a modular, extensible Python-based Integrated Development Environment (IDE) toolset designed for developers working with web projects, particularly React/TypeScript applications. It provides a graphical user interface (GUI) built with PyQt for code analysis, import graphing, content searching, build automation, and more. The tool leverages background workers for non-blocking operations and integrates with external utilities for tasks like code searching, API testing, and file management.

This project is part of a larger ecosystem of "abstract" modules (e.g., `abstract_paths`, `abstract_apis`) and is ideal for analyzing large codebases, debugging builds, and automating repetitive development tasks.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Features

Abstract IDE offers a tabbed GUI interface with the following core functionalities:

- **Runner Tab**: Execute TypeScript compilation (`tsc`) and React builds (`yarn build`) locally or via SSH. Displays errors and warnings with clickable links to open files in VS Code. Supports ANSI stripping, severity filtering, and alternate file extension resolution (e.g., `.ts` ↔ `.tsx`).

- **Functions Map Tab**: Scans the project for import/export graphs, displaying functions as interactive buttons. Filter by name, view exporters/importers, and open files directly. Supports "all" or "reachable" scopes with customizable entry points (e.g., `index.tsx`, `main.tsx`).

![Functions Map Tab](docs/images/functions_map.png)

- **Find Content Tab**: Advanced code search across directories. Supports recursive searches, string matching (partial or exact), file extensions, path filters, and line-specific queries. Results are clickable for editing in VS Code.

![Find Content Tab](docs/images/find_content.png)

- **API Client Tab**: A console for testing APIs with dynamic endpoints, headers, and parameters. Fetches remote endpoints from `/api/endpoints` and supports GET/POST methods.

![API Client Tab](docs/images/api_client.png)

- **ClipIt Tab**: Drag-and-drop file browser with clipboard integration for quick file operations.

![ClipIt Tab](docs/images/clipit.png)

- **Window Manager Tab**: Manages multiple windows and layouts within the IDE.

- **Directory Map Tab**: Generates a visual tree map of the project directory, with filters for extensions, types, and patterns.

![Directory Map Tab](docs/images/directory_map.png)

- **Collect Files Tab**: Collects and lists files based on criteria like extensions and paths, with options to open all in VS Code.

![Collect Files Tab](docs/images/collect_files.png)

- **Extract Python Imports Tab**: Scans Python files for imports and module paths, displaying them in a readable format.

![Extract Python Imports Tab](docs/images/extract_imports.png)

Additional tools (integrated via workers):
- Code execution in a REPL-like environment with pre-installed libraries (e.g., NumPy, SciPy, PyTorch).
- Web browsing, searching, and snippet extraction.
- X (Twitter) post searching (keyword, semantic, user, threads).
- Image/PDF viewing and searching.
- Render components for inline citations.

The IDE uses multi-threading (QThread) for background tasks to keep the UI responsive.

## Installation

### Prerequisites
- Python 3.8+
- Git (for cloning the repository)

### From PyPI
```bash
pip install abstract-ide
```

### From Source
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/abstract-ide.git
   cd abstract-ide
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   (Or use the list from `abstract_ide.egg-info/requires.txt`.)

3. Run the IDE:
   ```bash
   python -m abstract_ide
   ```

## Usage

Launch the application:
```bash
python -m abstract_ide
```

### Basic Workflow
1. **Set Project Path**: In the Runner tab, enter the project directory (e.g., `/path/to/react-app`).
2. **Run Build**: Click "Run" to compile and build. Errors/warnings appear in lists—click to view snippets or open in editor.
3. **Map Functions**: Switch to Functions Map tab, select scope ("all" or "reachable"), and scan. Filter functions and inspect imports/exports.
4. **Search Code**: In Find Content tab, specify directory, strings (comma-separated), extensions, and flags. Results are listed for quick navigation.
5. **Test APIs**: In API Client tab, select base URL, fetch endpoints, add headers/params, and send requests.
6. **Advanced**: Use workers for background tasks like web searches or PDF analysis via function calls (see [Tools](#tools)).

### Keyboard Shortcuts
- Double-click list items: Open in VS Code.
- Filter radios: Toggle error/warning views dynamically.

### Example: Analyzing a React Project
- Load `/var/www/html/clownworld/bolshevid` (as in the sample import graph).
- Scan functions: View exports like `getIps`, `fetchMedia`, and their importers/exporters.
- Search for "useState": Find all occurrences in `.tsx` files recursively.

## Configuration

- **Import Graph**: Generated via `create_import_maps()` and stored as `import-graph.json` and `graph.dot` in `/data/import_tools/`.
- **Custom Entries**: Override entry points (e.g., `index.tsx`) in the Functions Map tab.
- **Extensions**: Configurable via UI inputs (e.g., comma-separated lists).
- **SSH Builds**: Specify `user@host` for remote execution.

Customize via environment variables:
- `BASE_DIRECTORY`: Default project root (e.g., `/var/www/html/clownworld/bolshevid`).

## Dependencies

From `abstract_ide.egg-info/requires.txt`:
- abstract_apis
- PyQt5 (or PyQt6)
- abstract_webtools
- abstract_utilities
- abstract_gui
- pydot
- abstract_clipit
- flask
- abstract_paths

Install via `pip install -r requirements.txt`.

## Project Structure

```
├── Docs/
├── README.md
├── finditGUI.py
├── logs/
├── pyproject.toml
├── setup.cfg
├── setup.py
├── src/
│   └── abstract_ide/
│       ├── console_utils/
│       │   ├── collapsable_log_panel.py
│       │   ├── consoleBase.py
│       │   ├── ensure_resizable.py
│       │   ├── initFuncsCall.py
│       │   ├── log_manager.py
│       │   ├── startConsole.py
│       │   └── worker_scans.py
│       ├── consoles/
│       │   ├── apiTab/
│       │   │   ├── _build_ui.py
│       │   │   ├── functions/
│       │   │   │   ├── base_utils.py
│       │   │   │   ├── build_ui.py
│       │   │   │   ├── collect_utils.py
│       │   │   │   ├── combo_utils.py
│       │   │   │   ├── endpoint_utils.py
│       │   │   │   ├── fetch_utils.py
│       │   │   │   ├── http_helpers.py
│       │   │   │   ├── imports.py
│       │   │   │   ├── logging_utils.py
│       │   │   │   ├── pyproject.toml
│       │   │   │   ├── request_utils.py
│       │   │   │   └── row_utils.py
│       │   │   ├── getFnames.py
│       │   │   ├── imports/
│       │   │   │   ├── constants.py
│       │   │   │   └── imports.py
│       │   │   ├── initFuncs.py
│       │   │   └── main.py
│       │   ├── appRunnerTab/
│       │   │   ├── functions/
│       │   │   │   └── core_utils.py
│       │   │   ├── getLines.py
│       │   │   ├── imports.py
│       │   │   ├── initFuncs.py
│       │   │   └── main.py
│       │   ├── clipitTab/
│       │   │   ├── FileDropArea/
│       │   │   │   ├── functions/
│       │   │   │   │   ├── directory_utils.py
│       │   │   │   │   ├── python_utils.py
│       │   │   │   │   ├── rebuild_utils.py
│       │   │   │   │   └── view_utils.py
│       │   │   │   ├── imports.py
│       │   │   │   ├── initFuncs.py
│       │   │   │   └── main.py
│       │   │   ├── FileSystemTree/
│       │   │   │   ├── functions/
│       │   │   │   │   └── text_utils.py
│       │   │   │   ├── imports.py
│       │   │   │   ├── initFuncs.py
│       │   │   │   └── main.py
│       │   │   ├── JSBridge/
│       │   │   │   └── JSBridge.py
│       │   │   ├── clipitTab/
│       │   │   │   ├── functions/
│       │   │   │   │   └── drop_utils.py
│       │   │   │   ├── getFnames.py
│       │   │   │   ├── imports.py
│       │   │   │   ├── initFuncs.py
│       │   │   │   └── main.py
│       │   │   ├── imports/
│       │   │   │   ├── imports.py
│       │   │   │   ├── qt_funcs.py
│       │   │   │   └── utils.py
│       │   │   ├── imports.py
│       │   │   ├── initFuncs.py
│       │   │   ├── main.py
│       │   │   └── utils/
│       │   │       └── read_utils.py
│       │   ├── finderTab/
│       │   │   ├── imports/
│       │   │   ├── main.py
│       │   │   └── tabs/
│       │   │       ├── collectFilesTab/
│       │   │       │   ├── functions.py
│       │   │       │   ├── initFuncs.py
│       │   │       │   └── main.py
│       │   │       ├── diffParserTab/
│       │   │       │   ├── functions/
│       │   │       │   │   ├── edit_funcs.py
│       │   │       │   │   ├── files_funcs.py
│       │   │       │   │   ├── getkeys.py
│       │   │       │   │   └── select_funcs.py
│       │   │       │   ├── imports.py
│       │   │       │   ├── initFuncs.py
│       │   │       │   └── main.py
│       │   │       ├── directoryMapTab/
│       │   │       │   ├── functions.py
│       │   │       │   ├── initFuncs.py
│       │   │       │   └── main.py
│       │   │       ├── extractImportsTab/
│       │   │       │   ├── functions.py
│       │   │       │   ├── initFuncs.py
│       │   │       │   └── main.py
│       │   │       ├── finderTab/
│       │   │       │   ├── functions.py
│       │   │       │   ├── initFuncs.py
│       │   │       │   └── main.py
│       │   │       ├── getFnames.py
│       │   │       ├── imports.py
│       │   │       └── testTab/
│       │   │           ├── functions.py
│       │   │           ├── initFuncs.py
│       │   │           └── main.py
│       │   ├── imageTab/
│       │   │   ├── imports/
│       │   │   │   ├── functions.py
│       │   │   │   ├── green_screen_delimiter/
│       │   │   │   │   ├── compare_screens.py
│       │   │   │   │   ├── detect_allgreen.py
│       │   │   │   │   ├── detect_green_screen_blur.py
│       │   │   │   │   ├── get_new_imagepath.py
│       │   │   │   │   └── utils.py
│       │   │   │   └── imports.py
│       │   │   └── main.py
│       │   ├── imports/
│       │   ├── launcherWindowTab/
│       │   │   ├── functions/
│       │   │   │   └── core_utils.py
│       │   │   ├── imports.py
│       │   │   ├── initFuncs.py
│       │   │   └── main.py
│       │   ├── logPaneTab/
│       │   │   ├── functions/
│       │   │   │   └── core_utils.py
│       │   │   ├── imports.py
│       │   │   ├── initFuncs.py
│       │   │   └── main.py
│       │   ├── main.py
│       │   ├── reactRunnerTab/
│       │   │   ├── functionsTab/
│       │   │   │   ├── flowLayout/
│       │   │   │   │   ├── functions/
│       │   │   │   │   │   └── function_utils.py
│       │   │   │   │   ├── imports.py
│       │   │   │   │   ├── initFuncs.py
│       │   │   │   │   └── main.py
│       │   │   │   ├── functionsTab/
│       │   │   │   │   ├── functions/
│       │   │   │   │   │   ├── build_ui.py
│       │   │   │   │   │   ├── filter_utils.py
│       │   │   │   │   │   ├── function_utils.py
│       │   │   │   │   │   ├── init_yabs_creator.py
│       │   │   │   │   │   ├── log_utils.py
│       │   │   │   │   │   └── variable_filter_utils.py
│       │   │   │   │   ├── imports.py
│       │   │   │   │   ├── initFuncs.py
│       │   │   │   │   └── main.py
│       │   │   │   ├── getFnames.py
│       │   │   │   ├── imports.py
│       │   │   │   └── main.py
│       │   │   ├── imports/
│       │   │   ├── main.py
│       │   │   └── runnerTab/
│       │   │       ├── functions/
│       │   │       │   ├── action_utils.py
│       │   │       │   ├── analyser.py
│       │   │       │   ├── clickHandlers_utils.py
│       │   │       │   ├── edit_utils.py
│       │   │       │   ├── helper_utils.py
│       │   │       │   ├── highlight_utils.py
│       │   │       │   ├── init_dict_panel.py
│       │   │       │   ├── init_split_edit.py
│       │   │       │   ├── init_trees.py
│       │   │       │   ├── initialize_init.py
│       │   │       │   ├── logEntries_utils.py
│       │   │       │   └── warning_utils.py
│       │   │       ├── imports.py
│       │   │       ├── initFuncs.py
│       │   │       └── main.py
│       │   ├── start_gui.py
│       │   └── windowManagerTab/
│       │       ├── functions/
│       │       │   ├── build_ui.py
│       │       │   ├── command_utils.py
│       │       │   ├── core_utils.py
│       │       │   ├── file_utils.py
│       │       │   ├── update_utils.py
│       │       │   └── wmctrl_utils.py
│       │       ├── getFnames.py
│       │       ├── imports/
│       │       │   ├── functions.py
│       │       │   └── imports.py
│       │       ├── initFuncs.py
│       │       └── main.py
│       ├── logTab/
│       │   ├── functions/
│       │   │   └── toggle_funcs.py
│       │   ├── imports.py
│       │   ├── initFuncs.py
│       │   └── main.py
│       └── test_gui.py
└── test/
    ├── finditGUI.py
    ├── get_all_import_classes.py
    ├── separate.py
    ├── spliceerrs.py
    ├── test_consoles.py
    └── testit.py
```

- **utils/managers**: Core GUI logic and workers.
- **utils/imports**: Import graphing and utilities.
- **utils/widgets**: Reusable Qt widget helpers.

To integrate the provided screenshots into this README:

1. **Save the Screenshots**: Download or capture the screenshots and save them in a dedicated folder, e.g., `docs/images/`. Name them descriptively:
   - `directory_map.png`
   - `find_content.png`
   - `clipit.png`
   - `extract_imports.png`
   - `api_client.png`
   - `functions_map.png`
   - `collect_files.png`

2. **Update the README**: Insert the Markdown image syntax under the relevant feature descriptions, as shown above (e.g., `![Directory Map Tab](docs/images/directory_map.png)`). Ensure the path is relative to the README file.

3. **Commit and Push**: Add the images to your Git repo and push the changes. This will make them visible on GitHub or other hosts.

If the screenshots need processing (e.g., cropping, annotations), use tools like ImageMagick or online editors before adding.

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/new-tool`.
3. Commit changes: `git commit -am 'Add new tool'`.
4. Push: `git push origin feature/new-tool`.
5. Submit a Pull Request.

Report issues via GitHub Issues.

## License

MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgments

- Built with PyQt for cross-platform GUI.
- Integrates with `pydot` for graph visualization.
- Thanks to xAI for inspiration in tool integration.