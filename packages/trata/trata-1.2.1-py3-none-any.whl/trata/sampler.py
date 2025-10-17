#! /usr/bin/env python

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import itertools
import math
import os
from copy import deepcopy
import warnings
import numpy as np

try:
    from scipy import optimize, stats
except:
    print("Could not import Scipy! Some features may not be availible.")


class SamplerMeta(type):
    def __str__(self):
        return "{} Sampler".format(self.name)

    def __repr__(self):
        return "{} Sampler".format(self.name)


class _Sampler(object):
    """
        Base class for all samplers.

        Provides the interface method 'sample_points'.
    """

    __metaclass__ = SamplerMeta

    def __str__(self):
        return str(type(self))

    def __repr__(self):
        return repr(type(self))


class ContinuousSampler(_Sampler):
    name = "Continuous"


class DiscreteSampler(_Sampler):
    name = "Discrete"

    @staticmethod
    def normalize_box(box, values):

        if box is None and values is None:
            raise TypeError("Must give at least one of 'box' and 'values'")
        if box is None:
            box = [[]] * len(values)
        if values is None:
            values = [[]] * len(box)

        new_box = []
        for i, (box_el, values_el) in enumerate(zip(box, values)):
            if len(box_el) != 0 and len(values_el) == 0:
                new_box.append(box_el)
            elif len(box_el) == 0 and len(values_el) != 0:
                new_box.append([0.0, 1.0])
            elif len(box_el) == 0 and len(values_el) == 0:
                raise ValueError("Either box or values must be specified. Neither found in dimension {}".format(i))
            else:
                raise ValueError("Only one of box or values can be specified. Found both in dimension {}".format(i))

        return new_box

    @staticmethod
    def unnormalize_points(box, values, points):
        if box is None:
            box = [[]] * len(values)
        if values is None:
            values = [[]] * len(box)

        points = points.astype('O')
        for i, point in enumerate(points):
            for j, (dim, box_el, values_el) in enumerate(zip(point, box, values)):
                if len(box_el) != 0 and len(values_el) == 0:
                    pass
                elif len(box_el) == 0 and len(values_el) != 0:
                    len_values_el = float(len(values_el))
                    for k, value in enumerate(values_el):
                        if (k / len_values_el) <= dim <= ((k + 1) / len_values_el):
                            points[i][j] = value
                else:
                    raise Exception("An error that should have been caught in 'normalize_box' wasn't caught")
        return points


class DiscreteOrderedSampler(DiscreteSampler):
    name = "Discrete Ordered"


