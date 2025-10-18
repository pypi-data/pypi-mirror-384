"""
Implements the grid finding algorithm, that is able to find the intersections of horizontal and vertical rules.
"""

import math
from typing import cast
import os
import cv2 as cv
import numpy as np
from cv2.typing import MatLike
from numpy.typing import NDArray
from pathlib import Path
import json
from typing import Optional, List, Tuple
import logging
from os import PathLike

from taulu._core import astar as rust_astar
from taulu.types import PointFloat, Point
from . import img_util as imu
from .img_util import ensure_gray
from .constants import WINDOW
from .decorators import log_calls
from .table_indexer import TableIndexer
from .header_template import _Rule
from .split import Split
from ._core import TableGrower

show_time = 0

logger = logging.getLogger(__name__)


def clamp(
    num: float | int, min_bound: float | int, max_bound: float | int
) -> float | int:
    return max(min(num, max_bound), min_bound)


def vector_average_slope(lines: List[Tuple[PointFloat, PointFloat]]) -> float:
    sin_sum = 0
    cos_sum = 0
    for left, right in lines:
        dx = right[0] - left[0]
        dy = right[1] - left[1]
        angle = math.atan2(dy, dx)

        sin_sum += math.sin(angle)
        cos_sum += math.cos(angle)

    avg_angle = math.atan2(sin_sum, cos_sum)

    # Convert back to slope
    if math.isclose(math.cos(avg_angle), 0.0, abs_tol=1e-9):
        return float("inf")  # vertical line
    else:
        return math.tan(avg_angle)


