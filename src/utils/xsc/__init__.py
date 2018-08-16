import json
from datetime import timedelta
from typing import List, Optional, Any, Dict, Tuple

from utils.cache import JsonCache
from utils.log import err_log
from utils.api import CrossSectionApi


class CrossSectionMeta:
    """
    This class represents meta data about all of a molecules available
    cross-sections. It can cache to disk in the '{data}/.cache/xsc/' folder to prevent
    unneeded web requests, since they're slow. If the data is not present on
    the disk, it will be downloaded automatically.

    The cached cross section metas have the 'xscm' file extension and contain plain json
    in the following format:

    {
        // This is an unix time-stamp that is used to put an
        // expiration date on the cached data, so it will rarely
        // be out-dated.
        'timestamp': 143145,
        // This is an array of 'metas.' Each meta corresponds to
        // an actual cross-section file that is available to download on hitran.org
        'metas':    [   {
                        "__identity__": "id",
                        "numax": 811.995,
                        "pressure": 757.7,
                        "id": 139,
                        "molecule_id": 104,
                        "numin": 750.0028,
                        "valid_from": "2000-05-04",
                        "temperature": 296.7,
                        "sigma_max": 4.867e-18,
                        "npnts": 6173,
                        "__class__": "CrossSection",
                        "valid_to": "2012-12-31",
                        "filename": "CCl4_296.7K-757.7Torr_750.0-812.0_00.xsc",
                        "resolution_units": "cm-1",
                        "source_id": 631,
                        "resolution": 0.03,
                        "broadener": "air"
                        },
                        ...
                    ]
    }

    """

    molecule_metas = {}

    def __init__(self, molecule_id):
        """
        :param molecule_id: HITRAN MoleculeId of the molecule to retrieve xsc meta data for
        """
        self.molecule_id = molecule_id

        self.metas = []

        self.api = CrossSectionApi()

        self.cache = JsonCache(".xscm", self.api.request_xsc_meta, timedelta(days = 1.0))

        if not self.cache.ok():
            err_log("Failed to load xscm from cache.")
        else:
            parsed = self.cache.data()
            self.add_meta_objects(parsed)
            if self.molecule_id in CrossSectionMeta.molecule_metas:
                self.metas = CrossSectionMeta.molecule_metas[self.molecule_id]

    def molecule_id_matches(self, d: Dict[str, Any]):
        return 'molecule_id' in d and d['molecule_id'] == self.molecule_id

    def get_all_filenames(self) -> List[str]:
        return list(map(lambda x: x['filename'], self.metas))

    def add_meta_objects(self, meta_objs: List[Dict]):
        def insert(meta_obj):
            ind = meta_obj['molecule_id']
            if ind in CrossSectionMeta.molecule_metas:
                CrossSectionMeta.molecule_metas[ind].append(meta_obj)
            else:
                CrossSectionMeta.molecule_metas[ind] = [meta_obj]

        list(map(insert, meta_objs))


class CrossSectionFilter:

    def __init__(self, molecule_id: int, wn_range: Tuple[float, float] = None, pressure_range: Tuple[float, float] = None,
                 temp_range: Tuple[float, float] = None):
        self.molecule_id = molecule_id
        self.wn_range = wn_range
        self.temp_range = temp_range
        self.pressure_range = pressure_range

    def get_cross_sections(self) -> List[str]:
        if self.molecule_id not in CrossSectionMeta.molecule_metas:
            return []
        return list(item['filename'] for item in CrossSectionMeta.molecule_metas[self.molecule_id] if self.passes(item))

    def passes(self, meta) -> bool:
        return (self.pressure_range is None or (self.pressure_range[0] < meta['pressure'] < self.pressure_range[1])) \
                and (self.temp_range is None or (self.temp_range[0] < meta['temperature'] < self.temp_range[1])) \
                and (self.wn_range is None or (meta['numin'] < self.wn_range[0] and meta['numax'] > self.wn_range[1]))