class LatinHyperCubeSampler(ContinuousSampler, DiscreteOrderedSampler):
    """A sampler for creating latin hypercube sample sets."""

    name = "Latin HyperCube"

    @staticmethod
    def sample_points(num_points, box=None, values=None, geo_degree=None, seed=None, **kwargs):
        """
        Create a set of points in a random latin hypercube

        Ranges in each dimension are divided in to N sub-intervals, where N is the number of points. For each
        sample point, an interval is randomly selected from each dimension, and the point is selected uniformly
        within the intersection of those intervals. Once a point has been sampled from an interval, that interval
        can no longer be selected to be sampled from.

        Args:
            - num_points (int): The number of sample points
            - box ([[float]]): The bounding box. Discrete dimensions are an empty list.
            - values ([[~]]): A set of values for discrete variables. Continuous dimensions are an empty list.
            - geo_degree (float): Degree for geometric Latin Hypercube
            - seed (int): Random seed

        Returns (numpy array):
            - A two dimensional numpy array of sample points

        Raises:
            - ValueError
            - TypeError
        """

        ls_box = DiscreteOrderedSampler.normalize_box(box, values)
        i_num_dim = len(ls_box)
        i_num_points = int(num_points)
        if seed is not None:
            i_seed = int(seed)
            np.random.seed(i_seed)
        ls_points = []
        np_indices = np.arange(i_num_points)

        if geo_degree is None:  # perform standard latin hypercube sampling

            for iDim in range(i_num_dim):  # for each dimension
                np.random.shuffle(np_indices)
                ls_dim_limits = ls_box[iDim]
                f_dx = (ls_dim_limits[1] - ls_dim_limits[0]) / float(i_num_points)

                # sample uniformly from sub interval
                ls_points.append(ls_dim_limits[0] + (np_indices + np.random.uniform(0, 1, i_num_points)) * f_dx)

        else:  # 'geo_degree' in kwargs. Perform geometric latin hypercube sampling

            f_degree = float(geo_degree)

            # Values outside of this range cause solver to fail.
            if not 0.0 < f_degree < 2.0:
                raise ValueError("geo_degree must be within the range (0.0,2.0). Was given {}".format(f_degree))

            b_has_mid_pt = i_num_points % 2 == 1  # Midpoint exists only if nPts is odd

            for f_low, f_high in ls_box:
                f_mid_point = (f_high + f_low) / 2.
                if b_has_mid_pt:
                    f_delta = (f_high - f_low) / 8.
                    f_mid_low = f_mid_point - f_delta
                    f_mid_high = f_mid_point + f_delta
                    ls_middle = [(f_mid_low, f_mid_high)]
                else:
                    ls_middle = []
                    f_mid_low = f_mid_point

                ls_intervals = LatinHyperCubeSampler._make_intervals(i_num_points // 2, f_low, f_mid_low, f_degree)

                ls_high_intervals = [(2 * f_mid_point - b, 2 * f_mid_point - a) for a, b in reversed(ls_intervals)]
                ls_intervals.extend(ls_middle)
                ls_intervals.extend(ls_high_intervals)
                np_intervals = np.array(ls_intervals)
                del ls_intervals, ls_middle, ls_high_intervals

                np.random.shuffle(np_indices)

                ls_points.append([(np_intervals[i_x, 1] - np_intervals[i_x, 0]) * np.random.uniform(0, 1)
                                  + np_intervals[i_x, 0] for i_x in np_indices])

        return DiscreteSampler.unnormalize_points(box, values, np.array(ls_points).T)

    @staticmethod
    def _make_intervals(i_num_intervals, f_low, f_high, f_degree):
        """
        Create intervals for geometric latin hypercube.

        Args:
            - i_num_intervals (int): The number of intervals to create
            - f_low (float): The low end of the intervals
            - f_high (float): The high end of the intervals
            - f_degree (float): Determines how skewed to make the intervals

        Returns (list):
            - List of intervals
        """
        def _to_float(value):
            """Convert value to float, handling both numpy arrays and regular numbers."""
            if hasattr(value, 'item'):
                return float(value.item())
            return float(value)

        f_delta = (f_high - f_low) / (i_num_intervals ** f_degree)
        ls_poly = [1.0] * (i_num_intervals - 1)
        ls_poly[-1] = 1.0 - ((f_high - f_low) / f_delta)
        f_epsilon = optimize.root(lambda x: np.polyval(ls_poly, x), 1.).x

        ls_intervals = []
        f_a = f_low
        for _ in range(i_num_intervals):
            f_b = f_a + f_delta
            ls_intervals.append((_to_float(f_a), _to_float(f_b)))
            f_a = f_b
            f_delta = f_epsilon * f_delta

        return ls_intervals


class MonteCarloSampler(ContinuousSampler):
    """A sampler for creating standard monte carlo sample sets."""

    name = "Monte Carlo"

    @staticmethod
    def sample_points(num_points, box, seed=None, **kwargs):
        """
        Create a set of points using standard uniform monte carlo.

        Each dimension is sampled independently from a uniform distribution determined by 'box'.

        Args:
            - num_points (int): The number of sample points
            - box ([[float]]): The bounding box
            - seed (int): Random seed

        Returns (numpy array):
            - A two dimensional numpy array of sample points

        Raises:
            - ValueError
            - TypeError
        """

        ls_box = box
        i_num_points = int(num_points)
        if seed is not None:
            i_seed = int(seed)
            np.random.seed(i_seed)

        # Using python list comprehension
        return np.array([np.random.uniform(f_low, f_high, i_num_points) for f_low, f_high in ls_box]).T


class QuasiRandomNumberSampler(ContinuousSampler):
    """A sampler for creating quasi-random sample sets using scipy.stats.qmc."""

    name = "Quasi Random Number"

    @staticmethod
    def sample_points(num_points, box, technique='sobol', sequence_offset=0, scramble=False, seed=None, **kwargs):
        """
        Create a set of points using quasi-random numbers

        Produces a quasi-random set of points that tends to evenly cover space. The sampler will always produce
        the same sequence given the same inputs (unless scrambling is enabled).

        Note: Sobol sequences have optimal properties when num_points is a power of 2 (e.g., 64, 128, 256, 512).

        Args:
            - num_points (int): the number of sample points
            - box ([[float]]): The bounding box
            - technique (string): Which type of sequence to use; either 'sobol' or 'halton'. Sobol is the default.
            - sequence_offset (int): Starting position in the sequence (default: 0)
                Use this to continue a sequence across multiple calls
            - scramble (bool): Whether to scramble the sequence for better randomization (default: False)
            - seed (int): Random seed for reproducibility when scrambling (default: None)

        Returns (numpy array):
            - A two dimensional numpy array of sample points

        Raises:
            - ValueError: If technique is not 'sobol' or 'halton'
        """
        from scipy.stats import qmc

        technique = str(technique).lower()

        if technique not in ['sobol', 'halton']:
            raise ValueError(f"Value given for 'technique' is invalid: {technique}. Must be 'sobol' or 'halton'")

        # Validate box format
        if not isinstance(box, (list, np.ndarray)):
            raise TypeError("'box' must be a list or array")

        # Check if box is 2D (list of lists)
        try:
            box_array = np.array(box)
            if box_array.ndim != 2:
                raise TypeError("'box' must be a 2D array-like structure (list of [min, max] pairs)")
            if box_array.shape[1] != 2:
                raise TypeError("Each dimension in 'box' must have exactly 2 values [min, max]")
        except (ValueError, IndexError) as e:
            raise TypeError("'box' must be a 2D array-like structure (list of [min, max] pairs)") from e

        ls_box = box
        i_num_points = int(num_points)
        n_dim = len(ls_box)

        # Create the appropriate sampler
        if technique == 'sobol':
            sampler = qmc.Sobol(d=n_dim, scramble=scramble, seed=seed)
        else:  # technique == 'halton'
            sampler = qmc.Halton(d=n_dim, scramble=scramble, seed=seed)

        # Fast forward to the desired position in the sequence
        if sequence_offset > 0:
            sampler.fast_forward(sequence_offset)

        # Generate points in [0, 1)^d
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message="The balance properties of Sobol")
            points_unit = sampler.random(i_num_points)

        # Convert box to numpy array and slice
        box_array = np.array(ls_box)
        l_bounds = box_array[:, 0]  # First column: lower bounds
        u_bounds = box_array[:, 1]  # Second column: upper bounds

        points_scaled = qmc.scale(points_unit, l_bounds, u_bounds)

        return points_scaled


class CenteredSampler(ContinuousSampler):
    """A sampler for creating sample sets with centered points."""

    name = "Centered"

    @staticmethod
    def sample_points(num_divisions, box,
                      default=None, technique=None, num_points=10, seed=None, **kwargs):
        """
        Create a set of points centered using a default point or generated points

        Generates a line of points in across a single dimension, while holding the other dimensions constant at the
        center point. Points in the varying-dimension will range based on the box range in that dimension.

        Args:
            - num_divisions (int or [int]): The number of sample points in a given dimension
            - box ([[float]]): The bounding box
            - default ([float]): The point at which the lines of points is centered. Elements of points in non-varying dimensions will all equal the corresponding element from the default.
            - technique (string): Whether to perform standard or latin hypercube centered sampling
            - num_points (int): The number of points to generate for latin hypercube centered sampling
            - seed (int): Random seed for latin hypercube centered sampling

        Returns (numpy array):
            - A two dimensional numpy array of sample points

        Raises:
            - ValueError
            - TypeError
            - IndexError: If dim_indices is beyond the number of dimensions in box
        """

        ls_points = []

        ls_box = box

        if isinstance(num_divisions, int):
            ls_num_divisions = [num_divisions] * len(ls_box)
        else:
            ls_num_divisions = num_divisions

        if technique is not None:
            if technique == 'lhs_vals':
                i_num_points = int(num_points)
                if seed is not None:
                    np_default_points = LatinHyperCubeSampler.sample_points(box=ls_box, num_points=i_num_points,
                                                                            seed=seed)
                else:
                    np_default_points = LatinHyperCubeSampler.sample_points(box=ls_box, num_points=i_num_points)
            else:
                raise ValueError('Invalid technique')
        elif default is not None:
            ls_point = deepcopy(default)

            if len(ls_point) != len(ls_box):
                raise ValueError('Default not the same dimension as box')
            else:
                np_default_points = np.array([ls_point], dtype=float)
        else:
            raise ValueError("Either 'default' or 'technique' must be given")

        for np_default_point in np_default_points:
            for i_index in range(len(ls_box)):

                ls_limit = ls_box[i_index]

                np_new_point = deepcopy(np_default_point)
                f_increment = (float(ls_limit[1]) - float(ls_limit[0])) / (ls_num_divisions[i_index] - 1)
                np_new_point[i_index] = ls_limit[0] - f_increment

                for _ in range(ls_num_divisions[i_index]):
                    np_new_point = deepcopy(np_new_point)
                    np_new_point[i_index] += f_increment
                    ls_points.append(np_new_point)

        return np.array(ls_points)


