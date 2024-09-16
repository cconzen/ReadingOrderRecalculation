import os
import re
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import argparse 

def extract_features_from_xml(xml_file: str) -> pd.DataFrame:
    """
    Extracts text region features from a PageXML. Parses the XML,
    extracts text region coordinates, their IDs, structure types, and previous reading order index,
    and computes various geometric properties.

    Args:
        xml_file (str): Path to the XML file.

    Returns:
        pd.DataFrame: DataFrame containing extracted features for each text region, including:
            * 'id': Region ID
            * 'x_min', 'y_min': Minimum x and y coordinates
            * 'x_max', 'y_max': Maximum x and y coordinates
            * 'width', 'height': Width and height of the region
            * 'page_side': position of the region; left (0) or right (1) page
            * 'aspect_ratio': Aspect ratio of the region
            * 'structure_type': Structure type of the region
            * 'index': Reading order index
    """

    tree = ET.parse(xml_file)
    root = tree.getroot()

    ns = {'ns': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}

    page_width = int(root.find('.//ns:Page', ns).attrib['imageWidth'])
    page_height = int(root.find('.//ns:Page', ns).attrib['imageHeight'])

    bookfold_centre = page_width / 2 if page_width > page_height else 0

    regions = []

    reading_order = {}
    ordered_group = root.find('.//ns:ReadingOrder/ns:OrderedGroup', ns)
    if ordered_group:
        for region_ref in ordered_group.findall('ns:RegionRefIndexed', ns):
            region_id = region_ref.attrib['regionRef']
            index = int(region_ref.attrib['index'])
            reading_order[region_id] = index

        text_regions = root.findall('.//ns:TextRegion', ns)
        if not text_regions:
            return None

        for region in text_regions:
            region_id = region.attrib['id']
            coords = region.find('ns:Coords', ns).attrib['points']
            custom_str = region.attrib.get('custom', '')

            match = re.search(r'structure\s*{[^}]*type:([^;]+);', custom_str)
            structure_type = match.group(1) if match else "Unknown"

            points = [list(map(int, point.split(','))) for point in coords.split()]
            x_min = min(p[0] for p in points)
            y_min = min(p[1] for p in points)
            x_max = max(p[0] for p in points)
            y_max = max(p[1] for p in points)

            width = x_max - x_min
            height = y_max - y_min
            aspect_ratio = width / height

            avg_x = np.mean([point[0] for point in points])
            page_side = 0 if avg_x < bookfold_centre else 1  

            index = reading_order.get(region_id, -1)  # default to -1 if not found

            regions.append({
                'id': region_id,
                'x_min': x_min, # left most coordinate
                'x_max': x_max, # right most coordinate
                'y_min': y_min, # highest coordinate
                'y_max': y_max, # lowest coordinate
                'width': width,
                'height': height,
                'page_side': page_side, # 0 = left side, 1 = right side
                'aspect_ratio': aspect_ratio,
                'structure_type': structure_type,
                'index': index # initial reading order index
            })

        return pd.DataFrame(regions)
    else:
        return None

def update_reading_order_in_xml(xml_file: str, updated_df: pd.DataFrame, overwrite: bool) -> None:
    """
    Updates the reading order in a PageXML based on the predicted order.
    The PageXML file is modified to reflect the new reading order and saved as a new XML file.

    Args:
        xml_file (str): Path to the original XML file.
        updated_df (pd.DataFrame): DataFrame containing the updated reading order for each text region.
        overwrite (bool): Option to save the modified PageXML as a new file, or to overwrite the original.

    Returns:
        None: The updated XML file is saved to disk.
    """
    
    def remove_namespace(tree: ET.ElementTree) -> None:
        """Removes namespace in the passed XML tree."""
        for elem in tree.iter():
            if '}' in elem.tag:
                elem.tag = elem.tag.split('}', 1)[1]
            elem.attrib = {k.split('}', 1)[-1]: v for k, v in elem.attrib.items()}
        return tree

    tree = ET.parse(xml_file)
    ns_r = remove_namespace(tree)
    root = ns_r.getroot()

   # ns = {'ns': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}

    reading_order = root.find('.//ReadingOrder/OrderedGroup')

    if reading_order is None:
        print(f"No ReadingOrder found in {xml_file}. Skipping...")
        return

    for _, row in updated_df.iterrows():
        region_ref = row['id']
        sequential_order = row['sequential_order']

        region_element = reading_order.find(f".//RegionRefIndexed[@regionRef='{region_ref}']")
        if region_element is not None:
            region_element.set('index', str(sequential_order))

        text_region = root.find(f".//TextRegion[@id='{region_ref}']")
        if text_region is not None:
            custom_attrib = text_region.attrib.get('custom', '')
            new_custom_attrib = re.sub(r'readingOrder {index:\d+;}',
                                       f'readingOrder {{index:{sequential_order};}}',
                                       custom_attrib)
            text_region.set('custom', new_custom_attrib)

    xml_bytes = ET.tostring(root, encoding='UTF-8', method='xml', xml_declaration=True)
    xml_str = xml_bytes.decode('UTF-8')

    xml_str = re.sub(r'(<\?xml version=\'1.0\' encoding=\'UTF-8\'\?>)',
                     '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>', xml_str)

    if 'xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15"' not in xml_str:
        xml_str = re.sub(r'<PcGts', '<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15"', xml_str)

    if overwrite:
        with open(xml_file, 'w', encoding='UTF-8') as file:
            file.write(xml_str)
        print(f"PageXML with corrected reading order was saved as: {xml_file}")
    else:
        new_xml_file = xml_file.replace('.xml', '_updated.xml')
        with open(new_xml_file, 'w', encoding='UTF-8') as file:
            file.write(xml_str)
        print(f"PageXML with corrected reading order was saved as: {new_xml_file}")

