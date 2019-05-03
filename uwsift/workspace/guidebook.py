#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
guidebook.py
~~~~~~~~~~~~

PURPOSE
This module is the "scientific expert knowledge" that is consulted.



:author: R.K.Garcia <rayg@ssec.wisc.edu>
:copyright: 2014 by University of Wisconsin Regents, see AUTHORS for more details
:license: GPLv3, see LICENSE for more details
"""
__author__ = 'rayg'
__docformat__ = 'reStructuredText'

import logging

from uwsift.common import Info, Kind, Platform, Instrument
from uwsift.view.colormap import DEFAULT_IR, DEFAULT_VIS, DEFAULT_UNKNOWN

LOG = logging.getLogger(__name__)
GUIDEBOOKS = {}


class Guidebook(object):
    """
    guidebook which knows about AHI, ABI, AMI bands, timing, file naming conventions
    """

    @staticmethod
    def is_relevant(pathname):
        return False

    @staticmethod
    def for_info(info=None, path=None):
        """
        given an info dictionary, figure out which
        :param info:
        :return:
        """
        if info and not path:
            path = info.get(Info.PATHNAME, None)

    def channel_siblings(self, uuid, infos):
        """
        determine the channel siblings of a given dataset
        :param uuid: uuid of the dataset we're interested in
        :param infos: datasetinfo_dict sequence, available datasets
        :return: (list,offset:int): list of [uuid,uuid,uuid] for siblings in order;
                 offset of where the input is found in list
        """
        return None, None

    def time_siblings(self, uuid, infos):
        """
        determine the time siblings of a given dataset
        :param uuid: uuid of the dataset we're interested in
        :param infos: datasetinfo_dict sequence, available datasets
        :return: (list,offset:int): list of [uuid,uuid,uuid] for siblings in order;
                 offset of where the input is found in list
        """
        return None, None


DEFAULT_COLORMAPS = {
    'toa_bidirectional_reflectance': DEFAULT_VIS,
    'toa_brightness_temperature': DEFAULT_IR,
    'brightness_temperature': DEFAULT_IR,
    'height_at_cloud_top': 'Cloud Top Height',
    'air_temperature': DEFAULT_IR,
    'relative_humidity': DEFAULT_IR,
    # 'thermodynamic_phase_of_cloud_water_particles_at_cloud_top': 'Cloud Phase',
}

_NW_GOESR_ABI = {
    Instrument.ABI: {  # http://www.goes-r.gov/education/ABI-bands-quick-info.html
        1: 0.47,
        2: 0.64,
        3: 0.86,
        4: 1.37,
        5: 1.6,
        6: 2.2,
        7: 3.9,
        8: 6.2,
        9: 6.9,
        10: 7.3,
        11: 8.4,
        12: 9.6,
        13: 10.3,
        14: 11.2,
        15: 12.3,
        16: 13.3,
    },
}

_NW_HIMAWARI_AHI = {
    Instrument.AHI: {
        1: 0.47,
        2: 0.51,
        3: 0.64,
        4: 0.86,
        5: 1.6,
        6: 2.3,
        7: 3.9,
        8: 6.2,
        9: 6.9,
        10: 7.3,
        11: 8.6,
        12: 9.6,
        13: 10.4,
        14: 11.2,
        15: 12.4,
        16: 13.3,
    },
}

# Instrument -> Band Number -> Nominal Wavelength
NOMINAL_WAVELENGTHS = {
    Platform.HIMAWARI_8: _NW_HIMAWARI_AHI,
    Platform.HIMAWARI_9: _NW_HIMAWARI_AHI,

    Platform.GOES_16: _NW_GOESR_ABI,
    Platform.GOES_17: _NW_GOESR_ABI,
}

# CF compliant Standard Names (should be provided by input files or the workspace)
# Instrument -> Band Number -> Standard Name

_SN_GOESR_ABI = {
    Instrument.ABI: {
        1: "toa_bidirectional_reflectance",
        2: "toa_bidirectional_reflectance",
        3: "toa_bidirectional_reflectance",
        4: "toa_bidirectional_reflectance",
        5: "toa_bidirectional_reflectance",
        6: "toa_bidirectional_reflectance",
        7: "toa_brightness_temperature",
        8: "toa_brightness_temperature",
        9: "toa_brightness_temperature",
        10: "toa_brightness_temperature",
        11: "toa_brightness_temperature",
        12: "toa_brightness_temperature",
        13: "toa_brightness_temperature",
        14: "toa_brightness_temperature",
        15: "toa_brightness_temperature",
        16: "toa_brightness_temperature",
    }
}

_SN_HIMAWARI_AHI = {
    Instrument.AHI: {
        1: "toa_bidirectional_reflectance",
        2: "toa_bidirectional_reflectance",
        3: "toa_bidirectional_reflectance",
        4: "toa_bidirectional_reflectance",
        5: "toa_bidirectional_reflectance",
        6: "toa_bidirectional_reflectance",
        7: "toa_brightness_temperature",
        8: "toa_brightness_temperature",
        9: "toa_brightness_temperature",
        10: "toa_brightness_temperature",
        11: "toa_brightness_temperature",
        12: "toa_brightness_temperature",
        13: "toa_brightness_temperature",
        14: "toa_brightness_temperature",
        15: "toa_brightness_temperature",
        16: "toa_brightness_temperature",
    },
}

STANDARD_NAMES = {
    Platform.HIMAWARI_8: _SN_HIMAWARI_AHI,
    Platform.HIMAWARI_9: _SN_HIMAWARI_AHI,
    Platform.GOES_16: _SN_GOESR_ABI,
    Platform.GOES_17: _SN_GOESR_ABI,
}


class ABI_AHI_Guidebook(Guidebook):
    "e.g. HS_H08_20150714_0030_B10_FLDK_R20.merc.tif"
    _cache = None  # {uuid:metadata-dictionary, ...}

    REFL_BANDS = [1, 2, 3, 4, 5, 6]
    BT_BANDS = [7, 8, 9, 10, 11, 12, 13, 14, 15, 16]

    def __init__(self):
        self._cache = {}

    def _relevant_info(self, seq):
        "filter datasetinfo dictionaries in sequence, if they're not relevant to us (i.e. not AHI)"
        for dsi in seq:
            if self.is_relevant(dsi.get(Info.PATHNAME, None)):
                yield dsi

    def collect_info(self, info):
        """Collect information that may not come from the dataset.

        This method should only be called once to "fill in" metadata
        that isn't originally known about an opened file.
        """
        z = {}

        if info[Info.KIND] in (Kind.IMAGE, Kind.COMPOSITE):
            if z.get(Info.CENTRAL_WAVELENGTH) is None:
                try:
                    wl = NOMINAL_WAVELENGTHS[info[Info.PLATFORM]][info[Info.INSTRUMENT]][info[Info.BAND]]
                except KeyError:
                    wl = None
                z[Info.CENTRAL_WAVELENGTH] = wl

        if Info.BAND in info:
            band_short_name = "B{:02d}".format(info[Info.BAND])
        else:
            band_short_name = info.get(Info.DATASET_NAME, '???')
        if Info.SHORT_NAME not in info:
            z[Info.SHORT_NAME] = band_short_name
        else:
            z[Info.SHORT_NAME] = info[Info.SHORT_NAME]
        if Info.LONG_NAME not in info:
            z[Info.LONG_NAME] = info.get(Info.SHORT_NAME, z[Info.SHORT_NAME])

        if Info.STANDARD_NAME not in info:
            try:
                z[Info.STANDARD_NAME] = STANDARD_NAMES[info[Info.PLATFORM]][info[Info.INSTRUMENT]][info[Info.BAND]]
            except KeyError:
                z[Info.STANDARD_NAME] = "." + str(z.get(Info.SHORT_NAME))

        # Only needed for backwards compatibility with originally supported geotiffs
        if not info.get(Info.UNITS):
            standard_name = info.get(Info.STANDARD_NAME, z.get(Info.STANDARD_NAME))
            if standard_name == 'toa_bidirectional_reflectance':
                z[Info.UNITS] = '1'
            elif standard_name == 'toa_brightness_temperature':
                z[Info.UNITS] = 'kelvin'
        if info.get(Info.UNITS, z.get(Info.UNITS)) in ['K', 'Kelvin']:
            z[Info.UNITS] = 'kelvin'

        return z

    def _is_refl(self, dsi):
        # work around for old `if band in BAND_TYPE`
        return dsi.get(Info.BAND) in self.REFL_BANDS or dsi.get(Info.STANDARD_NAME) == "toa_bidirectional_reflectance"

    def _is_bt(self, dsi):
        return dsi.get(Info.BAND) in self.BT_BANDS or \
            dsi.get(Info.STANDARD_NAME) in ["toa_brightness_temperature", 'brightness_temperature', 'air_temperature']

    def collect_info_from_seq(self, seq):
        "collect AHI metadata about a sequence of datasetinfo dictionaries"
        # FUTURE: cache uuid:metadata info in the guidebook instance for quick lookup
        for each in self._relevant_info(seq):
            md = self.collect_info(each)
            yield each[Info.UUID], md

    def climits(self, dsi):
        # Valid min and max for colormap use for data values in file (unconverted)
        if self._is_refl(dsi):
            lims = (-0.012, 1.192)
            if dsi[Info.UNITS] == '%':
                # Reflectance/visible data limits
                lims = (lims[0] * 100., lims[1] * 100.)
            return lims
        elif self._is_bt(dsi):
            # BT data limits
            return -109.0 + 273.15, 55 + 273.15
        elif "valid_min" in dsi and "valid_max" in dsi:
            return dsi["valid_min"], dsi["valid_max"]
        elif "flag_values" in dsi:
            return min(dsi["flag_values"]), max(dsi["flag_values"])
        elif "valid_range" in dsi:
            return dsi['valid_range']
        elif Info.VALID_RANGE in dsi:
            return dsi[Info.VALID_RANGE]
        else:
            # some kind of default
            return 0., 255.

    def valid_range(self, dsi):
        if 'valid_min' in dsi:
            valid_range = (dsi['valid_min'], dsi['valid_max'])
        elif 'valid_range' in dsi:
            valid_range = dsi['valid_range']
        else:
            valid_range = dsi[Info.CLIM]
        return dsi.setdefault(Info.VALID_RANGE, valid_range)

    def default_colormap(self, dsi):
        return DEFAULT_COLORMAPS.get(dsi.get(Info.STANDARD_NAME), DEFAULT_UNKNOWN)

    def _default_display_time(self, ds_info):
        # FUTURE: This can be customized by the user
        when = ds_info.get(Info.SCHED_TIME, ds_info.get(Info.OBS_TIME))
        if when is None:
            dtime = '--:--:--'
        elif 'model_time' in ds_info:
            dtime = "{}Z +{}h".format(
                ds_info['model_time'].strftime('%Y-%m-%d %H:%M'),
                when.strftime('%H')
            )
        else:
            dtime = when.strftime('%Y-%m-%d %H:%M:%S')
        return dtime

    def _default_display_name(self, ds_info, display_time=None):
        # FUTURE: This can be customized by the user
        sat = ds_info[Info.PLATFORM]
        inst = ds_info[Info.INSTRUMENT]
        name = ds_info.get(Info.SHORT_NAME, '-unknown-')

        label = ds_info.get(Info.STANDARD_NAME, '')
        if label == 'toa_bidirectional_reflectance':
            label = 'Refl'
        elif label == 'toa_brightness_temperature':
            label = 'BT'
        else:
            label = ''

        if display_time is None:
            display_time = ds_info.get(Info.DISPLAY_TIME, self._default_display_time(ds_info))
        name = "{sat} {inst} {name} {standard_name} {dtime}".format(
            sat=sat.value, inst=inst.value, name=name, standard_name=label, dtime=display_time)
        return name

# if __name__ == '__main__':
#     sys.exit(main())
