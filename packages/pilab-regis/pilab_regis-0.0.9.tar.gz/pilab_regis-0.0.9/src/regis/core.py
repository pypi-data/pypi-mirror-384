# -*- coding: utf-8 -*-
"""
Created on Wed Mar  1 16:37:35 2023

@author: pilab
"""

import numpy as np
import nibabel as nib
from dipy.viz import regtools
from dipy.io.image import load_nifti
from dipy.align.metrics import CCMetric
from dipy.align.imaffine import (transform_centers_of_mass,
                                 AffineMap,
                                 MutualInformationMetric,
                                 AffineRegistration)
from dipy.align.transforms import (TranslationTransform3D,
                                   RigidTransform3D,
                                   AffineTransform3D)
from dipy.align.imwarp import SymmetricDiffeomorphicRegistration


def find_transform(moving_file: str, static_file: str,
                   only_affine: bool = False, level_iters=[10000, 1000, 100],
                   diffeomorph: bool = True, level_iters_diff=[10000, 1000, 100],
                   sanity_check: bool = False, normalize: bool = False,
                   static_mask=None, moving_mask=None,
                   hard_static_mask=None):
    '''
    If volume are 4D+, only the first 3D volume is taken into account.

    Parameters
    ----------
    moving_file : str
        3D array of moving volume.
    static_file : str
        3D array of static volume.
    only_affine : bool, optional
        Registers using only the affine information of both files.
        The default is False.
    level_iters : list, optional
        Number of iterations to perform per 'scale' of the image, greater scales
        first. The size of possible deformations increases with the scale. The
        default is [10000, 1000, 100].
    diffeomorph : bool, optional
        If False then registration is only affine. The default is True.
    level_iters_diff : list, optional
        Number of iterations to perform per 'scale' of the image for the
        diffeomorphic step, greater scales first. The size of possible
        deformations increases with the scale. The default is [10000, 1000, 100].
    sanity_check : bool, optional
        If True then prints figures. The default is False.
    normalize : bool, optional
        If True, both volume are normalized before registration. This parameter
        improves robustness of registration. The default is False.
    static_mask : array, optional
        Static image mask that defines which pixels in the static image
        are used to calculate the mutual information.
    moving_mask : array, optional
        Moving image mask that defines which pixels in the moving image
        are used to calculate the mutual information.
    hard_static_mask : array, optional
        Static image mask that defines which pixels in the static image
        are not set to 0 (black).

    Returns
    -------
    mapping : TYPE
        transform operation to send moving_volume to static_volume space.

    '''

    static, static_affine = load_nifti(static_file)
    static_grid2world = static_affine
    if len(static.shape) > 3:
        static = static[:, :, :, 0]

    moving, moving_affine = load_nifti(moving_file)
    moving_grid2world = moving_affine
    if len(moving.shape) > 3:
        moving = moving[:, :, :, 0]

    if normalize:
        static = static/np.max(static)
        moving = moving/np.max(moving)

    if type(hard_static_mask) is np.ndarray:
        static *= hard_static_mask

    # Affine registration ------------------------------------------------------

    if sanity_check or only_affine:

        identity = np.eye(4)
        affine_map = AffineMap(identity,
                               static.shape, static_grid2world,
                               moving.shape, moving_grid2world)

        if sanity_check:
            resampled = affine_map.transform(moving)

            regtools.overlay_slices(static, resampled, None, 0,
                                    "Static", "Moving", "resampled_0.png")
            regtools.overlay_slices(static, resampled, None, 1,
                                    "Static", "Moving", "resampled_1.png")
            regtools.overlay_slices(static, resampled, None, 2,
                                    "Static", "Moving", "resampled_2.png")

        if only_affine:

            return affine_map

    c_of_mass = transform_centers_of_mass(static, static_grid2world,
                                          moving, moving_grid2world)

    nbins = 32
    sampling_prop = None
    metric = MutualInformationMetric(nbins, sampling_prop)

    sigmas = [3.0, 1.0, 0.0]
    factors = [4, 2, 1]
    affreg = AffineRegistration(metric=metric,
                                level_iters=level_iters,
                                sigmas=sigmas,
                                factors=factors)

    transform = TranslationTransform3D()
    params0 = None
    translation = affreg.optimize(static, moving, transform, params0,
                                  static_grid2world, moving_grid2world,
                                  starting_affine=c_of_mass.affine,
                                  static_mask=static_mask,
                                  moving_mask=moving_mask)

    transform = RigidTransform3D()
    rigid = affreg.optimize(static, moving, transform, params0,
                            static_grid2world, moving_grid2world,
                            starting_affine=translation.affine,
                            static_mask=static_mask,
                            moving_mask=moving_mask)

    transform = AffineTransform3D()
    affine = affreg.optimize(static, moving, transform, params0,
                             static_grid2world, moving_grid2world,
                             starting_affine=rigid.affine,
                             static_mask=static_mask,
                             moving_mask=moving_mask)

    # Diffeomorphic registration -----------------------------------------------

    if diffeomorph:

        metric = CCMetric(3)

        sdr = SymmetricDiffeomorphicRegistration(metric, level_iters_diff)

        mapping = sdr.optimize(static, moving, static_affine, moving_affine,
                               affine.affine)

    else:

        mapping = affine

    if sanity_check:

        transformed = mapping.transform(moving)

        regtools.overlay_slices(static, transformed, None, 0,
                                "Static", "Transformed", "transformed.png")
        regtools.overlay_slices(static, transformed, None, 1,
                                "Static", "Transformed", "transformed.png")
        regtools.overlay_slices(static, transformed, None, 2,
                                "Static", "Transformed", "transformed.png")

    return mapping


