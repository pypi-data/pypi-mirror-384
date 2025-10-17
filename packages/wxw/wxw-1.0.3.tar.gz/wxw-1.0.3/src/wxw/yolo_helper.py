import cv2
import numpy as np
import json
import base64
import os.path as osp
from collections import defaultdict


def create_labelme_file(
    png_path, content=None, overwrite=False, labelme_version="5.0.1"
):
    """Creates a LabelMe JSON file for the given PNG image.

    Args:
        png_path (str):Path to the PNG image file.
        content (dict, optional):Content to be written to the JSON file. Defaults to None.
        overwrite (bool, optional):Whether to overwrite the existing JSON file. Defaults to False.
        labelme_version (str, optional):Version of LabelMe. Defaults to "5.0.1".
    """
    json_path = osp.splitext(png_path)[0] + ".json"
    if osp.exists(json_path) and not overwrite:
        return

    # Create the content dictionary if not provided
    if content is None:
        content = create_labelme_content(None, png_path, [], labelme_version)

    # Write the content dictionary to a JSON file
    with open(json_path, "w") as file_object:
        json.dump(content, file_object)


def create_labelme_content(img, png_path, shapes=None, labelme_version="5.0.1"):
    """Creates the content dictionary for a LabelMe JSON file.

    Args:
        img (numpy.ndarray or None):Image data. If None, the image will be read from png_path.
        png_path (str):Path to the PNG image file.
        shapes (list, optional):List of shapes to be included in the JSON file. Defaults to an empty list.
        labelme_version (str, optional):Version of LabelMe. Defaults to "5.0.1".

    Returns:
        dict:Content dictionary for the LabelMe JSON file.
    """
    if shapes is None:
        shapes = []
    if not isinstance(shapes, list):
        shapes = [shapes]

    # Convert the image to base64
    if img is None:
        img = cv2.imread(png_path)
    encoded_string = cv_img_to_base64(img)
    img_height, img_width = img.shape[:2]

    # Create the base_info dictionary
    base_info = {
        "version": labelme_version,
        "flags": {},
        "shapes": shapes,
        "imagePath": osp.basename(png_path),
        "imageData": encoded_string,
        "imageHeight": img_height,
        "imageWidth": img_width,
    }
    return base_info


def create_labelme_shape(label: str, points, shape_type: str):
    """Creates a shape dictionary for a LabelMe JSON file.

    Args:
        label (str):Label for the shape.
        points (list):List of points defining the shape.
        shape_type (str):Type of the shape (e.g., "rectangle", "polygon").

    Returns:
        dict:Shape dictionary for the LabelMe JSON file.
    """
    points = np.reshape(points, [-1, 2]).squeeze().tolist()
    return {
        "label": label,
        "points": points,
        "group_id": None,
        "shape_type": shape_type,
        "flags": {},
    }


def update_labelme_shape_label(js, convert):
    info = json.load(open(js, "r"))
    shapes = info.get("shapes", [])
    new_shape = []
    for shape in shapes:
        label = shape["label"]
        if label in convert:
            new_label = convert[label]
            if new_label is None:
                continue
            shape["label"] = new_label
        new_shape.append(shape)
    info["shapes"] = new_shape
    json.dump(info, open(js, "w"))


def compute_polygon_from_mask(mask, debug=False):
    """Extracts polygon contours from a binary mask image.

    Args:
        mask (numpy.ndarray):Binary mask image with values 0 or 1.
        debug (bool, optional):Whether to visualization. Defaults to False.

    Returns:
        list:List of polygons, where each polygon is represented as an array of points.
    """
    import skimage.measure

    POLYGON_APPROX_TOLERANCE = 0.004
    # Pad the mask to ensure contours are detected at the edges
    padded_mask = np.pad(mask, pad_width=1)
    contours = skimage.measure.find_contours(padded_mask, level=0.5)

    if len(contours) == 0:
        print("No contour found, returning empty polygon.")
        return []

    polygons = []

    for contour in contours:
        if contour.shape[0] < 3:
            continue
        # Approximate the polygon
        polygon = skimage.measure.approximate_polygon(
            coords=contour,
            tolerance=np.ptp(contour, axis=0).max() * POLYGON_APPROX_TOLERANCE,
        )
        # Clip the polygon to the mask dimensions
        polygon = np.clip(polygon, (0, 0), (mask.shape[0] - 1, mask.shape[1] - 1))
        # Remove the last point if it is a duplicate of the first point
        polygon = polygon[:-1]

        # Optional visualization (disabled by default)
        if debug:
            vision = (255 * np.stack([mask] * 3, axis=-1)).astype(np.uint8)
            for y, x in polygon.astype(int):
                cv2.circle(vision, (x, y), 3, (0, 0, 222), -1)
            cv2.imshow("Polygon", vision)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        # Append the polygon with coordinates in (x, y) format
        polygons.append(polygon[:, ::-1])

    return polygons


class LabelObject(object):
    """Class representing a labeled object with various attributes."""

    def __init__(self):
        self.type = None
        self.pts = None
        self.ori_pts = None
        self.pts_normed = None
        self.label = None
        self.box = None
        self.height = None
        self.width = None

    def __str__(self):
        return f"type:{self.type}, label:{self.label}"


