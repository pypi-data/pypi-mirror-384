import numpy as np
import cv2
from .common import xyxy2xywh

# =========Warp face from insightface=======


def estimate_norm(landmarks, image_size=112):
    """Estimates the normalization transformation matrix for given landmarks.

    Args:
        landmarks (numpy.ndarray):Array of shape (5, 2) containing the facial landmarks.
        image_size (int, optional):Size of the output image. Defaults to 112.

    Returns:
        numpy.ndarray:The 2x3 transformation matrix.
    """
    from skimage import transform as trans

    arcface_dst = np.array(
        [
            [38.2946, 51.6963],
            [73.5318, 51.5014],
            [56.0252, 71.7366],
            [41.5493, 92.3655],
            [70.7299, 92.2041],
        ],
        dtype=np.float32,
    )

    assert landmarks.shape == (5, 2), "Landmarks should be of shape (5, 2)."
    assert (
        image_size % 112 == 0 or image_size % 128 == 0
    ), "Image size should be a multiple of 112 or 128."

    if image_size % 112 == 0:
        ratio = float(image_size) / 112.0
        diff_x = 0
    else:
        ratio = float(image_size) / 128.0
        diff_x = 8.0 * ratio

    dst = arcface_dst * ratio
    dst[:, 0] += diff_x

    tform = trans.SimilarityTransform()
    tform.estimate(landmarks, dst)
    transformation_matrix = tform.params[0:2, :]

    return transformation_matrix


def norm_crop(img, landmarks, image_size=112):
    """Normalizes and crops an image based on facial landmarks.

    Args:
        img (numpy.ndarray):The input image.
        landmarks (numpy.ndarray):Array of shape (5, 2) containing the facial landmarks.
        image_size (int, optional):Size of the output image. Defaults to 112.

    Returns:
        tuple:The warped image and the transformation matrix.
    """
    transformation_matrix = estimate_norm(landmarks, image_size)
    warped_image = cv2.warpAffine(
        img, transformation_matrix, (image_size, image_size), borderValue=0.0
    )

    return warped_image, transformation_matrix


def warp_face(img, x1, y1, x2, y2):
    """Warps a face in an image based on bounding box coordinates.

    Args:
        img (numpy.ndarray):The input image.
        x1 (int):The x-coordinate of the top-left corner of the bounding box.
        y1 (int):The y-coordinate of the top-left corner of the bounding box.
        x2 (int):The x-coordinate of the bottom-right corner of the bounding box.
        y2 (int):The y-coordinate of the bottom-right corner of the bounding box.

    Returns:
        numpy.ndarray:The warped image.
    """
    center_x, center_y, face_width, face_height = (
        xyxy2xywh([x1, y1, x2, y2]).flatten().astype(int)
    )
    scale = 256 / (max(face_width, face_height) * 1.5)
    return transform(img, (center_x, center_y), 256, scale, 0)


def transform(data, center, output_size, scale, rotation):
    """Applies a series of transformations to the input data.

    Args:
        data (numpy.ndarray):The input image data.
        center (tuple):The center point for the transformation.
        output_size (int):The size of the output image.
        scale (float):The scaling factor.
        rotation (float):The rotation angle in degrees.

    Returns:
        tuple:The transformed image and the transformation matrix.
    """
    from skimage import transform as trans

    scale_ratio = scale
    rotation_radians = float(rotation) * np.pi / 180.0

    # Define the series of transformations
    scale_transform = trans.SimilarityTransform(scale=scale_ratio)
    translation_transform1 = trans.SimilarityTransform(
        translation=(-center[0] * scale_ratio, -center[1] * scale_ratio)
    )
    rotation_transform = trans.SimilarityTransform(rotation=rotation_radians)
    translation_transform2 = trans.SimilarityTransform(
        translation=(output_size / 2, output_size / 2)
    )

    # Combine the transformations
    combined_transform = (
        scale_transform
        + translation_transform1
        + rotation_transform
        + translation_transform2
    )
    transformation_matrix = combined_transform.params[0:2]

    # Apply the transformation
    cropped_image = cv2.warpAffine(
        data, transformation_matrix, (output_size, output_size), borderValue=0.0
    )

    return cropped_image, transformation_matrix


def transform_points_2d(points, transformation_matrix):
    """Transforms 2D points using a given transformation matrix.

    Args:
        points (numpy.ndarray):Array of shape (N, 2) containing the 2D points.
        transformation_matrix (numpy.ndarray):The 2x3 transformation matrix.

    Returns:
        numpy.ndarray:Array of transformed 2D points.
    """
    transformed_points = np.zeros(shape=points.shape, dtype=np.float32)
    for i in range(points.shape[0]):
        point = points[i]
        homogeneous_point = np.array([point[0], point[1], 1.0], dtype=np.float32)
        transformed_point = np.dot(transformation_matrix, homogeneous_point)
        transformed_points[i] = transformed_point[0:2]

    return transformed_points


def transform_points_3d(points, transformation_matrix):
    """Transforms 3D points using a given transformation matrix.

    Args:
        points (numpy.ndarray):Array of shape (N, 3) containing the 3D points.
        transformation_matrix (numpy.ndarray):The 2x3 transformation matrix.

    Returns:
        numpy.ndarray:Array of transformed 3D points.
    """
    scale = np.sqrt(transformation_matrix[0][0] ** 2 + transformation_matrix[0][1] ** 2)
    transformed_points = np.zeros(shape=points.shape, dtype=np.float32)
    for i in range(points.shape[0]):
        point = points[i]
        homogeneous_point = np.array([point[0], point[1], 1.0], dtype=np.float32)
        transformed_point = np.dot(transformation_matrix, homogeneous_point)
        transformed_points[i][0:2] = transformed_point[0:2]
        transformed_points[i][2] = points[i][2] * scale

    return transformed_points