class OneAtATimeSampler(ContinuousSampler):
    """A sampler for creating sample sets varying each dimension one at a time."""
    name = "List"

    @staticmethod
    def sample_points(box, default=None, use_low=False, use_high=False, use_default=False, do_oat=False, **kwargs):
        """
        Create a set of points varying each dimension one at a time        

        Generates a set of points with each dimension taking on its high and low values once, keeping all
        other dimensions constant at the default point. Can also include points with all dimensions set at the high
        value and the low value, as well as the default point itself.

        Args:
            - box ([[float]]): The bounding box
            - default ([float]): The default center point. Required when use_default=True or do_oat=True.
            - use_low (bool): Whether to include a point with all the low values from 'box'
            - use_high (bool): Whether to include a point with all the high values from 'box'
            - use_default (bool): Whether to include the default point. Note: when do_oat=True, 
              the default point is automatically included as the base point, so this flag is ignored.
            - do_oat (bool): Whether to perform one-at-a-time sampling. Each dimension is chosen
              one at a time to use the high and low value in that dimension. The other dimensions'
              values for the point come from the given default value. When True, the default point
              is always placed first in the returned array.

        Returns (numpy array):
            - A two dimensional numpy array of sample points. When do_oat=True (only), returns 
              exactly 2*n+1 points where n is the number of dimensions.

        Raises:
            - ValueError: If default is None when required, or if default has incorrect dimensions
            - TypeError: If box has invalid structure or type
        """

        # Validate that default is provided when needed
        if (use_default or do_oat) and default is None:
            raise ValueError("'default' parameter is required when use_default=True or do_oat=True")

       # Validate default has correct dimensions when provided
        if default is not None and len(default) != len(box):
            raise ValueError(f"Default point has {len(default)} dimensions, but box has {len(box)} dimensions")
    
        ls_points = []
        
        # Handle corner points (all-low, all-high, default)
        if use_low:
            ls_points.append([box[j][0] for j in range(len(box))])
        if use_high:
            ls_points.append([box[j][1] for j in range(len(box))])
        if use_default and not do_oat:   # Only add default if NOT doing OAT
            ls_points.append(list(default))
        
        # Handle OAT sampling
        if do_oat:
            # ALWAYS include the base point first for OAT
            ls_points.insert(0, list(default))  # Put at beginning
            
            # Add variations for each dimension
            for i in range(len(box)):
                # Low variation for dimension i
                point_low = list(default)
                point_low[i] = float(box[i][0])
                ls_points.append(point_low)
                
                # High variation for dimension i
                point_high = list(default)
                point_high[i] = float(box[i][1])
                ls_points.append(point_high)
        
        return np.array(ls_points)


class DefaultValueSampler(ContinuousSampler):
    """A sampler for creating sample sets only using a default point."""

    name = "Default Value"

    @staticmethod
    def sample_points(num_points, default, box=None, **kwargs):
        """
        Create a set of default points.

        Generates an array 'num_points' long simply repeating the default point.

        Args:
            - num_points (int): The number of sample points
            - default ([float]): The point to repeat
            - box ([[float]]): The bounding box. Used for error checking the dimension of 'default'

        Returns (numpy array):
            - A two dimensional numpy array of sample points

        Raises:
            - ValueError
            - TypeError
        """

        i_num_points = int(num_points)
        np_default = np.array(default)

        if box is not None:
            ls_box = box
            if len(np_default) != len(ls_box):
                raise ValueError('Default not the same dimension as box')

        return np.tile(np_default, (i_num_points, 1))


class CornerSampler(ContinuousSampler, DiscreteOrderedSampler):
    """A sampler for creating sample sets of corners."""

    name = "Corners"

    @staticmethod
    def sample_points(box=None, values=None, num_points=None, **kwargs):
        """
        Create a set of corner points.

        Generates a set of points at the corners of the bounding box. If the number of points requested does not equal
        the number of corners (2^N for N==num_dimesions), then the sampler will return the number requested. If the
        number of points is greater than 2^N, then the set of 2^N will be repeated until num_points have been given.

        Args:
            - box ([[float]]): The bounding box. Discrete dimensions are an empty list.
            - values ([[~]]): A set of values for discrete variables. Continuous dimensions are an empty list.
            - num_points (int): The number of sample points

        Returns (numpy array):
            - A two dimensional numpy array of sample points

        Raises:
            - ValueError
            - TypeError
        """
        ls_box = DiscreteOrderedSampler.normalize_box(box, values)
        i_num_dim = len(ls_box)

        if num_points is not None:
            i_num_points = int(num_points)
        else:
            i_num_points = 2 ** i_num_dim

        ls_points = []

        # Count up in binary
        for i in range(i_num_points):
            str_binary_string = bin(i % 2 ** i_num_dim)[2:].rjust(i_num_dim, '0')
            ls_point = []

            # Each dimension corresponds with a place value in the binary number.
            # For each dimension use the upper bound if 1 and the lower bound if 0
            for j in range(i_num_dim):
                if str_binary_string[j] == '0':
                    ls_point.append(ls_box[j][0])
                else:
                    ls_point.append(ls_box[j][1])

            ls_points.append(ls_point)

        return DiscreteOrderedSampler.unnormalize_points(box, values, np.array(ls_points))


