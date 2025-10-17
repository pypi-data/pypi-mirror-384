import os

import numpy as np
import tifffile as tf


class dark_calibration:
    '''A class holder for pixelwise average and variance.

    Intended to be used for photon-free calibration:
    https://www.biorxiv.org/lookup/doi/10.1101/2021.04.16.440125
    http://dx.doi.org/10.1038/s41467-022-30907-2

    ACCENT (ImageJ/Fiji Plugin):
    https://github.com/ries-lab/Accent
    '''
    def __init__(self, shape, exposure):
        self._counter = 0
        self._exposure = exposure
        self._shape = shape
        self._accumulator = np.zeros(
            shape=shape, dtype=np.float64)
        self._quad_accum = np.zeros(
            shape=shape, dtype=np.float64)

    def addFrame(self, image: np.ndarray):
        '''Adds an image frame to the mean/variance estimators.

        Parameters
        ----------
        image : np.ndarray
            image of dark_calibration shape to be added.

        Raises
        ------
        ValueError
            image of wrong shape.
        '''
        if image.shape != self._shape:
            raise ValueError('Image of wrong shape.')

        self._accumulator += image
        self._quad_accum += np.square(image)
        self._counter += 1

    def getResults(self):
        '''Gets the resulting mean and variance frames.

        Returns
        -------
        tuple(ndarray, ndarray)
            the rasults (mean, variance)

        Raises
        ------
        ValueError
            in case zero frames are added.
        '''
        if self._counter < 1:
            raise ValueError('Counter should be non-zero.')

        mean = self._accumulator / self._counter
        variance = (
            self._quad_accum -
            np.square(self._accumulator)/self._counter)/(self._counter - 1)

        return mean, variance

    def saveResults(self, path, prefix):
        if not os.path.exists(path):
            os.makedirs(path)

        def getFilename(index: int):
            return path + \
                    f'\\image_{index:05d}.ome.tif'

        mean, variance = self.getResults()

        with tf.TiffWriter(
                path + prefix + \
                    f'_image_mean_{self._exposure:.5f}_ms'.replace('.', '_') + \
                    '.ome.tif',
                append=False,
                bigtiff=False,
                ome=False) as writer:
            writer.write(
                data=mean,
                photometric='minisblack')

        with tf.TiffWriter(
                path + prefix + \
                    f'_image_var_{self._exposure:.5f}_ms'.replace('.', '_') + \
                    '.ome.tif',
                append=False,
                bigtiff=False,
                ome=False) as writer:
            writer.write(
                data=variance,
                photometric='minisblack')
