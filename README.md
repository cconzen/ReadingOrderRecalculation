# PageXML Reading Order Recalculation

This is a simple rule-based script for recalculating the region reading order of a PageXML file. It is meant to post-process results of a layout recognition using [Transkribus](https://www.transkribus.org/) or [Loghi](https://github.com/knaw-huc/loghi). More specifically, it is modelled to correctly order one or two page scans which contain marginalia. 

This script was developed for [Het Utrechts Archief](https://hetutrechtsarchief.nl/) within the context of an internship.

## What It Does

- **Extract Features**: Parses XML files to extract text regions, including coordinates, aspect ratios, structure types, and initial reading order indices.
- **Update Reading Order**: Adjusts the reading order of text regions based on their position and geometry.
- **Update Files**: Saves the new reading order into the XMLs.

## How It Works

The script is using simple logic based on the geometric properties of the regions and page.

1. Check aspect ratio. If the width of the page is bigger than the height, a bookfold is approximated by deviding the width by 2. If not, the bookfold is set to 0 for a single page layout.
2. Assign all regions that have their centre left of the bookfold 0 for the left page, all right of the bookfold 1 for the right page.
3. Order the regions by their page side first (left before right), then for each side top to bottom and left to right
4. iterate over all regions following the current reading order and compare each box with its immediate following one UNTIL not one swap occurs:
     - if the two consecutive boxes are both on the same page:
        - if box 2's lowest coordinate is higher than that of box 1, and its highest lower than that of box 1:
          - swap their ranks if box 2 (x_min) is left of box 1 (x_min) OR box 2 (x_max) is right of box 1 (x_max), update current reading order and restart loop
     - keep their initial reading order rank if otherwise

5. Once a loop runs through with no swaps, the script takes the final reading order and updates the reading order attributes within the XML structure, reflecting the new reading order. You can choose if you wish to overwrite the prior xml file, or save it as a new one.

## Requirements

You only need numpy and pandas in addition to some standard Python libraries. You can install the required dependencies using pip:

```
pip install numpy pandas
```

## Usage

### Batch Reading Order Recalculation of PageXML files

The code is written to process all XML files located in a directory; To execute the script, install all dependencies first and then run following:
```
python reorder.py example_folder/page --overwrite
```
As arguments, specify the base directory containing the PageXML files (here example_folder/page), and add --overwrite if you wish to overwrite the existing file.

### Visualisation

You can visualise the calculated reading order path by specifying your base directory and executing it:
```
python visualise.py example_folder
```
Here are some side-by-side comparisons of input image and visualised result: 

(these can be found in the [example_folder](https://github.com/cconzen/ReadingOrderRecalculation/tree/main/example_folder); The scans were processed using [Loghi](https://github.com/knaw-huc/loghi).

<img src="https://github.com/cconzen/readingOrderCorrection/blob/main/example_folder/default.jpg" width="50%" height="50%"><img src="https://github.com/cconzen/readingOrderCorrection/blob/main/visualisation/default_vis.jpg" width="50%" height="50%">
<img src="https://github.com/cconzen/readingOrderCorrection/blob/main/example_folder/default2.jpg" width="50%" height="50%"><img src="https://github.com/cconzen/readingOrderCorrection/blob/main/visualisation/default2_vis.jpg" width="50%" height="50%">
<img src="https://github.com/cconzen/readingOrderCorrection/blob/main/example_folder/default5.jpg" width="50%" height="50%"><img src="https://github.com/cconzen/readingOrderCorrection/blob/main/visualisation/default5_vis.jpg" width="50%" height="50%">

# License
This project is licensed under the MIT License - see the LICENSE file for details.