class UniformSampler(ContinuousSampler):
    """A sampler for creating sample sets of a uniform line."""

    name = "Uniform"

    @staticmethod
    def sample_points(num_points, box, equal_area_divs=False, **kwargs):
        """
        Create a set points in a line from the low corner to the high corner.

        Each dimension is divided into 'nPts' linearly spaced points. If 'equal_area_divs' is set
        the points will be placed in the middle of the divisions instead of on the edges. The result is a line of
        points from the corner of all low extents to the corner of all high extents.

        Args:
            - num_points (int): The number of sample points
            - box ([[float]]): The bounding box
            - equal_area_divs (bool): Whether to place points in the center of the division areas or at the edges

        Returns (numpy array):
            - A two dimensional numpy array of sample points

        Raises:
            - ValueError
            - TypeError
        """

        np_box = np.array(box)
        if len(np_box.shape) != 2:
            raise ValueError('Box must be two dimensional')

        i_num_dim = len(np_box)

        i_num_div = [int(num_points)] * i_num_dim

        ls_points = []
        for i_dim in range(i_num_dim):
            i_num_dim_div = i_num_div[i_dim]

            if equal_area_divs:

                # Generate n+1 linearly spaced points
                # Use the mid-points of those points
                np_points = np.linspace(np_box[i_dim][0], np_box[i_dim][1], i_num_dim_div + 1)
                ls_points.append([(np_points[i] + np_points[i + 1]) / 2.0 for i in range(i_num_dim_div)])

            # If only only one division in dimension, just use the midpoint between high and low
            elif i_num_dim_div == 1:
                ls_points.append([(np_box[i_dim][0] + np_box[i_dim][1]) / 2.0])

            else:
                ls_points.append(np.linspace(np_box[i_dim][0], np_box[i_dim][1], i_num_dim_div))

        return np.array(ls_points).T


class CartesianCrossSampler(ContinuousSampler, DiscreteSampler):
    """A sampler for creating sample sets of a Cartesian product."""

    name = "Cartesian Cross"

    @staticmethod
    def sample_points(num_divisions, values=None, box=None, equal_area_divs=False, **kwargs):
        """
        Creates a set of points that is the the Cartesian product of the given variables.

        The continuous dimension's values are a linear spacing of the range given through the 'box' keyword.
        The discrete dimension's values are given through the 'value' keyword.

        Example:
            * sample_points(box=[[0,1],[0,1]], num_divisions=3)
                - returns 9 points, with 3 divisions in each dimension

            * sample_points(box=[[0,1],[0,1]], num_divisions=[3,4])
                - returns 12 points, with 3 divisions in the first dimension, and 4 divisions in the second

            * sample_points(box=[[0,1],[0,1]], num_divisions=[[.5,.75],[.3,.32]])
                - returns 4 points, the first dimension having values of .5 and .75, and the second dimension having values of .3 and .32

        Args:
            - num_divisions (int, [int], [[int]]): Number of divisions in each dimension.
                                                 * An integer value will produce that many divisions in all dimensions.
                                                 * An array-like [] value will produce the number of divisions mapping each value to the corresponding dimension.
                                                 * An array-like [[]] value will specify the exact values on which to create the points.
            - values ([[~]]): A set of values for discrete variables. Continuous dimensions are an empty list.
            - box ([[float]]): The bounding box for continuous variables. Discrete dimensions are an empty list.
            - equal_area_divs (bool): Whether to place points in the center of the division areas or at the edges

        Returns (numpy array):
            - A two dimensional numpy array of sample points

        Raises:
            - ValueError
            - TypeError
        """

        if len(np.array(box, dtype=object).shape) > 2:
            raise ValueError('Box cannot have more than 2 dimensions')
        if box != None and not any(isinstance(_, list) for _ in box):
            raise TypeError("Type of 'box' must be list [[float]]")

        np_box = np.array(DiscreteSampler.normalize_box(box, values), dtype='float')
        i_num_dim = np_box.shape[0]

        if isinstance(num_divisions, int):
            # Use the same number of divisions for each dimension
            np_num_div = np.repeat(num_divisions, i_num_dim).astype('int')
            if i_num_dim != np_num_div.shape[0]:
                raise ValueError("Length of box != Length of num_divisions")
        elif isinstance(num_divisions, list):
            np_num_div = np.array(num_divisions, dtype='int')
            if i_num_dim != np_num_div.shape[0]:
                raise ValueError("Length of box != Length of num_divisions")
        else:
            raise TypeError("Type of 'num_divisions' must be either 'int' or '[int]'. "
                            "Was given type '{}'".format(type(num_divisions)))

        if equal_area_divs:
            diff = (np_box[:, 1] - np_box[:, 0]) / np_num_div
            np_box[:, 0] += .5 * diff
            np_box[:, 1] -= .5 * diff

        np_mgrid = np.mgrid[[slice(b[0], b[1], 1j * r) for b, r in zip(np_box, np_num_div)]]

        np_points = np.moveaxis(np_mgrid, 0, -1).reshape(-1, i_num_dim)

        return DiscreteSampler.unnormalize_points(box, values, np_points)


class SamplePointsSampler(ContinuousSampler, DiscreteOrderedSampler):
    """A sampler for creating sample sets of a given set of points."""

    name = "Sample Points"

    @staticmethod
    def sample_points(samples, **kwargs):
        """
        Create a set of points using a given list.

        Generates the points given from 'samples'.

        Args:
            - samples ([[~]]): The list of sample points to use

        Returns (numpy array):
            - A two dimensional numpy array of sample points

        Raises:
            - TypeError
        """

        np_samples = np.array(samples, dtype='O')

        # Ensure samples is at least 2D
        if np_samples.ndim < 2:
            raise TypeError("Samples must be a 2D array-like structure")

        lengths = np.apply_along_axis(len, 1, np_samples)

        # assume that the first point is correct
        incorrect_length_locations = np.argwhere(lengths != lengths[0]).flatten()

        if len(incorrect_length_locations) > 0:
            raise ValueError("Given sample(s) at index {} have an incorrect length".format(incorrect_length_locations))

        if len(np_samples.shape) != 2:
            raise TypeError("Samples must 2 dimensional."
                            "Samples dimension was {}".format(len(np_samples.shape)))

        return np_samples


