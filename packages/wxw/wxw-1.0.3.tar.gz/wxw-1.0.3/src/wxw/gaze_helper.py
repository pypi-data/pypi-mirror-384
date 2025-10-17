import numpy as np
import cv2


# =======3D==========
def pixel_to_camera_3d(pt_2d, depth, camera_matrix):
    """Converts 2D pixel coordinates to 3D camera coordinates.

    Args:
        pt_2d (tuple):The (u, v) coordinates in the distorted image.
        depth (float or numpy.ndarray):The depth value or depth map.
        camera_matrix (numpy.ndarray):The camera intrinsic matrix.

    Returns:
        tuple:The 3D camera coordinates and the depth value.
    """
    if np.ndim(depth) > 1:
        x, y = map(int, pt_2d)
        depth = depth[y, x]

    if depth == 0:
        return None, None

    u_distorted, v_distorted = pt_2d
    homogeneous_uv1 = np.array([u_distorted, v_distorted, 1])
    camera_xy1 = np.linalg.inv(camera_matrix) @ homogeneous_uv1
    camera_xyz = camera_xy1 * depth

    return camera_xyz, depth


def pixel_to_camera_3d_numpy(p_uv, depth, camera_matrix):
    """Converts 2D pixel coordinates to 3D camera coordinates using NumPy.

    Args:
        p_uv (numpy.ndarray):Array of shape (N, 2) containing the 2D pixel coordinates.
        depth (numpy.ndarray or float):Array of shape (N,) containing the depth values or a single depth value.
        camera_matrix (numpy.ndarray):The 3x3 camera intrinsic matrix.

    Returns:
        tuple:The 3D camera coordinates (N, 3) and the depth values (N,).
    """
    if np.ndim(depth) == 2:
        indices = np.reshape(p_uv, (-1, 2)).astype(int)
        depth = depth[indices[:, 1], indices[:, 0]]

    u_distorted, v_distorted = np.split(p_uv, 2, axis=-1)
    homogeneous_uv1 = np.stack(
        [u_distorted, v_distorted, np.ones_like(u_distorted)], axis=1
    )  # [N, 3, 1]
    camera_xy1 = np.matmul(np.linalg.inv(camera_matrix), homogeneous_uv1)[
        ..., 0
    ]  # [N, 3, 1]
    camera_xyz = camera_xy1 * depth[:, None]  # depth shape:(N,)

    return camera_xyz, depth


def draw_gaze(
    image, start, pitch_yaw, length, thickness=1, color=(0, 0, 255), is_degree=False
):
    """Draws the gaze angle on the given image based on eye positions.

    Args:
        image (numpy.ndarray):The input image.
        start (tuple):The starting (x, y) coordinates for the gaze line.
        pitch_yaw (tuple):The pitch and yaw angles.
        length (int):The length of the gaze line.
        thickness (int, optional):The thickness of the gaze line. Defaults to 1.
        color (tuple, optional):The color of the gaze line in BGR format. Defaults to (0, 0, 255).
        is_degree (bool, optional):Whether the pitch and yaw are in degrees. Defaults to False.

    Returns:
        tuple:The image with the gaze line drawn and the angle in degrees.
    """
    if is_degree:
        pitch_yaw = np.deg2rad(pitch_yaw)

    pitch, yaw = pitch_yaw
    x, y = start

    if np.ndim(image) == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    dx = length * np.cos(pitch) * np.sin(yaw)
    dy = -length * np.sin(pitch)

    cv2.arrowedLine(
        image,
        (int(x), int(y)),
        (int(x + dx), int(y + dy)),
        color,
        thickness,
        cv2.LINE_AA,
        tipLength=0.2,
    )

    angle = np.rad2deg(np.arctan2(dy, dx))

    return image, angle


def gaze_3d_to_2d(gaze_3d, transformation_matrix=None):
    """Converts 3D gaze vector to 2D pitch and yaw angles.

    Args:
        gaze_3d (numpy.ndarray):The 3D gaze vector.
        transformation_matrix (numpy.ndarray, optional):The transformation matrix. Defaults to None.

    Returns:
        tuple:The pitch and yaw angles in degrees.
    """
    if transformation_matrix is not None:
        gaze_3d = np.dot(transformation_matrix, gaze_3d)

    gaze_3d = gaze_3d / np.linalg.norm(gaze_3d)
    dx, dy, dz = gaze_3d
    pitch = np.rad2deg(np.arcsin(-dy))  # -dy:Up is positive
    yaw = np.rad2deg(np.arctan(-dx / (dz + 1e-7)))  # -dx:Left is positive

    return pitch, yaw


def gaze_2d_to_3d(pitch, yaw, is_degree=True):
    """Converts 2D pitch and yaw angles to a 3D gaze vector.

    Args:
        pitch (float or numpy.ndarray):The pitch angle.
        yaw (float or numpy.ndarray):The yaw angle.
        is_degree (bool, optional):Whether the angles are in degrees. Defaults to True.

    Returns:
        numpy.ndarray:The 3D gaze vector.
    """
    if is_degree:
        pitch = np.deg2rad(pitch)
        yaw = np.deg2rad(yaw)

    pitch = np.reshape(pitch, (-1, 1))
    yaw = np.reshape(yaw, (-1, 1))
    batch_size = np.shape(pitch)[0]
    gaze = np.zeros((batch_size, 3))
    gaze[:, 0] = np.cos(pitch) * np.sin(yaw)
    gaze[:, 1] = -np.sin(pitch)
    gaze[:, 2] = -np.cos(pitch) * np.cos(yaw)
    gaze = gaze / np.linalg.norm(gaze, axis=1, keepdims=True)

    return gaze


