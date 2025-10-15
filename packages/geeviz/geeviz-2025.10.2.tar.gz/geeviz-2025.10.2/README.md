# geeVizBuilder – Build Tools for the geeViz Python Package

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen)](https://github.com/gee-community/geeViz)

**[geeViz Documentation →](https://geeviz.org/)**

This repository provides tools to build, test, document, and release the [geeViz](https://geeviz.org/) Python package for interactive Earth Engine analysis.

---

## 🛠️ Development Setup

### 1. Prerequisites

- Python **3.9** or higher
- `pip`
- `git`


### 2. Clone Required Repositories

```bash
git clone https://github.com/redcastle-resources/geeVizBuilder
cd geeVizBuilder
git clone https://github.com/redcastle-resources/geeVizDocs
git clone https://github.com/redcastle-resources/geeViz
git clone https://github.com/redcastle-resources/lcms-viewer
```
Recommended folder structure:

```
geeVizBuilder/
│
├── geeVizDocs/
├── geeViz/
├── lcms-viewer/
└── venv/
```

### 3. Set Up Virtual Environment

```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 4. Install Package Dependencies

```bash
python -m pip install -r requirements.txt
```

### 5. Link geeViz Package for Local Development

To use the latest code from the local `geeViz` folder in your virtual environment, create a symbolic link (adjust path separators as needed):

- **Windows (PowerShell):**
    ```powershell
    Remove-Item .\venv\Lib\site-packages\geeViz -Recurse -Force
    New-Item -Path ".\venv\Lib\site-packages\geeViz" -ItemType SymbolicLink -Target "..\..\geeViz"
    ```
- **macOS/Linux:**
    ```bash
    rm -rf ./venv/lib/python*/site-packages/geeViz
    ln -s "$(pwd)/geeViz" ./venv/lib/python*/site-packages/geeViz
    ```

### 6. Update `geeViz.geeView` from LCMS Viewer

If you modify the LCMS framework in `lcms-viewer` and want changes in `geeViz.geeView`, run:

```bash
python ./lcms-viewer/buildgeeViz.py
```
After this, `Map.view()` in geeViz will reflect any changes. (Do a hard refresh/clear cache in your browser if needed.)

### 7. Build, Package, and Release geeViz

- **Update Version**: Increment `__version__` in `geeViz/__init__.py` and `geeViz/examples/__init__.py`.
- **Build and Upload to PyPI:**

    **Batch/Windows:**
    ```bash
    build.bat
    ```

    **Manual Steps:**
    ```bash
    rmdir build /s /q
    rmdir dist /s /q
    rmdir geeViz.egg-info /s /q
    python -m jupyter nbconvert --ClearOutputPreprocessor.enabled=True --inplace examples/*.ipynb
    python setup.py sdist bdist_wheel
    python -m twine upload dist/* --verbose
    ```

- **Commit and Push to GitHub:**
    ```bash
    cd geeViz
    git add .
    git commit -m "vYYYY.M.n release"
    git push origin master
    ```
    _To also push to the EE community fork:_
    ```bash
    git remote add ee-community https://github.com/gee-community/geeViz
    git push ee-community master
    ```

### 8. Build Documentation and Publish to [geeviz.org](https://geeviz.org/)

```bash
cd geeVizDocs
make html  # or .\make.bat html on Windows

git add .
git commit -m "vYYYY.M.n release"
git push origin main
```
Docs will auto-update [https://geeviz.org/](https://geeviz.org/) (allow a few minutes for propagation).

### 9. Sync with LCMS Viewer (Upstream)

The LCMS Viewer code (`lcms-viewer/`) is updated often. Keep your fork and geeViz in sync:

```bash
cd lcms-viewer
git add .
git commit -m "Describe your changes"
git push origin main
```

---

## 🤝 Contributing

Want to help improve geeViz? Great!

1. [Create or comment on issues](https://github.com/gee-community/geeViz/issues) to discuss relevant bugs or ideas.
2. Fork the repository.
3. Create a feature or bugfix branch.
4. Implement your changes & add tests.
5. Ensure all tests/build steps pass.
6. Submit a pull request with a clear description.

---

## 📄 License

This project is licensed under the [Apache 2.0 License](LICENSE).

---

## 📧 Contact & Support

- **Report Issues:** [https://github.com/gee-community/geeViz/issues](https://github.com/gee-community/geeViz/issues)
- **General Questions:** info@geeviz.org

---