def apply_transform(moving_file: str, mapping, static_file: str = '',
                    output_path: str = '', binary: bool = False,
                    binary_thresh: float = 0.5, labels: bool = False,
                    inverse: bool = False, mask_file: str = ''):
    '''
    Applies the transformation obtained from find_transform() in 'mapping' to a
    moving file.

    Parameters
    ----------
    moving_file : str
        Moving file path.
    mapping : TYPE
        Deformation from moving to static.
    static_file : str, optional
        Only necessary if output_path is specified. The default is ''.
    output_path : str, optional
        If entered, saves result at specified location. The default is ''.
    binary : bool, optional
        If True, outputs a binary mask. The default is False.
    binary_thresh : float, optional
        If 'binary'==True, all values above this threshold are set to 1.
        The default is 0.5.
    labels : bool, optional
        Set as True if the moving file is a labelled parcelation.
        The default is False.
    inverse : bool, optional
        If True, the inverse transformation is applied. The default is False.
    mask_file : str, optional
        If specified, applies a binary mask to moving file before mapping.

    Returns
    -------
    transformed : 3-D array of shape (x,y,z)
        Transformed array.

    '''

    moving = nib.load(moving_file)
    moving_data = moving.get_fdata()

    if len(moving_data.shape) > 3:
        moving_data = moving_data[:, :, :, 0]

    if len(mask_file) > 0:
        mask = nib.load(mask_file).get_fdata()
        moving_data *= mask

    if labels:
        interpolation = 'nearest'
    else:
        interpolation = 'linear'

    if inverse:
        transformed = mapping.transform_inverse(moving_data,
                                                interpolation=interpolation)
    else:
        transformed = mapping.transform(moving_data,
                                        interpolation=interpolation)

    if binary:
        transformed = np.where(transformed > binary_thresh, 1, 0)

    if labels:
        transformed = transformed.astype(int)

    if len(output_path) > 0:

        transformed = transformed.astype('float32')

        static = nib.load(static_file)

        out = nib.Nifti1Image(transformed, static.affine, header=static.header)
        out.to_filename(output_path)

    else:

        return transformed
