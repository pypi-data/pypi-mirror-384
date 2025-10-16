# ZynAMon

## Synopsis

This project hosts a Python package of same name (see below) as well as a collection of useful applications to **work with arbitrary time-series data** (i.e. both regularly sampled as well as event-type logs). Besides import/export functionalities for a mass conversion of data, an "Explorer GUI" built on the famous ```plotly``` and ```streamlit``` packages is provided for an intuitive analysis of trend data.

## Tools

All tools are accessible via a single application script, bundling the following command line tools:

```py app.py importer``` -> bulk import/conversion of CSV files into collection files

```py app.py compresser``` -> pack time-series collections acc. to specified windows sizes (e.g. 5 min) and modes (e.g. average values)

```py app.py merger``` -> combine time-series from several periods into a single collection file

```py app.py summarizer``` -> determine information on collection files & store to *.tsinfo files (ASCII text) for quick reference

Besides the above, a web-based GUI may be started by ```py app.py explorer``` to allow for an interactive analysis in the browser.

All of these tools can be used and fully controlled by setting parameters directly as CLI arguments. However, it is helpful to set up dedicated config files to describe the respective data structure for each project. Refer to the last section in this README for a template (JSON).

Use the ```--help``` option on the individual tools to get further instructions on how to use effectively.

## Package

The essential functionality of this project is given by classes of the package ```zynamon```. This is located in the respective subfolder and contains the following modules:

- zeit
- imex
- utils
- xutils

For more details, see the respective [package info](README_pkg.md).

## Template JSON Config

The following structure illustrates the outline of JSON-files that may act as specification for arbitrary projects. This is especially helpful for the import tool, but will also be used for the other processing steps.

```json
{
    "name": "TEMPLATE",
    "info": "Template for a Full Project (w/ all categories present)",

    "root": "ProjectFolderName",
    "path": "C:/Data/CSV",
    "assets": [ "Asset1", "Asset2" ],
    "periods": [ "2025-01", "AnyLabelIsPossible" ],

    "sub_logs_enum": [ "STAT", "DIAG", "WARN", "ALRM" ],
    "sub_logs_real": [ "MEAS" ],
    "sub_streams": [ "HiResSamples" ],
    "sub_streams_xt": [ "CMS_XTools" ],
    
    "def_logs_enum": {
        "name": "MessageText",
        "time": "MessageTime",
        "data": "MessageState"
        },
        
     "def_logs_real": {
        "name": "ShortTagName",
        "time": "TagTimeStamp",
        "data": "TagRealValue"
        },

    "def_streams": {
        "time": "Timestamp",
        "data": [ "humidity", "pressure", "temperature" ]
        },

    "def_streams_xt": {
        "time": null,
        "data": null
        },

    "_comment": "Provide human readable comments if required; this field is *not* evaluated!"    
}
```

For even more details, consult the source code of the ```zynamon.cli.py``` file.

- - -

[ Dr. Marcus Zeller | <dsp4444@gmail.com> | Erlangen, Germany | 2022-2024 ]