def parse_json(
    path,
    to_polygon=False,
    to_rectangle=False,
    return_dict=False,
    ignore=None,
    value=127.5,
) -> [list, np.ndarray, str]:
    """Parses a JSON file and extracts image and shape information.

    Args:
        path (str):Path to the JSON file.
        to_polygon (bool):Whether to convert points to polygon format.
        return_dict (bool, optional):Whether to return a dictionary of objects. Defaults to False.
        to_rectangle (bool, optional):Whether to return a dictionary of objects. Defaults to False.
        ignore (str, optional):Whether to draw ingore on image. Defaults to False.

    Returns:
        tuple:A tuple containing a list or dictionary of LabelObject instances, the image, and the basename.
    """
    assert path.endswith(".json")
    info = json.load(open(path, "r"))
    base64_str = info.get("imageData", None)
    if base64_str is None:
        img = cv2.imread(path.replace(".json", ".png"))
    else:
        img_str = base64.b64decode(base64_str)
        np_arr = np.frombuffer(img_str, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        image_height = info.get("imageHeight", None)
        image_width = info.get("imageWidth", None)
    else:
        image_height, image_width = img.shape[:2]

    obj_list = []
    for shape in info.get("shapes", []):
        obj = LabelObject()
        obj.label = shape.get("label", None)
        pts = shape.get("points", [])
        obj.ori_pts = np.reshape(pts, (-1, 2)).astype(int)
        if to_polygon and len(pts) == 2:
            x1, y1, x2, y2 = np.array(pts).flatten()
            pts = np.array([x1, y1, x2, y1, x2, y2, x1, y2])
        if to_rectangle and len(pts) > 2:
            pts = get_min_rect(pts).flatten()[:4]
        obj.pts = np.reshape(pts, (-1, 2))
        obj.type = shape.get("shape_type", "")
        obj.height = image_height
        obj.width = image_width
        # =====processed=======
        if obj.label == ignore:
            if obj.type == "polygon":
                contours = np.reshape(obj.pts, (-1, 1, 2)).astype(int)
                img = cv2.drawContours(img, [contours], -1, (value, value, value), -1)
            elif obj.type == "rectangle":
                x1, y1, x2, y2 = obj.pts.astype(int).flatten()
                cv2.rectangle(img, (x1, y1), (x2, y2), (127.5, 127.5, 127.5), -1)
            else:
                print(f"未知的 ignore 标签形状类型, 形状类型为：{obj.type}")
            continue
        obj_list.append(obj)
        obj.pts_normed = np.reshape(obj.pts, [-1, 2]) / np.array(
            [image_width, image_height]
        )
    basename = osp.basename(path).split(".")[0]
    if return_dict:
        obj_dict = defaultdict(list)
        for obj in obj_list:
            obj_dict[obj.label].append(obj)
        return obj_dict, img, basename
    return obj_list, img, basename


def show_yolo_label(
    img, lines, xywh=True, classes: dict = None, colors=None, thickness=2
):
    """Displays YOLO labels on an image.

    Args:
        img (numpy.ndarray):The image on which to display the labels.
        lines (list):List of label lines, each containing class index and bounding box coordinates.
        xywh (bool, optional):Whether the bounding box coordinates are in (x, y, width, height) format. Defaults to True.
        classes (dict, optional):Dictionary mapping class indices to class names. Defaults to None.
        colors (list, optional):List of colors for each class. Defaults to None.
        thickness (int, optional):Thickness of the bounding box lines. Defaults to 2.

    Returns:
        tuple:The image with labels and a list of points.
    """
    if classes is None:
        classes = {i: i for i in range(10)}
    if colors is None:
        colors = create_color_list(len(classes))[1:]
    mask = np.zeros_like(img)
    height, width = img.shape[:2]
    pts = []
    for line in lines:
        if not line:
            continue
        sp = line.strip().split(" ")
        idx, a, b, c, d = [float(x) for x in sp]
        idx = int(idx)
        if xywh:
            x1, y1, x2, y2 = (
                xywh2xyxy([a, b, c, d]) * np.array([width, height, width, height])
            ).astype(int)[0]
        else:
            x1, y1, x2, y2 = (
                np.array([a, b, c, d]) * np.array([width, height, width, height])
            ).astype(int)[0]

        if thickness == -1:
            mask = cv2.rectangle(mask, (x1, y1), (x2, y2), colors[idx], thickness)
        else:
            img = cv2.rectangle(img, (x1, y1), (x2, y2), colors[idx], thickness)
        img = put_text(img, str(classes[idx]), (x1, y1), (0, 0, 0), (222, 222, 222))
        pts.append([idx, x1, y1, x2, y2])
    if thickness == -1:
        img = cv2.addWeighted(img, 0.7, mask, 0.3, 1)
    return img, pts


def show_yolo_file(jpg_path, xywh=True, classes=None, colors=None, thickness=2):
    """Displays YOLO labels on an image from a file.

    Args:
        jpg_path (str):Path to the JPEG image file.
        xywh (bool, optional):Whether the bounding box coordinates are in (x, y, width, height) format. Defaults to True.
        classes (dict, optional):Dictionary mapping class indices to class names. Defaults to None.
        colors (list, optional):List of colors for each class. Defaults to None.
        thickness (int, optional):Thickness of the bounding box lines. Defaults to 2.

    Returns:
        tuple:The image with labels and a list of points.
    """
    img = cv2.imread(jpg_path)
    txt = osp.splitext(jpg_path)[0] + ".txt"
    with open(txt, "r") as fo:
        lines = fo.readlines()
    img, pts = show_yolo_label(img, lines, xywh, classes, colors, thickness)
    # img = cv2.copyMakeBorder(img, 40, 0, 0, 0, cv2.BORDER_CONSTANT, (0, 0, 0))
    img = put_text(img, jpg_path)
    return img, pts