def circular_median_angle(angles):
    """Return the circular median of angles in radians."""
    import math

    def circular_distance(a, b):
        diff = abs(a - b) % (2 * math.pi)
        return min(diff, 2 * math.pi - diff)

    angles = [angle % (2 * math.pi) for angle in angles]
    n = len(angles)

    best_median = None
    min_total_distance = float("inf")

    # Try each angle as a potential "cut point" for linearization
    for cut_point in angles:
        # Reorder angles relative to this cut point
        reordered = sorted(angles, key=lambda x: (x - cut_point) % (2 * math.pi))

        # Find median in this ordering
        if n % 2 == 1:
            candidate = reordered[n // 2]
        else:
            a1, a2 = reordered[n // 2 - 1], reordered[n // 2]
            # Take circular average of the two middle angles
            diff = (a2 - a1) % (2 * math.pi)
            if diff > math.pi:
                diff = diff - 2 * math.pi
            candidate = (a1 + diff / 2) % (2 * math.pi)

        # Calculate total circular distance to all points
        total_distance = sum(circular_distance(candidate, angle) for angle in angles)

        if total_distance < min_total_distance:
            min_total_distance = total_distance
            best_median = candidate

    return best_median


def median_slope(lines: List[Tuple[PointFloat, PointFloat]]) -> float:
    angles = []

    for (x1, y1), (x2, y2) in lines:
        dx = x2 - x1
        dy = y2 - y1
        angle = math.atan2(dy, dx)
        angles.append(angle)

    median_angle = circular_median_angle(angles)

    # Convert back to slope
    if math.isclose(math.cos(median_angle), 0.0, abs_tol=1e-9):
        return float("inf")  # Vertical
    else:
        return math.tan(median_angle)


class GridDetector:
    """
    Detects table grid intersections using morphological filtering and template matching.

    This detector implements a multi-stage pipeline:

    1. **Binarization**: Sauvola adaptive thresholding to handle varying lighting
    2. **Morphological operations**: Dilation to connect broken rule segments
    3. **Cross-kernel matching**: Template matching with a cross-shaped kernel to find
       rule intersections where horizontal and vertical lines meet
    4. **Grid growing**: Iterative point detection starting from a known seed point

    The cross-kernel is designed to match the specific geometry of your table rules.
    It should be sized so that after morphology, it aligns with actual corner shapes.

    ## Tuning Guidelines

    - **kernel_size**: Increase if you need more selectivity (fewer false positives)
    - **cross_width/height**: Should match rule thickness after morphology
    - **morph_size**: Increase to connect more broken lines, but this thickens rules
    - **sauvola_k**: Increase to threshold more aggressively (remove noise)
    - **search_region**: Increase for documents with more warping/distortion
    - **distance_penalty**: Increase to prefer corners closer to expected positions

    ## Visual Debugging

    Set `visual=True` in methods to see intermediate results and tune parameters.
    """

    def __init__(
        self,
        kernel_size: int = 21,
        cross_width: int = 6,
        cross_height: Optional[int] = None,
        morph_size: Optional[int] = None,
        sauvola_k: float = 0.04,
        sauvola_window: int = 15,
        scale: float = 1.0,
        search_region: int = 40,
        distance_penalty: float = 0.4,
        min_rows: int = 5,
        grow_threshold: float = 0.3,
        look_distance: int = 4,
    ):
        """
        Args:
            kernel_size (int): the size of the cross kernel
                a larger kernel size often means that more penalty is applied, often leading
                to more sparse results
            cross_width (int): the width of one of the edges in the cross filter, should be
                roughly equal to the width of the rules in the image after morphology is applied
            cross_height (int | None): useful if the horizontal rules and vertical rules
                have different sizes
            morph_size (int | None): the size of the morphology operators that are applied before
                the cross kernel. 'bridges the gaps' of broken-up lines
            sauvola_k (float): threshold parameter for sauvola thresholding
            sauvola_window (int): window_size parameter for sauvola thresholding
            scale (float): image scale factor to do calculations on (useful for increasing calculation speed mostly)
            search_region (int): area in which to search for a new max value in `find_nearest` etc.
            distance_penalty (float): how much the point finding algorithm penalizes points that are further in the region [0, 1]
            min_rows (int): minimum number of rows to find before stopping the table finding algorithm
            grow_threshold (float): the threshold for accepting a new point when growing the table
            look_distance (int): how many points away to look when calculating the median slope
        """
        self._validate_parameters(
            kernel_size,
            cross_width,
            cross_height,
            morph_size,
            search_region,
            sauvola_k,
            sauvola_window,
            distance_penalty,
        )

        self._kernel_size = kernel_size
        self._cross_width = cross_width
        self._cross_height = cross_width if cross_height is None else cross_height
        self._morph_size = morph_size if morph_size is not None else cross_width
        self._search_region = search_region
        self._sauvola_k = sauvola_k
        self._sauvola_window = sauvola_window
        self._distance_penalty = distance_penalty
        self._scale = scale
        self._min_rows = min_rows
        self._grow_threshold = grow_threshold
        self._look_distance = look_distance

        self._cross_kernel = self._create_cross_kernel()

    def _validate_parameters(
        self,
        kernel_size: int,
        cross_width: int,
        cross_height: Optional[int],
        morph_size: Optional[int],
        search_region: int,
        sauvola_k: float,
        sauvola_window: int,
        distance_penalty: float,
    ) -> None:
        """Validate initialization parameters."""
        if kernel_size % 2 == 0:
            raise ValueError("kernel_size must be odd")
        if (
            kernel_size <= 0
            or cross_width <= 0
            or search_region <= 0
            or sauvola_window <= 0
        ):
            raise ValueError("Size parameters must be positive")
        if cross_height is not None and cross_height <= 0:
            raise ValueError("cross_height must be positive")
        if morph_size is not None and morph_size <= 0:
            raise ValueError("morph_size must be positive")
        if not 0 <= distance_penalty <= 1:
            raise ValueError("distance_penalty must be in [0, 1]")
        if sauvola_k <= 0:
            raise ValueError("sauvola_k must be positive")

    def _create_gaussian_weights(self, region_size: int) -> NDArray:
        """
        Create a 2D Gaussian weight mask.

        Args:
            shape (tuple[int, int]): Shape of the region (height, width)
            p (float): Minimum value at the edge = 1 - p

        Returns:
            NDArray: Gaussian weight mask
        """
        if self._distance_penalty == 0:
            return np.ones((region_size, region_size), dtype=np.float32)

        y = np.linspace(-1, 1, region_size)
        x = np.linspace(-1, 1, region_size)
        xv, yv = np.meshgrid(x, y)
        dist_squared = xv**2 + yv**2

        # Prevent log(0) when distance_penalty is 1
        if self._distance_penalty >= 0.999:
            sigma = 0.1  # Small sigma for very sharp peak
        else:
            sigma = np.sqrt(-1 / (2 * np.log(1 - self._distance_penalty)))

        weights = np.exp(-dist_squared / (2 * sigma**2))

        return weights.astype(np.float32)

    def _create_cross_kernel(self) -> NDArray:
        kernel = np.zeros((self._kernel_size, self._kernel_size), dtype=np.uint8)
        center = self._kernel_size // 2

        # Create horizontal bar
        h_start = max(0, center - self._cross_height // 2)
        h_end = min(self._kernel_size, center + (self._cross_height + 1) // 2)
        kernel[h_start:h_end, :] = 255

        # Create vertical bar
        v_start = max(0, center - self._cross_width // 2)
        v_end = min(self._kernel_size, center + (self._cross_width + 1) // 2)
        kernel[:, v_start:v_end] = 255

        return kernel

    def _apply_morphology(self, binary: MatLike) -> MatLike:
        # Define a horizontal kernel (adjust width as needed)
        kernel_hor = cv.getStructuringElement(cv.MORPH_RECT, (self._morph_size, 1))
        kernel_ver = cv.getStructuringElement(cv.MORPH_RECT, (1, self._morph_size))

        # Apply dilation
        dilated = cv.dilate(binary, kernel_hor, iterations=1)
        dilated = cv.dilate(dilated, kernel_ver, iterations=1)

        return dilated

    def _apply_cross_matching(self, img: MatLike) -> MatLike:
        """Apply cross kernel template matching."""
        pad_y = self._cross_kernel.shape[0] // 2
        pad_x = self._cross_kernel.shape[1] // 2

        padded = cv.copyMakeBorder(
            img, pad_y, pad_y, pad_x, pad_x, borderType=cv.BORDER_CONSTANT, value=0
        )

        filtered = cv.matchTemplate(padded, self._cross_kernel, cv.TM_SQDIFF_NORMED)
        # Invert and normalize to 0-255 range
        filtered = cv.normalize(1.0 - filtered, None, 0, 255, cv.NORM_MINMAX)
        return filtered.astype(np.uint8)

    def apply(self, img: MatLike, visual: bool = False) -> MatLike:
        """
        Apply the grid detection filter to the input image.

        Args:
            img (MatLike): the input image
            visual (bool): whether to show intermediate steps

        Returns:
            MatLike: the filtered image, with high values (whiter pixels) at intersections of horizontal and vertical rules
        """

        if img is None or img.size == 0:
            raise ValueError("Input image is empty or None")

        binary = imu.sauvola(img, k=self._sauvola_k, window_size=self._sauvola_window)

        if visual:
            imu.show(binary, title="thresholded")

        binary = self._apply_morphology(binary)

        if visual:
            imu.show(binary, title="dilated")

        filtered = self._apply_cross_matching(binary)

        return filtered

    @log_calls(level=logging.DEBUG, include_return=True)
    def find_nearest(
        self, filtered: MatLike, point: Point, region: Optional[int] = None
    ) -> Tuple[Point, float]:
        """
        Find the nearest 'corner match' in the image, along with its score [0,1]

        Args:
            filtered (MatLike): the filtered image (obtained through `apply`)
            point (tuple[int, int]): the approximate target point (x, y)
            region (None | int): alternative value for search region,
                overwriting the `__init__` parameter `region`
        """

        if filtered is None or filtered.size == 0:
            raise ValueError("Filtered image is empty or None")

        region_size = region if region is not None else self._search_region
        x, y = point

        # Calculate crop boundaries
        crop_x = max(0, x - region_size // 2)
        crop_y = max(0, y - region_size // 2)
        crop_width = min(region_size, filtered.shape[1] - crop_x)
        crop_height = min(region_size, filtered.shape[0] - crop_y)

        # Handle edge cases
        if crop_width <= 0 or crop_height <= 0:
            logger.warning(f"Point {point} is outside image bounds")
            return point, 0.0

        cropped = filtered[crop_y : crop_y + crop_height, crop_x : crop_x + crop_width]

        if cropped.size == 0:
            return point, 0.0

        # Always apply Gaussian weighting by extending crop if needed
        if cropped.shape[0] == region_size and cropped.shape[1] == region_size:
            # Perfect size - apply weights directly
            weights = self._create_gaussian_weights(region_size)
            weighted = cropped.astype(np.float32) * weights
        else:
            # Extend crop to match region_size, apply weights, then restore
            extended = np.zeros((region_size, region_size), dtype=cropped.dtype)

            # Calculate offset to center the cropped region in extended array
            offset_y = (region_size - cropped.shape[0]) // 2
            offset_x = (region_size - cropped.shape[1]) // 2

            # Place cropped region in center of extended array
            extended[
                offset_y : offset_y + cropped.shape[0],
                offset_x : offset_x + cropped.shape[1],
            ] = cropped

            # Apply Gaussian weights to extended array
            weights = self._create_gaussian_weights(region_size)
            weighted_extended = extended.astype(np.float32) * weights

            # Extract the original region back out
            weighted = weighted_extended[
                offset_y : offset_y + cropped.shape[0],
                offset_x : offset_x + cropped.shape[1],
            ]

        best_idx = np.argmax(weighted)
        best_y, best_x = np.unravel_index(best_idx, cropped.shape)

        result_point = (
            int(crop_x + best_x),
            int(crop_y + best_y),
        )
        result_confidence = float(weighted[best_y, best_x]) / 255.0

        return result_point, result_confidence

    def find_table_points(
        self,
        img: MatLike | PathLike[str],
        left_top: Point,
        cell_widths: list[int],
        cell_heights: list[int] | int,
        visual: bool = False,
        window: str = WINDOW,
        goals_width: Optional[int] = None,
        filtered: Optional[MatLike | PathLike[str]] = None,
    ) -> "TableGrid":
        """
        Parse the image to a `TableGrid` structure that holds all of the
        intersections between horizontal and vertical rules, starting near the `left_top` point

        Args:
            img (MatLike): the input image of a table
            left_top (tuple[int, int]): the starting point of the algorithm
            cell_widths (list[int]): the expected widths of the cells (based on a header template)
            cell_heights (list[int]): the expected height of the rows of data.
                The last value from this list is used until the image has no more vertical space.
            visual (bool): whether to show intermediate steps
            window (str): the name of the OpenCV window to use for visualization
            goals_width (int | None): the width of the goal region when searching for the next point.
                If None, defaults to 1.5 * search_region
            filtered (MatLike | PathLike[str] | None): if provided, this image is used instead of
                calculating the filtered image from scratch

        Returns:
            a TableGrid object
        """

        if goals_width is None:
            goals_width = self._search_region * 3 // 2

        if not cell_widths:
            raise ValueError("cell_widths must contain at least one value")

        if not isinstance(img, np.ndarray):
            img = cv.imread(os.fspath(img))

        if filtered is None:
            filtered = self.apply(img, visual)
        else:
            if not isinstance(filtered, np.ndarray):
                filtered = cv.imread(os.fspath(filtered))

            filtered = ensure_gray(filtered)

        if visual:
            imu.show(filtered, window=window)

        if isinstance(cell_heights, int):
            cell_heights = [cell_heights]

        left_top, confidence = self.find_nearest(
            filtered, left_top, int(self._search_region * 3)
        )

        if confidence < 0.1:
            logger.warning(
                f"Low confidence for the starting point: {confidence} at {left_top}"
            )

        # resize all parameters according to scale
        img = cv.resize(img, None, fx=self._scale, fy=self._scale)

        if visual:
            imu.push(img)

        filtered = cv.resize(filtered, None, fx=self._scale, fy=self._scale)
        cell_widths = [int(w * self._scale) for w in cell_widths]
        cell_heights = [int(h * self._scale) for h in cell_heights]
        left_top = (int(left_top[0] * self._scale), int(left_top[1] * self._scale))
        self._search_region = int(self._search_region * self._scale)

        img_gray = ensure_gray(img)
        filtered_gray = ensure_gray(filtered)

        table_grower = TableGrower(
            img_gray,
            filtered_gray,
            cell_widths,  # pyright: ignore
            cell_heights,  # pyright: ignore
            left_top,
            self._search_region,
            self._distance_penalty,
            self._look_distance,
            self._grow_threshold,
            self._min_rows,
        )

        def show_grower_progress(wait: bool = False):
            img_orig = np.copy(img)
            corners = table_grower.get_all_corners()
            for y in range(len(corners)):
                for x in range(len(corners[y])):
                    if corners[y][x] is not None:
                        img_orig = imu.draw_points(
                            img_orig,
                            [corners[y][x]],
                            color=(0, 0, 255),
                            thickness=30,
                        )

            edge = table_grower.get_edge_points()

            for point, score in edge:
                color = (100, int(clamp(score * 255, 0, 255)), 100)
                imu.draw_point(img_orig, point, color=color, thickness=20)

            imu.show(img_orig, wait=wait)

        if visual:
            threshold = self._grow_threshold
            look_distance = self._look_distance

            # python implementation of rust loops, for visualization purposes
            # note this is a LOT slower
            while table_grower.grow_point(img_gray, filtered_gray) is not None:
                show_grower_progress()

            show_grower_progress(True)

            original_threshold = threshold

            loops_without_change = 0

            while not table_grower.is_table_complete():
                loops_without_change += 1

                if loops_without_change > 50:
                    break

                if table_grower.extrapolate_one(img_gray, filtered_gray) is not None:
                    show_grower_progress()

                    loops_without_change = 0

                    grown = False
                    while table_grower.grow_point(img_gray, filtered_gray) is not None:
                        show_grower_progress()
                        grown = True
                        threshold = min(0.1 + 0.9 * threshold, original_threshold)
                        table_grower.set_threshold(threshold)

                    if not grown:
                        threshold *= 0.9
                        table_grower.set_threshold(threshold)

                else:
                    threshold *= 0.9
                    table_grower.set_threshold(threshold)

                    if table_grower.grow_point(img_gray, filtered_gray) is not None:
                        show_grower_progress()
                        loops_without_change = 0

        else:
            table_grower.grow_table(img_gray, filtered_gray)

        table_grower.smooth_grid()
        corners = table_grower.get_all_corners()
        logger.info(
            f"Table growth complete, found {len(corners)} rows and {len(corners[0])} columns"
        )
        # rescale corners back to original size
        if self._scale != 1.0:
            for y in range(len(corners)):
                for x in range(len(corners[y])):
                    if corners[y][x] is not None:
                        corners[y][x] = (
                            int(corners[y][x][0] / self._scale),  # pyright:ignore
                            int(corners[y][x][1] / self._scale),  # pyright:ignore
                        )

        return TableGrid(corners)  # pyright: ignore

    @log_calls(level=logging.DEBUG, include_return=True)
    def _build_table_row(
        self,
        gray: MatLike,
        filtered: MatLike,
        start_point: Point,
        cell_widths: List[int],
        row_idx: int,
        goals_width: int,
        previous_row_points: Optional[List[Point]] = None,
        visual: bool = False,
    ) -> List[Point]:
        """Build a single row of table points."""
        row = [start_point]
        current = start_point

        for col_idx, width in enumerate(cell_widths):
            next_point = self._find_next_column_point(
                gray,
                filtered,
                current,
                width,
                goals_width,
                visual,
                previous_row_points,
                col_idx,
            )
            if next_point is None:
                logger.warning(
                    f"Could not find point for row {row_idx}, col {col_idx + 1}"
                )
                return []  # Return empty list to signal failure
            row.append(next_point)
            current = next_point

        return row

    def _clamp_point_to_img(self, point: Point, img: MatLike) -> Point:
        """Clamp a point to be within the image bounds."""
        x = max(0, min(point[0], img.shape[1] - 1))
        y = max(0, min(point[1], img.shape[0] - 1))
        return (x, y)

    @log_calls(level=logging.DEBUG, include_return=True)
    def _find_next_column_point(
        self,
        gray: MatLike,
        filtered: MatLike,
        current: Point,
        width: int,
        goals_width: int,
        visual: bool = False,
        previous_row_points: Optional[List[Point]] = None,
        current_col_idx: int = 0,
    ) -> Optional[Point]:
        """Find the next point in the current row."""

        if previous_row_points is not None and current_col_idx + 1 < len(
            previous_row_points
        ):
            # grow an astar path downwards from the previous row point that is
            # above and to the right of current
            # and ensure all points are within image bounds
            bottom_right = [
                self._clamp_point_to_img(
                    (
                        current[0] + width - goals_width // 2 + x,
                        current[1] + goals_width,
                    ),
                    gray,
                )
                for x in range(goals_width)
            ]
            goals = self._astar(
                gray, previous_row_points[current_col_idx + 1], bottom_right, "down"
            )

            if goals is None:
                logger.warning(
                    f"A* failed to find path going downwards from previous row's point at idx {current_col_idx + 1}"
                )
                return None
        else:
            goals = [
                self._clamp_point_to_img(
                    (current[0] + width, current[1] - goals_width // 2 + y), gray
                )
                for y in range(goals_width)
            ]

        path = self._astar(gray, current, goals, "right")

        if path is None:
            logger.warning(
                f"A* failed to find path going rightward from {current} to goals"
            )
            return None

        next_point, _ = self.find_nearest(filtered, path[-1], self._search_region)

        # show the point and the search region on the image for debugging
        if visual:
            self._visualize_path_finding(
                goals + path,
                current,
                next_point,
                current,
                path[-1],
                self._search_region,
            )

        return next_point

    @log_calls(level=logging.DEBUG, include_return=True)
    def _find_next_row_start(
        self,
        gray: MatLike,
        filtered: MatLike,
        top_point: Point,
        row_idx: int,
        cell_heights: List[int],
        goals_width: int,
        visual: bool = False,
    ) -> Optional[Point]:
        """Find the starting point of the next row."""
        if row_idx < len(cell_heights):
            row_height = cell_heights[row_idx]
        else:
            row_height = cell_heights[-1]

        if top_point[1] + row_height >= filtered.shape[0] - 10:  # Near bottom
            return None

        goals = [
            (top_point[0] - goals_width // 2 + x, top_point[1] + row_height)
            for x in range(goals_width)
        ]

        path = self._astar(gray, top_point, goals, "down")
        if path is None:
            return None

        next_point, _ = self.find_nearest(
            filtered, path[-1], region=self._search_region * 3 // 2
        )

        if visual:
            self._visualize_path_finding(
                path, top_point, next_point, top_point, path[-1], self._search_region
            )

        return next_point

    def _visualize_grid(self, img: MatLike, points: List[List[Point]]) -> None:
        """Visualize the detected grid points."""
        all_points = [point for row in points for point in row]
        drawn = imu.draw_points(img, all_points)
        imu.show(drawn, wait=True)

    def _visualize_path_finding(
        self,
        path: List[Point],
        current: Point,
        next_point: Point,
        previous_row_target: Optional[Point] = None,
        region_center: Optional[Point] = None,
        region_size: Optional[int] = None,
    ) -> None:
        """Visualize the path finding process for debugging."""
        global show_time

        screen = imu.pop()

        # if gray, convert to BGR
        if len(screen.shape) == 2 or screen.shape[2] == 1:
            debug_img = cv.cvtColor(screen, cv.COLOR_GRAY2BGR)
        else:
            debug_img = cast(MatLike, screen)

        debug_img = imu.draw_points(debug_img, path, color=(200, 200, 0), thickness=2)
        debug_img = imu.draw_points(
            debug_img, [current], color=(0, 255, 0), thickness=3
        )
        debug_img = imu.draw_points(
            debug_img, [next_point], color=(0, 0, 255), thickness=2
        )

        # Draw previous row target if available
        if previous_row_target is not None:
            debug_img = imu.draw_points(
                debug_img, [previous_row_target], color=(255, 0, 255), thickness=2
            )

        # Draw search region if available
        if region_center is not None and region_size is not None:
            top_left = (
                max(0, region_center[0] - region_size // 2),
                max(0, region_center[1] - region_size // 2),
            )
            bottom_right = (
                min(debug_img.shape[1], region_center[0] + region_size // 2),
                min(debug_img.shape[0], region_center[1] + region_size // 2),
            )
            cv.rectangle(
                debug_img,
                top_left,
                bottom_right,
                color=(255, 0, 0),
                thickness=2,
                lineType=cv.LINE_AA,
            )

        imu.push(debug_img)

        show_time += 1
        if show_time % 10 != 1:
            return

        imu.show(debug_img, title="Next column point", wait=False)
        # time.sleep(0.003)

    @log_calls(level=logging.DEBUG, include_return=True)
    def _astar(
        self,
        img: np.ndarray,
        start: tuple[int, int],
        goals: list[tuple[int, int]],
        direction: str,
    ) -> Optional[List[Point]]:
        """
        Find the best path between the start point and one of the goal points on the image
        """

        if not goals:
            return None

        if self._scale != 1.0:
            img = cv.resize(img, None, fx=self._scale, fy=self._scale)
            start = (int(start[0] * self._scale), int(start[1] * self._scale))
            goals = [(int(g[0] * self._scale), int(g[1] * self._scale)) for g in goals]

        # calculate bounding box with margin
        all_points = goals + [start]
        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]

        margin = 30
        top_left = (max(0, min(xs) - margin), max(0, min(ys) - margin))
        bottom_right = (
            min(img.shape[1], max(xs) + margin),
            min(img.shape[0], max(ys) + margin),
        )

        # check bounds
        if (
            top_left[0] >= bottom_right[0]
            or top_left[1] >= bottom_right[1]
            or top_left[0] >= img.shape[1]
            or top_left[1] >= img.shape[0]
        ):
            return None

        # transform coordinates to cropped image
        start_local = (start[0] - top_left[0], start[1] - top_left[1])
        goals_local = [(g[0] - top_left[0], g[1] - top_left[1]) for g in goals]

        cropped = img[top_left[1] : bottom_right[1], top_left[0] : bottom_right[0]]

        if cropped.size == 0:
            return None

        path = rust_astar(cropped, start_local, goals_local, direction)

        if path is None:
            return None

        if self._scale != 1.0:
            path = [(int(p[0] / self._scale), int(p[1] / self._scale)) for p in path]
            top_left = (int(top_left[0] / self._scale), int(top_left[1] / self._scale))

        return [(p[0] + top_left[0], p[1] + top_left[1]) for p in path]


class TableGrid(TableIndexer):
    """
    A data class that allows segmenting the image into cells
    """

    _right_offset: int | None = None

    def __init__(self, points: list[list[Point]], right_offset: Optional[int] = None):
        """
        Args:
            points: a 2D list of intersections between hor. and vert. rules
        """
        self._points = points
        self._right_offset = right_offset

    @property
    def points(self) -> list[list[Point]]:
        return self._points

    def row(self, i: int) -> list[Point]:
        assert 0 <= i and i < len(self._points)
        return self._points[i]

    @property
    def cols(self) -> int:
        if self._right_offset is not None:
            return len(self.row(0)) - 2
        else:
            return len(self.row(0)) - 1

    @property
    def rows(self) -> int:
        return len(self._points) - 1

    @staticmethod
    def from_split(
        split_grids: Split["TableGrid"], offsets: Split[Point]
    ) -> "TableGrid":
        """
        Convert two ``TableGrid`` objects into one, that is able to segment the original (non-cropped) image

        Args:
            split_grids (Split[TableGrid]): a Split of TableGrid objects of the left and right part of the table
            offsets (Split[tuple[int, int]]): a Split of the offsets in the image where the crop happened
        """

        def offset_points(points, offset):
            return [
                [(p[0] + offset[0], p[1] + offset[1]) for p in row] for row in points
            ]

        split_points = split_grids.apply(
            lambda grid, offset: offset_points(grid.points, offset), offsets
        )

        points = []

        rows = min(split_grids.left.rows, split_grids.right.rows)

        for row in range(rows + 1):
            row_points = []

            row_points.extend(split_points.left[row])
            row_points.extend(split_points.right[row])

            points.append(row_points)

        table_grid = TableGrid(points, split_grids.left.cols)

        return table_grid

    def save(self, path: str | Path):
        with open(path, "w") as f:
            json.dump({"points": self.points, "right_offset": self._right_offset}, f)

    @staticmethod
    def from_saved(path: str | Path) -> "TableGrid":
        with open(path, "r") as f:
            points = json.load(f)
            right_offset = points.get("right_offset", None)
            points = [[(p[0], p[1]) for p in pointes] for pointes in points["points"]]
            return TableGrid(points, right_offset)

    def add_left_col(self, width: int):
        for row in self._points:
            first = row[0]
            new_first = (first[0] - width, first[1])
            row.insert(0, new_first)

    def add_top_row(self, height: int):
        new_row = []
        for point in self._points[0]:
            new_row.append((point[0], point[1] - height))

        self.points.insert(0, new_row)

    def _surrounds(self, rect: list[Point], point: tuple[float, float]) -> bool:
        """point: x, y"""
        lt, rt, rb, lb = rect
        x, y = point

        top = _Rule(*lt, *rt)
        if top._y_at_x(x) > y:
            return False

        right = _Rule(*rt, *rb)
        if right._x_at_y(y) < x:
            return False

        bottom = _Rule(*lb, *rb)
        if bottom._y_at_x(x) < y:
            return False

        left = _Rule(*lb, *lt)
        if left._x_at_y(y) > x:
            return False

        return True

    def cell(self, point: tuple[float, float]) -> tuple[int, int]:
        for r in range(len(self._points) - 1):
            offset = 0
            for c in range(len(self.row(0)) - 1):
                if self._right_offset is not None and c == self._right_offset:
                    offset = -1
                    continue

                if self._surrounds(
                    [
                        self._points[r][c],
                        self._points[r][c + 1],
                        self._points[r + 1][c + 1],
                        self._points[r + 1][c],
                    ],
                    point,
                ):
                    return (r, c + offset)

        return (-1, -1)

    def cell_polygon(self, cell: tuple[int, int]) -> tuple[Point, Point, Point, Point]:
        r, c = cell

        self._check_row_idx(r)
        self._check_col_idx(c)

        if self._right_offset is not None and c >= self._right_offset:
            c = c + 1

        return (
            self._points[r][c],
            self._points[r][c + 1],
            self._points[r + 1][c + 1],
            self._points[r + 1][c],
        )

    def region(
        self, start: tuple[int, int], end: tuple[int, int]
    ) -> tuple[Point, Point, Point, Point]:
        r0, c0 = start
        r1, c1 = end

        self._check_row_idx(r0)
        self._check_row_idx(r1)
        self._check_col_idx(c0)
        self._check_col_idx(c1)

        if self._right_offset is not None and c0 >= self._right_offset:
            c0 = c0 + 1

        if self._right_offset is not None and c1 >= self._right_offset:
            c1 = c1 + 1

        lt = self._points[r0][c0]
        rt = self._points[r0][c1 + 1]
        rb = self._points[r1 + 1][c1 + 1]
        lb = self._points[r1 + 1][c0]

        return lt, rt, rb, lb

    def visualize_points(self, img: MatLike):
        """
        Draw the detected table points on the image for visual verification
        """
        import colorsys

        def clr(index, total_steps):
            hue = index / total_steps  # Normalized hue between 0 and 1
            r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            return int(r * 255), int(g * 255), int(b * 255)

        for i, row in enumerate(self._points):
            for p in row:
                cv.circle(img, p, 4, clr(i, len(self._points)), -1)

        imu.show(img)

    def text_regions(
        self, img: MatLike, row: int, margin_x: int = 10, margin_y: int = -3
    ) -> list[tuple[tuple[int, int], tuple[int, int]]]:
        def vertical_rule_crop(row: int, col: int):
            self._check_col_idx(col)
            self._check_row_idx(row)

            if self._right_offset is not None and col >= self._right_offset:
                col = col + 1

            top = self._points[row][col]
            bottom = self._points[row + 1][col]

            left = int(min(top[0], bottom[0]))
            right = int(max(top[0], bottom[0]))

            return img[
                int(top[1]) - margin_y : int(bottom[1]) + margin_y,
                left - margin_x : right + margin_x,
            ]

        result = []

        start = None
        for col in range(self.cols):
            crop = vertical_rule_crop(row, col)
            text_over_score = imu.text_presence_score(crop)
            text_over = text_over_score > -0.10

            if not text_over:
                if start is not None:
                    result.append(((row, start), (row, col - 1)))
                start = col

        if start is not None:
            result.append(((row, start), (row, self.cols - 1)))

        return result