def cosine_similarity_deg(a, b):
    """Calculates the cosine similarity between two vectors and returns the angle in degrees.

    Args:
        a (numpy.ndarray):First input vector of shape (N, D).
        b (numpy.ndarray):Second input vector of shape (N, D).

    Returns:
        numpy.ndarray:Array of angles in degrees between the input vectors.
    """
    a_normalized = a / np.linalg.norm(a, axis=1, keepdims=True)
    b_normalized = b / np.linalg.norm(b, axis=1, keepdims=True)
    dot_product = np.sum(a_normalized * b_normalized, axis=1)
    dot_product = np.clip(dot_product, a_min=-1.0, a_max=0.999999)
    angle_rad = np.arccos(dot_product)  # radians
    angle_deg = np.rad2deg(angle_rad)

    return angle_deg


def compute_euler(rotation_vector, translation_vector):
    """Computes Euler angles from a rotation vector.

    Args:
        rotation_vector (numpy.ndarray):The rotation vector.
        translation_vector (numpy.ndarray):The translation vector.

    Returns:
        numpy.ndarray:The Euler angles (pitch, yaw, roll) in degrees.
    """
    rvec_matrix = cv2.Rodrigues(rotation_vector)[0]
    proj_matrix = np.hstack((rvec_matrix, translation_vector))
    euler_angles = -cv2.decomposeProjectionMatrix(proj_matrix)[6]
    pitch = euler_angles[0]
    yaw = euler_angles[1]
    roll = euler_angles[2]
    rotation_params = np.array([pitch, yaw, roll]).flatten()

    return rotation_params


class NormalWarp:
    def __init__(self, camera_matrix, distortion_coeffs, distance_norm, focal_norm):
        """Initializes the NormalWarp class.

        Args:
            camera_matrix (numpy.ndarray):The camera intrinsic matrix.
            distortion_coeffs (numpy.ndarray):The camera distortion coefficients.
            distance_norm (float):Normalized distance between eye and camera.
            focal_norm (float):Focal length of the normalized camera.
        """
        self.camera_matrix = camera_matrix
        self.distortion_coeffs = distortion_coeffs
        self.camera_matrix_inv = np.linalg.inv(self.camera_matrix)

        self.face_points = np.array(
            [
                [-45.0968, -21.3129, 21.3129, 45.0968, -26.2996, 26.2996],
                [-0.4838, 0.4838, 0.4838, -0.4838, 68.595, 68.595],
                [2.397, -2.397, -2.397, 2.397, -0.0, -0.0],
            ]
        )
        self.face_points_t = self.face_points.T.reshape(-1, 1, 3)

        self.distance_norm = distance_norm
        self.roi_size = (448, 448)
        self.normalized_camera_matrix = np.array(
            [
                [focal_norm, 0, self.roi_size[0] / 2],
                [0, focal_norm, self.roi_size[1] / 2],
                [0, 0, 1.0],
            ]
        )

    def estimate_head_pose(self, landmarks, iterate=True):
        """Estimates the head pose from facial landmarks.

        Args:
            landmarks (numpy.ndarray):Array of shape (N, 2) containing the facial landmarks.
            iterate (bool, optional):Whether to further optimize the pose estimation. Defaults to True.

        Returns:
            tuple:Rotation vector, translation vector, and Euler angles.
        """
        landmarks = np.reshape(landmarks, (-1, 2))
        _, rotation_vector, translation_vector = cv2.solvePnP(
            self.face_points_t,
            landmarks,
            self.camera_matrix,
            self.distortion_coeffs,
            flags=cv2.SOLVEPNP_EPNP,
        )

        if iterate:
            _, rotation_vector, translation_vector = cv2.solvePnP(
                self.face_points_t,
                landmarks,
                self.camera_matrix,
                self.distortion_coeffs,
                rotation_vector,
                translation_vector,
                True,
            )
        head_euler = compute_euler(rotation_vector, translation_vector)
        return rotation_vector, translation_vector, head_euler

    def __call__(self, image, landmarks):
        """Normalizes and warps the face in the image based on facial landmarks.

        Args:
            image (numpy.ndarray):The input image.
            landmarks (numpy.ndarray):Array of shape (N, 2) containing the facial landmarks.

        Returns:
            tuple:The warped face image, rotation matrix, and warp matrix.
        """
        rotation_vector, translation_vector, _ = self.estimate_head_pose(landmarks)

        translation_vector = np.repeat(translation_vector, 6, axis=1)
        rotation_matrix = cv2.Rodrigues(rotation_vector)[0]
        face_center_3d = np.dot(rotation_matrix, self.face_points) + translation_vector
        face_center = np.sum(face_center_3d, axis=1, dtype=np.float32) / 6.0

        distance = np.linalg.norm(face_center)
        face_center /= distance
        forward = face_center.reshape(3)
        rotation_matrix = cv2.Rodrigues(rotation_vector)[0]
        right = rotation_matrix[:, 0]
        down = np.cross(forward, right)
        down /= np.linalg.norm(down)
        right = np.cross(down, forward)
        right /= np.linalg.norm(right)
        rotation_matrix = np.c_[right, down, forward].T

        scale_matrix = np.array(
            [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, self.distance_norm / distance],
            ]
        )
        warp_matrix = np.dot(
            np.dot(self.normalized_camera_matrix, scale_matrix),
            np.dot(rotation_matrix, self.camera_matrix_inv),
        )

        face_image = cv2.warpPerspective(image, warp_matrix, self.roi_size)
        return face_image, rotation_matrix, warp_matrix
