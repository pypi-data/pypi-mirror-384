## Description
A Python-based package that creates Köppen-Geiger Climate Classification (KGCC) maps from monthly climate images prepared by the user. The earthengine-api (ee) dependency handles these images as image collection objects. Besides loading resulting KGCC maps to memory, the package can download KGCC geotif maps to Google Drive. Additionally, when the geemap library is installed, the maps may be visualized with only a few lines of code.

## Requirements
- Google Account
- Google Earth Engine Account
- Python 3
- earthengine-api library
- geemap library (optional for visualization)

## Setup
In a default Google Colab environment, setup requirements are already met for installing geekgcc. The earthengine-api (ee) depency is automatically installed with geekgcc and in Colab. When using Colab, prepend an exclamation mark (!) to the beginning of the following two code lines.
**To install the geekgcc Python package using Git and Pip:**
```bash
git clone https://github.com/ARS-SWRC/GEE-KGCC
pip install GEE-KGCC/geekgcc_package
```
**To install the geekgcc Python package locally from a downloaded clone of the repository, use the following steps.** In an environment tool like conda, activate your Python environment and navigate to the top of the geekgcc_package sub-directory, which should contain a .toml file. Then, run the following Pip command:
```bash
pip install .
```
**For visualization, additionally install the geemaps library. In Colab, this library is pre-installed.**

Installation instructions may be found at:
https://geemap.org/

**To authenticate ee and import necessary libraries, use the following steps.** Start by importing, authenticating, and initializing ee, then import geekgcc.
```python
import ee

#This will open a web browser for log-in steps.
ee.Authenticate()
geeusername = 'yourusername' #Enter your GEE user name.
geeproject = 'ee-yourusername' #Enter your GEE project name.
ee.Initialize(project=geeproject)
#The user must have an existing project.
#Default project names are in the format: "ee-yourusername".
#The web browser log-in steps assist with creating a project
#or one may be created at https://code.earthengine.google.com/

#ee should be initialized before importing geekgcc.
import geekgcc
```

## Usage Notes
The user must provide `ee.ImageCollection` objects of long-term average monthly precipitation and temperature (12 images each). These should be overlapping images and should exist enitrely within a hemisphere (i.e., not in both hemispheres, such that at least two operations are needed to produce global coverage). WGS84 coordinate system is assumed in geekgcc. Climate images should be reprojected if they are in some other coordinate system.

**The following methods are included in geekgcc**: `classify()`, `download()`, `get_class_index()`, and `get_vis_params()`.

**Classification from monthly precipitation and temperature raster images:**

`geekgcc.KGCC.classify(p_ic, t_ic, hemi)`

| Parameter | Type | Description |
| ------ | ------ | ------ |
| p_ic | ee.ImageCollection | 12 monthly precipitation images (mm) |
| t_ic | ee.ImageCollection | 12 monthly mean temperature images (°C) |
| hemi | string | "north" or "south" hemisphere |

Returns a classified `ee.Image` object. Possible output values are in the range from 1 to 30.

**Download classified image to Google Drive:**

`geekgcc.KGCC.download(type_image, geo, scale, filename)`

| Parameter | Type | Description |
| ------ | ------ | ------ |
| type_image | ee.Image | classified image |
| geo | ee.Geometry | bounding box geometry |
| scale | float | scale/resolution of downloaded image |
| filename | string | downloaded file name |

Returns `None`. Spawns a download task to Google Drive in geotif format. Download progress may be monitored in the Earth Engine Online Code Editor.

**Get visualization parameters:**

`geekgcc.KGCC.get_vis_params()`

| Parameter | Type | Description |
| ------ | ------ | ------ |
| - | - | - |

Returns a `dict` of visualization parameters including the minimum value (1), maximum value (30), and a commonly used color scheme for KGCC. Only needed when visualizing with geemaps.

**Get class look-up dictionary:**

`geekgcc.KGCC.get_class_index()`

| Parameter | Type | Description |
| ------ | ------ | ------ |
| - | - | - |

Returns a `dict` that relates class values to class names and letter labels corresponding to 30 climate classes.

## GitHub Repository
https://github.com/ARS-SWRC/GEE-KGCC/tree/main
