from pydggsapi.schemas.ogc_dggs.dggrs_descrption import DggrsDescription
from pydggsapi.schemas.ogc_dggs.common_ogc_dggs_api import Link
from pydggsapi.dependencies.api.collections import get_collections_info

from typing import Dict
from tinydb import TinyDB
import logging
import os

logger = logging.getLogger()


def get_conformance_classes():
    return ["https://www.opengis.net/spec/ogcapi-common-1/1.0/conf/landing-page",
            "https://www.opengis.net/spec/ogcapi-dggs-1/1.0/conf/core",
            "https://www.opengis.net/spec/ogcapi-dggs-1/1.0/conf/zone-query",
            "https://www.opengis.net/spec/ogcapi-dggs-1/1.0/conf/data-retrieval",
            "https://www.opengis.net/spec/ogcapi-dggs-1/1.0/conf/collection-dggs"]


def _checkIfTableExists():
    db = TinyDB(os.environ.get('dggs_api_config'))
    if ('dggrs' not in db.tables()):
        logger.error(f"{__name__} dggrs table not found.")
        raise Exception(f"{__name__} dggrs table not found.")
    return db


def get_dggrs_class(dggrsId: str) -> str:
    try:
        db = _checkIfTableExists()
    except Exception as e:
        logger.error(f"{__name__} {e}")
        raise Exception(f"{__name__} {e}")
    dggrs_indexes = db.table('dggrs')
    for dggrs in dggrs_indexes:
        id_, dggrs_config = dggrs.popitem()
        if (id_ == dggrsId):
            return dggrs_config['classname']
    return None


def get_dggrs_descriptions() -> Dict[str, DggrsDescription]:
    try:
        db = _checkIfTableExists()
        collections = get_collections_info()
    except Exception as e:
        logger.error(f"{__name__} {e}")
        raise Exception(f"{__name__} {e}")
    if (len(collections.keys()) == 0):
        logger.error(f"{__name__} no collections found")
        raise Exception(f"{__name__} no collections found")
    dggrs_indexes = db.table('dggrs').all()
    if (len(dggrs_indexes) == 0):
        logger.error(f"{__name__} no dggrs defined.")
        raise Exception(f"{__name__} no dggrs defined.")
    dggrs_dict = {}
    collection_providers = [v.collection_provider for k, v in collections.items()]
    max_dggrs = {}
    for cp in collection_providers:
        try:
            current_max = max_dggrs[cp.dggrsId]
            max_dggrs[cp.dggrsId] = cp.max_refinement_level if (current_max < cp.max_refinement_level) else current_max
        except KeyError:
            max_dggrs[cp.dggrsId] = cp.max_refinement_level
    for dggrs in dggrs_indexes:
        dggrsid, dggrs_config = dggrs.popitem()
        self_link = Link(**{'href': '', 'rel': 'self', 'title': 'DGGRS description link'})
        dggrs_model_link = Link(**{
            'href': dggrs_config['definition_link'],
            'rel': '[ogc-rel:dggrs-definition]',
            'title': 'DGGRS definition',
        })
        dggrs_config['id'] = dggrsid
        dggrs_config['maxRefinementLevel'] = max_dggrs.get(dggrsid, 32)
        dggrs_config['links'] = [self_link, dggrs_model_link]
        del dggrs_config['definition_link']
        dggrs_dict[dggrsid] = DggrsDescription(**dggrs_config)
    return dggrs_dict
