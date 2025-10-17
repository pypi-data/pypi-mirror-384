# EpiCure

[![License BSD-3](https://img.shields.io/pypi/l/epicure.svg?color=green)](https://github.com/gletort/Epicure/-/blob/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/epicure.svg?color=green)](https://pypi.org/project/epicure)
[![Python Version](https://img.shields.io/pypi/pyversions/epicure.svg?color=green)](https://python.org)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/epicure)](https://napari-hub.org/plugins/epicure)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.13952184.svg)](https://doi.org/10.5281/zenodo.13952184)

![EpiCure logo](https://github.com/gletort/Epicure/blob/main/docs/imgs/epicure_logo.png "EpiCure logo")

**Napari plugin to ease manual correction of epithelia segmentation in movies.**

To analyse individual cell trajectory from epithelia movies marked for cell-cell junctions, a very precise segmentation and tracking is required.
Several tools such as TissuAnalyzer, [Epyseg](https://github.com/baigouy/EPySeg), [CellPose](https://www.cellpose.org/) or [Dist2Net](https://github.com/jeanollion/distnet2d) perform very good segmentation (~5% of errors). 
However, this still implies a high amount of cells to correct manually. 

EpiCure allows to decrease the burden of this task. 
Several features are proposed to ease the manual correction of the segmented movies, such as error detection, numerous shortcuts for editing the segmentation, option for tracking, display and measure/export options.
EpiCure detect segmentation errors by taking advantage of temporal information. 
When a correction is done at a given frame, EpiCure relink the track to adjust for the changes.

 > **See the full [documentation here](https://gletort.github.io/Epicure/)**

![EpiCure interface](https://github.com/gletort/Epicure/blob/main/docs/imgs/EpiGen.png "EpiCure interface")

## Installation

### Install plugin
To install EpiCure on a fresh python virtual environment, type inside the environement:
```
pip install epicure
``` 

Then launch `Napari`, and the plugin should be visible in the `Plugins` list.

If you already have an environment with `Napari` installed, you can also install it directly in `Napari>Plugins>Install/Uninstall plugins`

### Install code
To have the code to be able to modify it, clone this repository. You can use `pip install -e .` so that everytime you update the code, the plugin will be updated. 

## Dependencies

The input files of EpiCure can be already tracked or not.
Tracking options are proposed in EpiCure:
* Laptrack centroids
* Laptrack overlaps

## Usage
Refer to the [documentation](https://gletort.github.io/Epicure/) for documentation of the different steps possible in the pipeline.

## References

If you use EpiCure, thank you for citing our work: 

EpiCure is not published yet, you can cite it using Zenodo for now: https://doi.org/10.5281/zenodo.13952184


## Issues
If you encounter a code related issue using EpiCure, please [file an issue](https://github.com/gletort/epicure/issues) in this repository.
If you have a question on using EpiCure or ask to add a feature, either file an issue or write in the [imagesc forum](https://forum.image.sc/).

[napari]: https://github.com/napari/napari
[file an issue]: https://github.com/gletort/epicure/issues
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/