class RejectionSampler(ContinuousSampler):
    """A sampler for creating sample sets using a rejection algorithm."""

    name = "Rejection"

    @staticmethod
    def sample_points(num_points, box, func, seed=None, metropolis=False, burn_in=None, **kwargs):
        """
        Create a set of points using a rejection algorithm.

        Generates points using rejection sampling. A candidate point is generated uniformly in the bounding box.
        The function's value at that candidate point is tested against a value produced from a uniform distribution
        ranging from zero to the function's maximum. If the function's value is less than the uniform value the
        point is accepted and placed in the list of accepted points. Otherwise, the point is rejected. This process
        is repeated until there are nPts in the list of accepted points.

        If 'metropolis' is True, then the Metropolis MCMC algorithm is used instead.

        Args:
            - num_points (int): The number of sample points
            - box ([[float]]): The bounding box
            - func (function): Numeric function to sample as a probability distribution. Must be positive within bounding box.
            - seed (int): The random seed
            - metropolis (bool): Whether to use the Metropolis MCMC algorithm. Otherwise, standard rejection algorithm.
            - burn_in (int): How many samples to generate for MCMC burn in period

        Returns (numpy array):
            - A two dimensional numpy array of sample points

        Raises:
            - ValueError
            - TypeError
        """

        ls_box = box
        i_num_points = int(num_points)
        fn_func = func
        if seed is not None:
            i_seed = int(seed)
            np.random.seed(i_seed)

        ls_points = []
        np_midpoints = np.array([(ls_box[i][1] + ls_box[i][0]) / 2.0 for i in range(len(ls_box))])
        if metropolis:
            if burn_in is not None:
                i_burn_in = int(burn_in)
            else:
                i_burn_in = 0
            i = 0
            np_x = np_midpoints
            while i < i_num_points + i_burn_in:
                b_in_range = True

                # Current candidate is based on previous accepted value.
                # i.e. the previous accepted value acts as the mean of distribution for selecting the next candidate
                np_z = np.random.normal(np_x, 1.0)

                for z_i, box_i in zip(np_z, ls_box):
                    # Automatically reject candidates that are outside the bounding box
                    if not box_i[0] < z_i < box_i[1]:
                        b_in_range = False

                # Always accept if candidate point is in higher density than previous point (f(z)>f(x) => f(z)/f(x)>1)
                # Sometimes accept if candidate point is in lower density than previous point
                if b_in_range and (fn_func(np_z) / fn_func(np_x)) > np.random.rand():
                    np_x = np_z
                    i += 1
                    if i > i_burn_in:  # Throw away burn in accepts
                        ls_points.append(np_x)
                else:
                    i += 1
                    if i > i_burn_in:
                        ls_points.append(np_z)

        else:
            np_max_x = optimize.minimize(lambda x: -1.0 * fn_func(x),
                                         np_midpoints, bounds=ls_box, method='SLSQP', tol=1e-1000).x
            np_max_y = fn_func(np_max_x)

            for n in range(i_num_points):
                b_fail = True

                # Try until we get find a successful point
                while b_fail:
                    # Generate candidate point
                    np_point = np.array([np.random.uniform(ls_box[i][0], ls_box[i][1]) for i in range(len(ls_box))])

                    # Check against uniform value.
                    # If u~U(0,max(f)), then P(f(candidate) > u) is large when f(candidate) is large
                    if fn_func(np_point) > np.random.uniform(0.0, np_max_y):
                        ls_points.append(np_point)
                        b_fail = False

        return np.array(ls_points)


def _auto_fit_to_box(dist_name, low, high, user_params):
    """Auto-fit distribution to box bounds if no conflicting params provided"""
    params = user_params.copy()
    
    if dist_name == 'uniform':
        if 'loc' not in params and 'scale' not in params:
            params['loc'] = low
            params['scale'] = high - low
    elif dist_name == 'norm':
        if 'loc' not in params:
            params['loc'] = (low + high) / 2
        if 'scale' not in params:
            params['scale'] = (high - low) / 4
    # For other distributions, just use user params as-is
    
    return params


class ProbabilityDensityFunctionSampler(ContinuousSampler):
    """A sampler for creating sample sets from probability distributions."""

    name = "Probability Density Function"

    @staticmethod
    def sample_points(num_points, box=None, num_dim=None, dist='uniform', 
                            seed=None, **dist_params):
        """
        Sample from any scipy distribution

        Parameters:
        - num_points: number of samples
        - box: [[low, high], ...] bounds for each dimension (optional)
        - num_dim: number of dimensions if box not provided (optional) 
        - dist: scipy distribution name (e.g., 'uniform', 'norm', 'beta', 'gamma')
        - seed: random seed
        - **dist_params: distribution parameters (loc, scale, a, b, etc.)
                         Can be scalars (same for all dims) or lists (per dimension)
        """
        if seed is not None:
            np.random.seed(seed)

        # Determine number of dimensions
        if box is not None and num_dim is not None:
            raise ValueError("Provide either 'box' or 'num_dim', not both")
        elif box is not None:
            num_dimensions = len(box)
        elif num_dim is not None:
            num_dimensions = int(num_dim)
            box = None  # No bounds when using num_dim
        else:
            raise ValueError("Must provide either 'box' or 'num_dim'")

        # Get distribution from scipy.stats
        try:
            distribution = getattr(stats, dist)
        except AttributeError:
            raise ValueError(f"Distribution '{dist}' not found in scipy.stats")

        points = []

        for i in range(num_dimensions):
            # Extract parameters for this dimension
            dim_params = {}
            for param_name, param_value in dist_params.items():
                if isinstance(param_value, (list, tuple, np.ndarray)):
                    if len(param_value) != num_dimensions:
                        raise ValueError(f"Parameter '{param_name}' length must match dimensions")
                    dim_params[param_name] = param_value[i]
                else:
                    # Scalar value - use same for all dimensions
                    dim_params[param_name] = param_value

            # Handle automatic box fitting for common distributions
            if box is not None:
                low, high = box[i]
                dim_params = _auto_fit_to_box(dist, low, high, dim_params)

            scipy_params = {}
            known_scipy_params = ['loc', 'scale', 'a', 'b', 'df', 's', 'size']  # extend as needed
            for key, value in dim_params.items():
                if key in known_scipy_params:
                    scipy_params[key] = value

            # Generate samples for this dimension
            samples = distribution.rvs(size=int(num_points), **scipy_params)

            # Clip to box bounds if provided
            if box is not None:
                low, high = box[i]
                samples = np.clip(samples, low, high)

            points.append(samples)

        return np.array(points).T


