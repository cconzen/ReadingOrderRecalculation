# PageXML Reading Order Recalculation

This is a simple rule-based script for recalculating the region reading order of a PageXML file. It is meant to post-process results of a layout recognition using [Transkribus](https://www.transkribus.org/) or [Loghi](https://github.com/knaw-huc/loghi). More specifically, it is modelled to correctly order one or two page scans which contain marginalia. 

This script was developed for [Het Utrechts Archief](https://hetutrechtsarchief.nl/) within the context of an internship.

## What It Does

- **Extract Features**: Parses XML files to extract image information (height, width) as well as text regions and their coordinates.
- **Calculate Reading Order**: Uses extracted features to calculate the region reading order.
- **Update Files**: Saves the new reading order into the PageXMLs.
  
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

## How It Works

The script is using simple logic based on the geometric properties of the regions and page.

Given this sample layout of a scan:

<img src="https://github.com/cconzen/readingOrderCorrection/blob/main/explanation_svgs/start.svg" width="100%">

1. Determine orientation (landscape = two pages, portrait = one page) based on the image’s height and width. Depending on the orientation, the bookfold location is estimated:
   - at the horizontal centre of the scan for landscape orientation
   - at the left edge (x = 0) for portrait orientation

<img src="https://github.com/cconzen/readingOrderCorrection/blob/main/explanation_svgs/page_side.svg" width="100%">

2. The regions are assigned either 0 for left page or 1 for right page based on where their own horizontal centre is located.
3. The regions are ordered:
    - Left page to right page
        - Top to bottom
            - Left to right

<img src="https://github.com/cconzen/readingOrderCorrection/blob/main/explanation_svgs/firstorder.svg" width="100%">

4. The script then uses this initial order to iterate through all regions, comparing every current box with its immediate following one in the ranking. It checks whether the following box might be a marginalium by inspecting if they are located on the same page, and then if the candidate is vertically contained within the current box:

<img src="https://github.com/cconzen/readingOrderCorrection/blob/main/explanation_svgs/verticallywithin.svg" width="100%">

5. It is then confirmed that it is located to the left or right of the current box (In this case, it is considered to be left of it; it’s comparing the left edge for the left condition (and vice versa) so overlapping boxes are handled correctly):

<img src="https://github.com/cconzen/readingOrderCorrection/blob/main/explanation_svgs/leftcheck.svg" width="100%">

6. If all these conditions apply, their ranks/indices are swapped:

<img src="https://github.com/cconzen/readingOrderCorrection/blob/main/explanation_svgs/swapranks.svg" width="100%">

7. If a swap occurs, the loop breaks and restarts with the new order. This gets repeated until no more swaps occur in a full loop; the final reading order has been reached:

<img src="https://github.com/cconzen/readingOrderCorrection/blob/main/explanation_svgs/finalorder.svg" width="100%">

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
