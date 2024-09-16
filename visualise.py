import re
import os
from typing import List, Tuple, Dict
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont


def parse_points(points_str: str) -> Tuple[int, int, int, int]:
    """Parse the points from the 'Coords' element and return x_min, x_max, y_min, y_max."""
    points = re.findall(r'\d+,\d+', points_str)
    x_coords = [int(point.split(',')[0]) for point in points]
    y_coords = [int(point.split(',')[1]) for point in points]
    return min(x_coords), max(x_coords), min(y_coords), max(y_coords)

def extract_region_info(xml_path: str) -> Tuple[List[Tuple[int, int, int, int, int]], int, int]:
    """Extract regions, their coordinates, and reading order from the XML file."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    ns = {'ns': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}

    regions: List[Tuple[int, int, int, int, int]] = []
    reading_order: Dict[str, int] = {}

    for region_ref in root.findall(".//ns:RegionRefIndexed", ns):
        region_id = region_ref.attrib['regionRef']
        order_index = int(region_ref.attrib['index'])
        reading_order[region_id] = order_index

    for region in root.findall(".//ns:TextRegion", ns):
        region_id = region.attrib['id']
        coords_element = region.find("ns:Coords", ns)
        if coords_element is not None:
            points_str = coords_element.attrib['points']
            x_min, x_max, y_min, y_max = parse_points(points_str)
            order = reading_order.get(region_id, -1)  # default to -1 if no reading order is found
            regions.append((x_min, x_max, y_min, y_max, order))
    page = root.find(".//ns:Page", ns)
    page_width = int(page.attrib['imageWidth'])
    page_height = int(page.attrib['imageHeight'])

    regions.sort(key=lambda r: r[4])  # sort by reading order (index 4)

    return regions, page_width, page_height

def draw(image_path: str, regions: List[Tuple[int, int, int, int, int]], output_image_path: str) -> None:
    """Draw bounding boxes, bookfold, and annotate reading order on the base image."""

    image = Image.open(image_path).convert("RGBA")  # convert to RGBA for transparency support
    draw = ImageDraw.Draw(image)

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    left_transparent = (200, 150, 255, 80) # light purple
    right_transparent = (152, 255, 152, 80) # light green

    bookfold_x = image.width // 2
    overlay_draw.rectangle([0, 0, bookfold_x, image.height], fill=left_transparent)
    overlay_draw.rectangle([bookfold_x, 0, image.width, image.height], fill=right_transparent)


    image = Image.alpha_composite(image, overlay) # combines image with page seperation overlay
    
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" # linux standard font, adjust for other OS
    font_size = 50 
    font = ImageFont.truetype(font_path, font_size)

    draw = ImageDraw.Draw(image)  # reinitialise draw object to draw on top of the overlay

    centers: List[Tuple[float, float]] = []
    for x_min, x_max, y_min, y_max, order in regions:
        center_x = (x_min + x_max) / 2
        center_y = (y_min + y_max) / 2
        centers.append((center_x, center_y))

    # READING ORDER PATH VISUALISATION
    path_color = "red"
    path_width = 5

    if len(centers) > 1:
        for i in range(len(centers) - 1):
            draw.line([centers[i], centers[i + 1]], fill=path_color, width=path_width)

    for x_min, x_max, y_min, y_max, order in regions:

        # BOUNDING BOX VISUALISATION
        draw.rectangle([x_min, y_min, x_max, y_max], outline="white", width=5)
        
        if order != -1:
            text = str(order)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # centre
            x_pos = x_min + (x_max - x_min - text_width) / 2
            y_pos = y_min + (y_max - y_min - text_height) / 2
            

            background_padding = 25
            background_x0 = x_pos - background_padding
            background_y0 = y_pos - background_padding
            background_x1 = x_pos + text_width + background_padding
            background_y1 = y_pos + text_height + background_padding

            draw.rectangle([background_x0, background_y0, background_x1, background_y1], fill="white")

            draw.text((x_pos, y_pos - 10), text, fill="black", font=font)

    final_image = image.convert("RGB")
    final_image.save(output_image_path)
    final_image.show()

def process_dir(base_folder: str) -> None:
    """Process all images and XML files in the specified base folder."""
    ordner_path = base_folder
    page_path = os.path.join(base_folder, "page")
    
    for image_filename in os.listdir(ordner_path):
        if image_filename.lower().endswith(('.jpg')):
            image_path = os.path.join(ordner_path, image_filename)
            xml_filename = os.path.splitext(image_filename)[0] + '.xml'
            xml_path = os.path.join(page_path, xml_filename)
            
            if os.path.exists(xml_path):
                # Extract regions and reading order from the XML
                regions, image_width, image_height = extract_region_info(xml_path)
                output_dir = "visualisation"
                os.makedirs(output_dir, exist_ok=True)
                output_image_path = os.path.join(output_dir, os.path.splitext(image_filename)[0] + '_vis.jpg')
                draw(image_path, regions, output_image_path)
            else:
                print(f"XML file not found for image: {image_filename}")


if __name__ == "__main__":

    base_folder = 'example_folder'  # replace with your base folder path

    process_dir(base_folder)