class MultiNormalSampler(ContinuousSampler):
    """A sampler for creating sample sets from a multi-variate normal distribution."""

    name = "Multi-variate Normal"

    @staticmethod
    def sample_points(num_points, mean=None, covariance=None, seed=None, **kwargs):
        """
        Create a set of points from a multi-variate normal distribution

        Gives points sampled from scipy's multivariate gaussian normal distribution.

        Args:
            - num_points (int): The number of sample points
            - mean ([float]): n-dimensional vector of the distribution mean
            - covariance ([[float]]): n-by-n symmetric positive semi-definite matrix of the distribution covariance
            - seed (int): Random seed

        Returns (numpy array):
            - A two dimensional numpy array of sample points

        Raises:
            - ValueError
            - TypeError
        """

        i_num_points = int(num_points)
        if seed is not None:
            i_seed = int(seed)
            np.random.seed(i_seed)

        obj_dist = stats.multivariate_normal(mean=mean, cov=covariance)

        np_points = obj_dist.rvs(i_num_points)

        if len(np_points.shape) < 2:
            return np.array([np_points]).T
        else:
            return np_points


class FaceSampler(ContinuousSampler):
    """A sampler for creating sample sets on the faces of a hyper-volume"""

    name = "Face"

    @staticmethod
    def sample_points(box, num_divisions, equal_area_divs=False, **kwargs):
        """
        Create a set of points on the faces of the hyper-volume

        Performs Cartesian Cross sampling in N-1 dimensions on each face of the hyper-volume.

        Args:
            - box ([[float]]): The bounding box. Defines an N dimension hyper-volume
            - num_divisions (int, [int], [[int]]): Number of divisions in each dimension.
                                        - An integer value will produce that many divisions in all dimensions.
                                        - An array-like [] value will produce the number of divisions mapping each value to the corresponding dimension.
                                        - An array-like [[]] value will specify the exact values on which to create the points.
            - equal_area_divs (bool): Whether to place points in the center of the division areas or at the edges

        Returns (numpy array):
            - A two dimensional numpy array of sample points

        Raises:
            - ValueError
            - TypeError
        """

        ls_box = box

        i_num_dim = len(ls_box)

        if isinstance(num_divisions, int):
            ls_num_div = [num_divisions] * i_num_dim
        else:
            ls_num_div = num_divisions
            if i_num_dim != len(ls_num_div):
                raise ValueError("Length of box != Length of num_divisions")

        ls_points = []
        for _ in range(i_num_dim):
            ls_alt_num_div = deepcopy(ls_num_div)

            # # Replace i-th division in nDim with a list containing the range extent (low or high) in that dimension
            # ls_alt_num_div[i] = ls_box[i][0]  #removed outer brackets

            # Then perform cartesian cross sampling with the altered divisions
            ls_points.append(CartesianCrossSampler.sample_points(box=ls_box, num_divisions=ls_alt_num_div))

            # ls_alt_num_div[i] = ls_box[i][1]    #removed outer brackets
            # ls_points.append(CartesianCrossSampler.sample_points(box=ls_box, num_divisions=ls_alt_num_div))

        np_points = np.concatenate(ls_points, axis=0)

        # Remove duplicates
        return np.unique(np_points.astype(float), axis=0)


class _FractionalHelperTable(object):
    # table[dimensions][resolution][fraction]
    _generator_table = {
        3: {3: {1: (np.array([True, True]),), }, },
        4: {
            3: {1: (np.array([True, True, True]),), },
            4: {1: (np.array([True, True, True]),), },
        },
        5: {
            3: {
                2: (
                    np.array([True, True, False]),
                    np.array([True, False, True]),
                ),
            },
            4: {1: (np.array([True, True, True, True]),), },
            5: {1: (np.array([True, True, True, True]),), },
        },
        6: {
            3: {
                3: (
                    np.array([True, True, False]),
                    np.array([True, False, True]),
                    np.array([False, True, True]),
                ),
            },
            4: {
                2: (
                    np.array([True, True, True, False]),
                    np.array([True, True, False, True]),
                ),
            },
            5: {1: (np.array([True, True, True, True, True]),), },
            6: {1: (np.array([True, True, True, True, True]),), },
        },
        7: {
            3: {
                4: (
                    np.array([True, True, False]),
                    np.array([True, False, True]),
                    np.array([False, True, True]),
                    np.array([True, True, True]),
                ),
            },
            4: {
                3: (
                    np.array([True, True, True, False]),
                    np.array([True, True, False, True]),
                    np.array([True, False, True, True]),
                ),
                2: (
                    np.array([True, True, True, False, False]),
                    np.array([True, True, False, True, True]),
                ),
            },
            5: {1: (np.array([True, True, True, True, True, True]),), },
            6: {1: (np.array([True, True, True, True, True, True]),), },
            7: {1: (np.array([True, True, True, True, True, True]),), },
        },
        8: {
            3: {
                4: (
                    np.array([True, True, True, False]),
                    np.array([True, True, False, True]),
                    np.array([True, False, True, True]),
                    np.array([False, True, True, True]),
                ),
            },
            4: {
                4: (
                    np.array([True, True, True, False]),
                    np.array([True, True, False, True]),
                    np.array([True, False, True, True]),
                    np.array([False, True, True, True]),
                ),
                3: (
                    np.array([True, True, True, False, False]),
                    np.array([True, True, False, True, True]),
                    np.array([True, False, True, True, True]),
                ),
            },
            5: {
                2: (
                    np.array([True, True, True, True, False, False]),
                    np.array([True, True, False, False, True, True]),
                ),
            },
            6: {
                1: (np.array([True, True, True, True, True, True, True]),),
            },
            7: {
                1: (np.array([True, True, True, True, True, True, True]),),
            },
            8: {
                1: (np.array([True, True, True, True, True, True, True]),),
            }
        }
    }

    # table[dimensions][fraction]
    _resolution_table = {
        3: {1: 3, },
        4: {1: 4, },
        5: {
            2: 3,
            1: 5,
        },
        6: {
            3: 3,
            2: 4,
            1: 6,
        },
        7: {
            4: 3,
            3: 4,
            2: 4,
            1: 7,
        },
        8: {
            4: 4,
            3: 4,
            2: 5,
            1: 8,
        },
    }

    # table[dimension][resolution]
    _fraction_table = {
        3: {3: 1, },
        4: {
            3: 1,
            4: 1,
        },
        5: {
            3: 2,
            4: 1,
            5: 1,
        },
        6: {
            3: 3,
            4: 2,
            5: 1,
            6: 1,
        },
        7: {
            3: 4,
            4: 3,
            5: 1,
            6: 1,
            7: 1,
        },
        8: {
            3: 4,
            4: 4,
            5: 2,
            6: 1,
            7: 1,
            8: 1,
        },
    }

    @staticmethod
    def get_el(r, f, d):
        if r is None and f is None:
            raise ValueError("At least one of 'resolution' or 'fraction' must be specified")

        if r is None:
            try:
                r = _FractionalHelperTable._resolution_table[d][f]
            except KeyError:
                raise ValueError("Not supported for 'dimension'={} and 'fraction'={}".format(d, f))

        if f is None:
            try:
                f = _FractionalHelperTable._fraction_table[d][r]
            except KeyError:
                raise ValueError("Not supported for 'dimension'={} and 'resolution'={}".format(d, r))

        try:
            return _FractionalHelperTable._generator_table[d][r][f], r, f
        except KeyError:
            raise ValueError("Not supported for 'dimension'={}, 'resolution'={}, and 'fraction'={}".format(d, r, f))


