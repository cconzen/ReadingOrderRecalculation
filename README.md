# PageXML Reading Order Correction

This is a simple rule-based script for correcting the reading order of a PageXML file. It is meant to post process results of a layout recognition using Transkribus or Loghi.

## What It Does

- **Extract Features**: Parses XML files to extract text regions, including coordinates, aspect ratios, structure types, and initial reading order indices.
- **Update Reading Order**: Adjusts the reading order of text regions based on their position and geometry.
- **Update Files**: Saves the new reading order into the XMLs.

## How It Works

The script is using simple logic based on the geometric properties of the regions and page.

1. Check aspect ratio. If the width of the page is bigger than the height, a bookfold is approximated by deviding the width by 2. If not, the bookfold is set to 0 for a single page layout.
2. Assign all regions that have their centre left of the bookfold 0 for the left page, all right of the bookfold 1 for the right page.
3. Order the regions by their page side first (left before right), then for each side top to bottom and left to right
4. iterate over all regions and compare each box with its immediate following one:
     - if the two consecutive boxes are both on the left page, OR if two consecutive boxes are both on the right page:
        - if box 2's lowest coordinate is higher than that of box 1, and its highest lower than that of box 1:
          - swap their ranks if box 2 (x_min) is left of box 1 (x_min)
          - swap their ranks if box 2 (x_max) is right of box 1 (x_max)
     - keep their initial reading order rank if otherwise

The script then updates the reading order attributes within the XML structure, reflecting the new reading order. You can choose if you wish to overwrite the prior xml file, or save it as a new one.

## Requirements

You only need numpy and pandas in addition to some standard Python libraries. You can install the required dependencies using pip:

```
pip install numpy pandas
```

## Usage
### Batch Processing of XML Files

The code is written to process all XML files located in a directory by calling batch_inference_rules().
This applies inference rules to adjust the reading order and saves the updated XML files either by overwriting them or creating new ones.

```
from reading_order import batch_inference_rules

batch_inference_rules('path/to/xml-directory', overwrite=True)
```
### Visualisation

You can visualise the calculated reading order path by specifying your base directory in visualise.py and executing it:


<img src="https://github.com/cconzen/readingOrderCorrection/blob/main/example_folder/default.jpg" width="50%" height="50%"><img src="https://github.com/cconzen/readingOrderCorrection/blob/main/visualisation/default_vis.jpg" width="50%" height="50%">
<img src="https://github.com/cconzen/readingOrderCorrection/blob/main/example_folder/default2.jpg" width="50%" height="50%"><img src="https://github.com/cconzen/readingOrderCorrection/blob/main/visualisation/default2_vis.jpg" width="50%" height="50%">
<img src="https://github.com/cconzen/readingOrderCorrection/blob/main/example_folder/default3.jpg" width="50%" height="50%"><img src="https://github.com/cconzen/readingOrderCorrection/blob/main/visualisation/default3_vis.jpg" width="50%" height="50%">

# License
This project is licensed under the MIT License - see the LICENSE file for details.
