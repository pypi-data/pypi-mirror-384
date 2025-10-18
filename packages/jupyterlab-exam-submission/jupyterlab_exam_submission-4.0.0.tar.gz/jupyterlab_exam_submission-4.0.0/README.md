# `jupyterlab-exam-submission`: Automatically hide code and/or output cells after running them


I wanted to allow students to use jupyter-lite to write computational exams. For this I made some logic that allows students to upload their notebooks to an endpoint with a unique token. However, I did not want students to see the logic behind this so this extension automatically runs all code cells once and hides the ones tagged with `hide_code`. If the tag `hide_output` is used, the output of the cell is also hidden.

## Requirements

- JupyterLab >= 4.0.0

## Install

To install the extension, use Development install

Note: You will need NodeJS to build the extension package.

The `jlpm` command is JupyterLab's pinned version of
[yarn](https://yarnpkg.com/) that is installed with JupyterLab. You may use
`yarn` or `npm` in lieu of `jlpm` below.

```bash
# Clone the repo to your local environment
# Change directory to the jupyterlab_exam_submission directory
# Install package in development mode
pip install -e "."
# Link your development version of the extension with JupyterLab
jupyter labextension develop . --overwrite
# Rebuild extension Typescript source after making changes
jlpm build
```

You can watch the source directory and run JupyterLab at the same time in different terminals to watch for changes in the extension's source and automatically rebuild the extension.

```bash
# Watch the source directory in one terminal, automatically rebuilding when needed
jlpm watch
# Run JupyterLab in another terminal
jupyter lab
```

With the watch command running, every saved change will immediately be built locally and available in your running JupyterLab. Refresh JupyterLab to load the change in your browser (you may need to wait several seconds for the extension to be rebuilt).

By default, the `jlpm build` command generates the source maps for this extension to make it easier to debug using the browser dev tools. To also generate source maps for the JupyterLab core extensions, you can run the following command:

```bash
jupyter lab build --minimize=False
```

### Testing the extension

#### Frontend tests

This extension is using [Jest](https://jestjs.io/) for JavaScript code testing.

To execute them, execute:

```sh
jlpm
jlpm test
```



## Acknowledgements

Built on top of the excellent work by [OSSCAR Team](https://www.osscar.org) for their jupyterlab-exam-submission extension.