class FractionalFactorialSampler(ContinuousSampler, DiscreteOrderedSampler):
    name = "Fractional Factorial"

    @staticmethod
    def sample_points(box=None, values=None, resolution=None, fraction=None, seed=None, **kwargs):
        """

        Creates a set of points based on a fractional factorial design

        Creates a set of points that will be a fractional factorial design of either a specified fraction or resolution.
        The sample set resolution will be at least the value specified, though it may be greater.
        If only resolution is specified, the design with the largest possible fraction will be chosen.
        If only fraction is specified, the design with the largest possible resolution will be chosen.

        This strategy will generate 2**(dim-fraction) points where 'dim' is the dimensionality of the sampling space and fraction is the given or selected fraction.

        Only one of 'fraction' and 'resolution' need to be given


        Args:
            - box ([[float]]): the bounding box
            - fraction (int):
            - resolution (int):

        Returns (numpy array):
            - A two dimensional numpy array of sample points

        Raises:
            - ValueError
        """
        if seed is not None:
            np.random.seed(seed)

        ls_box = DiscreteOrderedSampler.normalize_box(box, values)
        i_num_dim = len(ls_box)

        if i_num_dim < 2:
            raise ValueError("Fractional factorial sampling requires at least 2 parameters")

        generator_arrays, resolution, fraction = _FractionalHelperTable.get_el(resolution, fraction, i_num_dim)
        i_num_points = 2 ** (i_num_dim - fraction)

        # generate binary arrays

        np_binary_array = np.array(
            [[int(el) for el in bin(i % i_num_points)[2:].rjust(i_num_dim - fraction, '0')] for i in
             range(i_num_points)])

        new_arrays = [np.reshape(np_binary_array[:, gen].sum(axis=1) % 2, (-1, 1)) for gen in generator_arrays]
        new_arrays.append(np_binary_array)
        generated_array = np.hstack(new_arrays)

        # permute columns

        permuted_array = np.random.permutation(generated_array.T).T

        # randomly bit flip by columns

        bit_flips = np.random.randint(0, 2, i_num_dim)
        bit_flipped_array = np.bitwise_xor(permuted_array, bit_flips)

        # extract from box

        points = np.array([[ls_box[i][el] for i, el in enumerate(row)] for row in bit_flipped_array])

        return DiscreteOrderedSampler.unnormalize_points(box, values, points)


class MorrisOneAtATimeSampler(ContinuousSampler):
    name = 'Morris One at a Time'

    @staticmethod
    def sample_points(box, num_paths=1, seed=None, **kwargs):
        rng = np.random.default_rng(seed)

        box = np.array(box)
        k = box.shape[0]

        def make_path():
            B = np.ones(shape=(k + 1, k), dtype='int')
            B[np.triu_indices_from(B)] = 0
            B = rng.permutation(B, axis=1)
            x1, x2 = rng.uniform(box[:, 0], box[:, 1], (2, k))

            return x1 * B + x2 * (B ^ 1)

        return np.vstack([make_path() for _ in range(num_paths)])

class SobolIndexSampler(ContinuousSampler):
    """A sampler for creating sample sets for Sobol indices."""

    name = "Sobol Indices"

    @staticmethod
    def sample_points(
        num_points, box, include_second_order=False, scramble=True, seed=None, **kwargs
    ):
        """
        Create a set of points for Sobol indices calculation

        Produces a quasi-random set of points using scipy's qmc
        If 'include_second_order' is False, there will be
        2 ** num_points * (k + 2) rows.
        If 'include_second_order' is True, there will be
        2 ** num_points * (2k + 2) rows,
        where k is the number of parameters.

        Args:
            - num_points (int): Log in base 2 of the number of sample points
            - box ([[float]]): The bounding box
            - include_second_order (bool): Whether to include second order indices
            - scramble (bool): Whether to use scrambling in Sobol sequences
            - seed (int): Random seed

        Returns (numpy array):
            - A two dimensional numpy array of sample points
        """
        k = len(box)
        if not isinstance(num_points, int):
            raise TypeError(f"num_points should be an int. Was given {type(num_points)}")

        if scramble:
            qmc_sampler = stats.qmc.Sobol(d=2 * k, scramble=True, seed=seed)
        else:
            qmc_sampler = stats.qmc.Sobol(d=2 * k, scramble=False)

        qmc_sample = qmc_sampler.random_base2(m=num_points)
        l_bounds = [lb[0] for lb in box] * 2
        u_bounds = [ub[1] for ub in box] * 2
        sobol_points = stats.qmc.scale(qmc_sample, l_bounds, u_bounds)

        A = sobol_points[:, :k]
        B = sobol_points[:, -k:]
        M = np.append(A, B, axis=0)

        for i in range(k):
            AB_i = A.copy()
            AB_i[:, i] = B[:, i]
            M = np.append(M, AB_i, axis=0)

        if include_second_order:
            for i in range(k):
                BA_i = B.copy()
                BA_i[:, i] = A[:, i]
                M = np.append(M, BA_i, axis=0)

        return M