def batch_inference_rules(directory: str, overwrite: bool = False) -> None:
    """
    Processes all XML files in the given directory and updates their reading order based on 
    comparison rules between adjacent regions. It only compares each region with its 
    immediate following one on the same page side.

    Args:
        directory (str): Path to the directory containing XML files.
        overwrite (bool): Whether to overwrite the original XML files with the updated reading order.

    Returns:
        None
    """
    
    xml_files = [f for f in os.listdir(directory) if f.endswith('xml')]

    if not xml_files:
        print(f"No XML files found in directory: {directory}")
        return
    
    for xml_file in xml_files:
        xml_path = os.path.join(directory, xml_file)
        
        features_df = extract_features_from_xml(xml_path)

        if features_df is None:
            print(f"No text regions found in {xml_file}. Skipping...")
            continue

        # sort regions by page side first, then top to bottom, and then left to right
        features_df = features_df.sort_values(by=['page_side', 'y_min', 'x_min']).reset_index(drop=True)

        # initialise sequential order starting with 0
        features_df['sequential_order'] = 0
        features_df['swapped'] = False
        # iterate over regions and compare each box with its immediate following one
        for i in range(len(features_df) - 1):
            current_box = features_df.iloc[i]
            next_box = features_df.iloc[i + 1]

            if current_box['swapped'] or next_box['swapped']:
                continue

            # all boxes on the right side
            if current_box['page_side'] == next_box['page_side'] == 0:
                if next_box['y_max'] <= current_box['y_max'] and next_box['y_min'] >= current_box['y_min']:
                    if next_box['x_min'] > current_box['x_min'] or next_box['x_max'] < current_box['x_max']:
                        # swap order of the boxes
                        features_df.at[i, 'sequential_order'] = i + 1
                        features_df.at[i + 1, 'sequential_order'] = i
                        features_df.at[i, 'swapped'] = True
                        features_df.at[i + 1, 'swapped'] = True
                    else:
                        # keep as is
                        features_df.at[i, 'sequential_order'] = i
                        features_df.at[i + 1, 'sequential_order'] = i + 1
                else:
                    # keep as is
                    features_df.at[i, 'sequential_order'] = i
                    features_df.at[i + 1, 'sequential_order'] = i + 1

            # all boxes on the left side
            elif current_box['page_side'] == next_box['page_side'] == 1:
                if next_box['y_max'] <= current_box['y_max'] and next_box['y_min'] >= current_box['y_min']:
                    if next_box['x_min'] > current_box['x_min'] or next_box['x_max'] < current_box['x_max']:
                        # swap order of the boxes
                        features_df.at[i, 'sequential_order'] = i + 1
                        features_df.at[i + 1, 'sequential_order'] = i
                        features_df.at[i, 'swapped'] = True
                        features_df.at[i + 1, 'swapped'] = True
                    else:
                        # Keep as is
                        features_df.at[i, 'sequential_order'] = i
                        features_df.at[i + 1, 'sequential_order'] = i + 1
                else:
                    # keep as is
                    features_df.at[i, 'sequential_order'] = i
                    features_df.at[i + 1, 'sequential_order'] = i + 1
            else:
                features_df.at[i, 'sequential_order'] = i
                features_df.at[i + 1, 'sequential_order'] = i + 1

        for i in range(len(features_df)):
            if not features_df.iloc[i]['swapped']:
                features_df.at[i, 'sequential_order'] = i

        print("Predicted Reading Order:")
        print(features_df[['id', 'page_side', 'x_min', 'y_max', 'sequential_order']])

        update_reading_order_in_xml(xml_path, features_df, overwrite)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Process XML files to update reading order.')
    parser.add_argument('directory', type=str, help='Path to the directory containing XML files.')
    parser.add_argument('--overwrite', action='store_true', help='Whether to overwrite the original XML files.')
    args = parser.parse_args()
    
    batch_inference_rules(args.directory, args.overwrite)
