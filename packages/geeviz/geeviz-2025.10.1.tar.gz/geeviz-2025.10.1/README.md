# geeVizBuilder - build the geeViz Python Package

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) <!-- Or choose your license -->
[![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen)]() <!-- Or Beta, Alpha, etc. -->

**[geeViz](https://geeviz.org/)**

This repository facilitates the build, packaging, and distribution of geeViz. 

## 🛠️ Setup/Development 

1.  **Prerequisites:**
    *   Python 3.9+
    *   pip
    *   git
2.  **Clone the Repositories:**
    ```bash
    git clone https://github.com/redcastle-resources/geeVizBuilder
    cd geeVizBuilder
    git clone https://github.com/redcastle-resources/geeVizDocs
    git clone https://github.com/redcastle-resources/geeViz
    git clone https://github.com/redcastle-resources/lcms-viewer

    ```
    
3.  **Set up Virtual Environment (inside geeVizBuilder folder):**
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

    * The folder structure should be:
    ```
    geeVizBuilder
    └───geeVizDocs
    │   │   ...
    │   
    └───geeViz
    │   │   ...
    │   
    └───lcms-viewer
    │   │   ...
    │   
    └───venv
        │   ...
     
    ``` 
4.  **Install Dependencies:**
    ```bash
    python -m pip install -r requirements.txt
    ```
5.  **Setup geeViz pseudo package in venv site packages:**
    * One way of having the latest change to the package be available for testing is by creating a symbolic link to the package folder:
    ```bash
    rm -r .\venv\Lib\site-packages\geeViz -Force
    ```
    or in Powershell
    ```bash
    ni ".\venv\Lib\site-packages\geeViz\" -i SymbolicLink -ta ".\geeViz\"
    ```
6.  **Update `geeViz.geeView`:**
    * Any changes made to the LCMS viewer framework can be integrated into `geeViz.geeView` by using the `buildgeeViz.py` script.
    ```bash
    python .\lcms-viewer\buildgeeViz.py
    ```
    * Now, any time you do a `Map.view()` call, the updated `geeViz.geeView` UI will appear. Sometimes you need to do a ctrl+F5 hard refresh of the browser.

7.  **Build and release `geeViz` to `https://pypi.org/project/geeviz/` and `github.com`:**
    * Update the `.\geeViz\__init__.py` and `.\geeViz\examples\__init__.py` with the next version (`YYYY.M.n`).
    * Run `build.bat` or:
    ```bash
    rmdir build /s /q
    rmdir dist /s /q
    rmdir geeViz.egg-info /s /q
    python -m jupyter nbconvert --ClearOutputPreprocessor.enabled=True --inplace examples/*.ipynb
    python setup.py sdist bdist_wheel
    python -m twine upload dist/* --verbose

    cd geeViz
    git add .
    git commit -m 'vYYYY.M.n release'
    git push origin master
    ```
    * You can also add the EE community repo and push there as well:
    ```bash
    git remote add ee-community https://github.com/gee-community/geeViz
    git push ee-community master
    ```

8.  **Build `geeViz` docs and publish to `https://geeviz.org/`:**
    * Use Sphinx `make.bat` to create documentation site.
    * Then push to `https://github.com/redcastle-resources/geeVizDocs`. This will automatically update `https://geeviz.org/` (sometimes CloudFlare takes some time to reflect changes, but it is usually quite fast)  
    ```bash
    cd geeVizDocs
    .\make.bat html
    
    git add .
    git commit -m 'vYYYY.M.n release'
    git push origin main
    ```

9.  **Sync LCMS Viewer Framework Changes:**
    * The LCMS Viewer Framework that `geeViz.geeView` runs on changes frequently. You should push and pull/merge changes frequently.
    ```bash
    cd lcms-viewer
   
    git add .
    git commit -m 'Brief description of what you changed'
    git push origin main
    ```
    

## 🤝 Contributing

We welcome contributions! If you'd like to help improve geeViz, please:

1.  **Check for open issues** or open a new issue to discuss proposed changes.
2.  **Fork the repository.**
3.  **Create a new branch** for your feature or bug fix.
4.  **Make your changes** and add tests if applicable.
5.  **Ensure tests pass.**
6.  **Submit a pull request** with a clear description of your changes.


## 📄 License

This project is licensed under the Apache 2.0 License - see the `LICENSE` file for details.

## 📧 Contact & Support

*   **Report Issues:** https://github.com/gee-community/geeViz/issues
*   **General Questions:** info@geeviz.org

---