class DakotaSampler(ContinuousSampler):
    """A sampler for creating sample sets from Dakota"""

    name = "Dakota"

    @staticmethod
    def sample_points(sampling_type, box, default, dakota_path, input_file_path, variables, num_obj_fns, **kwargs):
        """
        Create a set of points using Dakota

        Args:
            - sampling_type (string): Which type of Dakota sampling to perform: nond, dace, or moat
            - box ([[float]]): The bounding box
            - default([float]): The default point
            - dakota_path (string): The relative path to the Dakota executable
            - input_file_path (string): The relative path to where the Dakota input file should be created
            - variables ([string]): List of variable names
            - num_obj_fns (int): The number of objective functions
            - \*\*kwargs: Any other key value pairs to be passed to Dakota

        Returns (numpy array):
            - A two dimensional numpy array of sample points

        Raises:
            - ValueError
            - TypeError
        """

        import os

        str_sampling_type = str(sampling_type)
        ls_box = box
        ls_default = default

        str_dakota_path = str(dakota_path)

        str_input_file_path = str(input_file_path)

        str_file_text = ""

        str_file_text += "strategy,\t\t\t\t\t\t\t\\\n"
        str_file_text += "\tsingle_method\t\t\t\t\t\t\\\n"
        str_file_text += "\titerator_static_scheduling\t\t\t\t\\\n"
        str_file_text += "\n"
        str_file_text += "method,\t\t\t\t\t\t\t\t\\\n"

        if str_sampling_type == 'nond':
            str_file_text += "\tnond_sampling \\\n"
        elif str_sampling_type == 'dace':
            str_file_text += "\tdace\\\n"
        elif str_sampling_type == 'moat':
            str_file_text += "\tpsuade_moat \\\n"

        for key in kwargs:
            if key == 'num_points':
                str_file_text += "\t\tsamples = {} \\\n".format(kwargs[key])
            elif key == 'values' or key == 'equal_area_divs':
                continue
            else:
                str_file_text += "\t\t{} {} \\\n".format(key, kwargs[key])

        str_file_text += "\n"
        str_file_text += "interface,\t\t\t\t\t\t\t\\\n"
        str_file_text += "\tasynchronous system\t\t\t\t\t\\\n"
        str_file_text += "\t  analysis_driver =       'interface.py'\t\t\\\n"
        str_file_text += "\t  parameters_file =       'info.in'\t\t\t\\\n"
        str_file_text += "\t  results_file =       'info.out'\t\t\t\\\n"
        str_file_text += "\t  aprepro\t\t\t\t\t\t\\\n"
        str_file_text += "\t  file_tag\t\t\t\t\t\t\\\n"
        str_file_text += "\t  file_save\t\t\t\t\t\t\\\n"
        str_file_text += "\n"
        str_file_text += "responses,\t\t\t\t\t\t\t\\\n"
        str_file_text += "\tnum_objective_functions = " + str(num_obj_fns) + "\t\t\t\t\\\n"
        str_file_text += "\tno_gradients\t\t\t\t\t\t\\\n"
        str_file_text += "\tno_hessians\n"

        str_file_text += "variables \\"
        str_file_text += "\n"
        str_file_text += "\t continuous_design = {} \\".format(len(variables))
        str_file_text += "\n"

        str_name = "\t cdv_descriptor \t"
        str_lower = "\t cdv_lower_bounds \t"
        str_init = "\t cdv_initial_point \t"
        str_upper = "\t cdv_upper_bounds \t"

        for i, var in enumerate(variables):
            f_lower = ls_box[i][0]
            f_init = ls_default[i]
            f_upper = ls_box[i][1]

            str_name += '\'' + var + '\'' + '\t'
            str_lower += "%24.16e\t" % f_lower
            str_init += "%24.16e\t" % f_init
            str_upper += "%24.16e\t" % f_upper
        # end for

        str_file_text += str_name + '\\\n'
        str_file_text += str_lower + '\\\n'
        str_file_text += str_init + '\\\n'
        str_file_text += str_upper + '\\\n'

        str_output_file_path = str_input_file_path + 'dakota.input'
        with open(str_output_file_path, 'w') as inputFile:
            inputFile.write(str_file_text)

        # Create the Sample Points
        cmd = '{s} -i {p}{dip}  -pre_run ::{p}{sout}'.format(p=str_input_file_path,
                                                             s=str_dakota_path, dip='dakota.input',
                                                             sout="DakotaSamplePoints.out")
        os.system(cmd)

        ls_points = []
        with open(str_input_file_path + "DakotaSamplePoints.out", 'r') as file_handle:
            b_first_pass = True
            for str_split_points in file_handle:
                if b_first_pass:
                    b_first_pass = False
                    continue

                ls_points.append(str_split_points.rsplit())
        return np.array(ls_points, dtype=float)


class UserValueSampler(ContinuousSampler, DiscreteSampler):
    """A sampler for creating sample sets from a tab file"""

    name = "User Value"

    @staticmethod
    def sample_points(user_samples_file, file_type='tab', **kwargs):
        """
        Create a set of points from a tab file

        Args:
            - user_samples_file (str): Relative path to tab file

        Returns (numpy array):
            - A two dimensional numpy array of sample points

        Raises:
            - TypeError
            - RuntimeError: If the given path is invalid
        """

        str_user_samples_file_path = str(user_samples_file)
        if not os.path.isfile(str_user_samples_file_path):
            raise RuntimeError("Cannot find {}".format(str_user_samples_file_path))
        ls_points = []
        if file_type.lower() == 'tab':
            with open(str_user_samples_file_path, "r") as file_handle:
                for str_split_points in file_handle:

                    if str_split_points[0] == '#' or str_split_points[0] == '\n':  # ignore comments and blank lines
                        continue
                    if str_split_points.find('#') > 0:
                        str_split_points = str_split_points[:str_split_points.find('#')]  # ignore text after comments

                    ls_points.append(str_split_points.rsplit())

        elif file_type.lower() == 'csv':
            with open(str_user_samples_file_path, 'r') as file_handle:
                file_handle.next()  # ignore header
                for str_split_points in file_handle:
                    ls_points.append(str_split_points.rsplit(','))
        else:
            raise TypeError('Only tab and csv file types supported')

        try:
            np_points = np.array(ls_points, dtype=float)
        except ValueError:
            np_points = np.array(ls_points, 'O')

        return np_points


if __name__ == "__main__":
    import time

    p = 5
    ls_num_div = [i + 2 for i in range(p)]
    car_box = [[-2, 4]] * p

    start2 = time.time()
    points2 = CartesianCrossSampler.sample_points(num_divisions=ls_num_div, box=car_box, equal_area_divs=False)
    end2 = time.time()

    print(points2[:10])
    print(end2 - start2)
