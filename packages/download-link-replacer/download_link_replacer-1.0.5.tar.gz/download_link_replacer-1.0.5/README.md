# Sphinx extension: download link replacer

This sphinx extension allows you to replace the download links on the generated [Jupyter book](https://jupyterbook.org/en/stable/intro.html) pages.

You can control the download option of the book in two ways:
 - Disabling downloading using cell tags `disable-download-page`
 - Add / replace download link with custom link using sphinx-`download-link-replacer`

## 1. Disabling download
If you add `disable-download-page` as a cell tag to a cell in a python notebook, the download button ({fa}`download`) will disappear from the topright corner. The cell tag can be added to any code cell in the notebook. This function might be handy if your page includes code which you don't want the students to see. Be aware that this also removes the option to download a PDF of the page.

## 2. Add/replace download link
The download link {fa}`download` -->  {fa}`file`{guilabel}`.ipynb` can be replaced by using the following code in any markdown / notebook file:
````md
```{custom_download_link} <link_target>
:text: "Custom text"
:replace_default: "True"
```
````

Replace `<link_target>` with the download location. It can either be a remote link (`http`, `https`, or `ftp`), or a local path (relative to the location of the file containing the directive). Local files must be located within or below the source folder of the book (i.e. the folder containing `_config.yml`).

The `replace_default` key is optional. When set to `True`, the default download link will be replaced with the custom one. When set to `False`, the default download link will be kept, and the custom one will be added below it. If the key is not set, the default behavior is to add the link to the list, without changing the default one.

The directive can appear multiple times in a single file.

A potential application of this functionality is when creating a page in which students have to do some coding. Downloading the page allows the student to save their work and work with their local environment. However, the original source file might include code (jupyterbook formatting, widgets, answers) which is not necessary for students. You can make a copy of the notebook file without these elements and replace the {fa}`file`{guilabel}`.ipynb` link to this custom notebook file. Furthermore, you can add any additional data as an additional {fa}`file`{guilabel}`.zip` file. 

### 2.1. Installation
To install the Download-Link-Replacer follow these steps:

**Step 1: Install the Package**

Install the `download-link-replacer` package using `pip`:
```
pip install download-link-replacer
```

**Step 2: Add to `requirements.txt`**

Make sure that the package is included in your project's `requirements.txt` to track the dependency:
```
download-link-replacer
```

**Step 3: Enable in `_config.yml`**

In your `_config.yml` file, add the extension to the list of Sphinx extra extensions:
```
sphinx: 
    extra_extensions:
        - download-link-replacer
```

## Contribute
This tool's repository is stored on [GitHub](https://github.com/TeachBooks/Download-Link-Replace). The `README.md` of the branch `manual_docs` is also part of the [TeachBooks manual](https://teachbooks.io/manual/external/Download-Link-Replacer/README.html) as a submodule. If you'd like to contribute, you can create a fork and open a pull request on the [GitHub repository](https://github.com/TeachBooks/Download-Link-Replacer). To update the `README.md` shown in the TeachBooks manual, create a fork and open a merge request for the [GitHub repository of the manual](https://github.com/TeachBooks/manual). If you intent to clone the manual including its submodules, clone using: `git clone --recurse-submodulesgit@github.com:TeachBooks/manual.git`.
