# Mascope Jupyter Widgets

This package provides interactive Jupyter widgets to construct data analysis notebooks for Mascope, utilizing [Mascope SDK](https://pypi.org/project/mascope_sdk/) to fetch data from the server.

See also [Mascope Tools](https://pypi.org/project/mascope_tools/) for extended analysis capabilities.

## 🚀 Getting started

### 1. Install Python

- Install [Python >= 3.12](https://www.python.org/downloads/).

### 2. Set up a virtual environment and install dependencies

When developing in Python, it is best practice to use [virtual environments](https://docs.python.org/3/library/venv.html) to
manage project dependencies. To set up a virtual environment for the project, in your terminal, run the following commands:

```sh
# initialize virtual environment
project-dir> python -m venv .venv
# activate the virtual environment
project-dir> .venv/Scripts/activate  # On Windows
project-dir> source .venv/bin/activate  # On Mac or Linux
# install dependencies
(.venv) project-dir> pip install mascope-jupyter-widgets jupyterlab
```

### 3. Configure Mascope access

To enable access from the notebook environment to your organization's Mascope instance, the following configuration steps need to be performed:

1. In the project directory, create an empty text file named `.env`.
2. In Mascope account settings, generate and copy a _Jupyter Notebooks_ access token.
3. Edit the `.env` file with the URL of your Mascope instance and your personal access token, as follows:

```sh
MASCOPE_URL="https://org.mascope.app"
MASCOPE_ACCESS_TOKEN="p3R5oN4l4cC35s70Ken"
```

### 4. Launch JupyterLab

[JupyterLab](https://jupyterlab.readthedocs.io/en/latest/#) is a popular notebook authoring and editing environment.

To run Jupyter Lab, you need to:

1. Open a terminal.
2. Navigate to the directory where your virtual environment is located.
3. Activate the virtual environment.
4. Launch JupyterLab.

```sh
# navigate to the source code directory
user> cd /path/to/project-dir
# activate the virtual environment
project-dir> .venv/Scripts/activate  # On Windows
project-dir> source .venv/bin/activate  # On Mac or Linux
# run jupyter lab
(.venv) project-dir> jupyter-lab
```

A browser window opens, with JupyterLab open. Now browse and open a notebook you wish to run and edit, or create a new one.

If you are not familiar with Jupyter Lab, we recommend starting from their [getting started tutorial](https://jupyterlab.readthedocs.io/en/stable/getting_started/overview.html).

## 📒 Examples

Below there are a few examples demonstrating how to load processed data from Mascope, and quick ways to visualize it. For more elaborate data visualization, you may have a look at for example [Plotly for Python](https://plotly.com/python/).

### Load data

To load data from Mascope, start with `MascopeDataBrowser`:

```
import mascope_jupyter_widgets as mjw

db = mjw.MascopeDataBrowser()
```

After loading, in the next cell, initialize a `MascopeDataWrapper` instance:

```
dataset = mjw.MascopeDataWrapper(db)
```

These two cells you would typically place at the beginning of your notebook. Now, you have easy access to many useful data properties.

> **NOTE:** When you load new data in the data browser, the dataset object gets automatically updated so you don't need to re-instantiate it.

### Target timeseries

To access intensities of all targets matched in Mascope, indexed by datetime, you may use the following dataset properties:

```
dataset.target_compound_timeseries
```

```
dataset.target_ion_timeseries
```

It is very easy to resample the data into different time resolution, for example to compute 1 hour means:

```
1h_timeseries = dataset.target_compound_timeseries.resample("1H").mean()
```

To see matched compositions, yoy may use e.g. `dataset.target_ion_timeseries.columns`. To access the timeseries of a specific target ion or compound, just select the corresponding column from the dataframe, e.g.

```
dataset.target_ion_timeseries['HSO4-']
```

### Peak data

If you have selected to `Import Peaks` when loading the data, you also have the property

```
dataset.peaks_matched
```

available, which contains all peaks of the loaded samples.

To get a quick glance of the peaks, you can for example visualize the, in a simple mass defect plot like this:

```
dataset.peaks_matched.plot(x="mz", y="mass_defect", kind="scatter")
```

### Match data

All the "match data" computed by Mascope are available as dataframes in the dataset object:

```
dataset.match_samples
dataset.match_compounds
dataset.match_ions
dataset.match_isotopes
```

> **NOTE:** The property `dataset.match_samples` contains all sample metadata from the loaded batches, including timestamps, filenames as well as other attributes.
