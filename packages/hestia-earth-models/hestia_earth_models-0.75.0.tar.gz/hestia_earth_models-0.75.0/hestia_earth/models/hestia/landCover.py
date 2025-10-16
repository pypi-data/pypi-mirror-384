import os
from hestia_earth.schema import SiteSiteType, TermTermType
from hestia_earth.utils.model import filter_list_term_type
from hestia_earth.utils.tools import to_precision, omit, pick, non_empty_list, flatten
from hestia_earth.utils.blank_node import group_by_keys

from hestia_earth.models.log import logRequirements, log_as_table, logShouldRun
from hestia_earth.models.utils.management import _new_management
from hestia_earth.models.utils.blank_node import _gapfill_datestr, DatestrGapfillMode, condense_nodes
from .utils import (
    LAND_USE_TERMS_FOR_TRANSFORMATION,
    IPCC_LAND_USE_CATEGORY_PERENNIAL,
    ANNUAL_CROPLAND,
    PERMANENT_CROPLAND,
    OTHER_LAND,
    PERMANENT_PASTURE,
    TOTAL_CROPLAND,
    crop_ipcc_land_use_category
)
from .landCover_utils import (
    _get_lookup_with_cache,
    get_site_area_from_lookups,
    compute_site_area
)
from . import MODEL

REQUIREMENTS = {
    "Site": {
        "siteType": [
            "forest",
            "cropland",
            "permanent pasture",
            "other natural vegetation"
        ],
        "country": {"@type": "Term", "termType": "region"},
        "management": [
            {
                "@type": "Management",
                "value": "",
                "term.termType": "landCover",
                "or": {
                    "startDate": "",
                    "endDate": ""
                }
            }
        ]
    }
}
RETURNS = {
    "Management": [{
        "term.termType": "landCover",
        "value": "",
        "endDate": "",
        "startDate": ""
    }]
}
LOOKUPS = {
    "region-crop-cropGroupingFAOSTAT-landCover-annualCropland": "",
    "region-crop-cropGroupingFAOSTAT-landCover-forest": "",
    "region-crop-cropGroupingFAOSTAT-landCover-otherLand": "",
    "region-crop-cropGroupingFAOSTAT-landCover-permanentCropland": "",
    "region-crop-cropGroupingFAOSTAT-landCover-permanentPasture": "",
    "region-crop-cropGroupingFaostatProduction-areaHarvestedUpTo20YearExpansion": "",
    "region-crop-cropGroupingFaostatProduction-areaHarvested": "",
    "region-faostatArea-UpTo20YearExpansion": "",
    "region-faostatArea": [
        "Arable land",
        "Cropland",
        "Forest land",
        "Land area",
        "Other land",
        "Permanent crops",
        "Permanent meadows and pastures"
    ],
    "crop": ["cropGroupingFaostatArea", "IPCC_LAND_USE_CATEGORY"],
    "landCover": ["cropGroupingFaostatProduction", "FAOSTAT_LAND_AREA_CATEGORY"],
    "property": "CALCULATE_TOTAL_LAND_COVER_SHARE_SEPARATELY"
}
MODEL_KEY = 'landCover'

_FALLBACK_COMPUTE_DATA = os.getenv('MODEL_LAND_COVER_FALLBACK_COMPUTE_DATA', 'true') == 'true'
_BUILDING_SITE_TYPES = [
    SiteSiteType.AGRI_FOOD_PROCESSOR.value,
    SiteSiteType.ANIMAL_HOUSING.value,
    SiteSiteType.FOOD_RETAILER.value
]
_ALLOWED_SITE_TYPES = [
    SiteSiteType.CROPLAND.value,
    SiteSiteType.FOREST.value,
    SiteSiteType.OTHER_NATURAL_VEGETATION.value,
    SiteSiteType.PERMANENT_PASTURE.value
]
_DEFAULT_WINDOW_IN_YEARS = 20
_ALLOWED_LAND_USE_TYPES = [ANNUAL_CROPLAND, PERMANENT_CROPLAND, PERMANENT_PASTURE, TOTAL_CROPLAND]
_COMPLETE_CHANGES_OTHER_LAND = {k: 0 for k in LAND_USE_TERMS_FOR_TRANSFORMATION.keys()} | {OTHER_LAND: 1}


def _run(values: list):
    blank_nodes = [
        _new_management(
            term=value.get("term-id"),
            value=value.get("percentage"),
            model=MODEL,
            start_date=f"{value['year'] - _DEFAULT_WINDOW_IN_YEARS}-01-01",
            end_date=f"{value['year'] - _DEFAULT_WINDOW_IN_YEARS}-12-31",
        ) for value in values
    ]
    return condense_nodes(blank_nodes)


def _should_group_landCover(management_node: dict):
    return any(
        bool(_get_lookup_with_cache(
            lookup_term=prop.get("term", {}),
            column="CALCULATE_TOTAL_LAND_COVER_SHARE_SEPARATELY"
        ))
        for prop in management_node.get("properties", [])
    )


def _get_land_use_term_from_node(node: dict):
    return _get_lookup_with_cache(lookup_term=node.get("term", {}), column='FAOSTAT_LAND_AREA_CATEGORY')


def _date_strip(date: str): return date[:10] if date else None


def _date_year(date: str): return int(date[:4]) if date else None


def _collect_land_use_types(nodes: list) -> list:
    """Look up the land use type from management nodes."""
    return [
        {
            "term": node.get("term", {}),
            "landCover-id": node.get("term", {}).get("@id"),
            "landUseType": _get_land_use_term_from_node(node),
            "endDate": _date_strip(_gapfill_datestr(datestr=node.get("endDate"), mode=DatestrGapfillMode.END)),
            "startDate": _date_strip(_gapfill_datestr(datestr=node.get("startDate"), mode=DatestrGapfillMode.START))
        } for node in nodes
    ]


def _site_area_valid(site_area: dict): return site_area and all([v is not None for v in site_area.values()])


def _extend_site_area(site: dict, existing_years: set, land_use_node: dict) -> list:
    reference_year = land_use_node['year']
    target_year = land_use_node['year'] - _DEFAULT_WINDOW_IN_YEARS

    has_no_prior_land_cover_data = target_year not in existing_years

    site_area_from_lookups = get_site_area_from_lookups(
        country_id=site.get("country", {}).get("@id"),
        reference_year=reference_year,
        term=land_use_node['term']
    )
    has_siteArea_from_lookups = _site_area_valid(site_area_from_lookups)

    site_area_computed, is_valid, extra_logs = compute_site_area(
        site=site,
        term=land_use_node['term'],
        land_use_type=land_use_node['landUseType'],
        reference_year=reference_year
    ) if not has_siteArea_from_lookups and _FALLBACK_COMPUTE_DATA else ({}, False, {})

    is_perenial = crop_ipcc_land_use_category(land_use_node['landCover-id']) == IPCC_LAND_USE_CATEGORY_PERENNIAL

    return land_use_node | {
        'hasNoPriorLandCoverData': has_no_prior_land_cover_data,
        'isPerenial': is_perenial,
        'isValid': has_siteArea_from_lookups or is_valid,
        'siteArea': site_area_from_lookups if has_siteArea_from_lookups else site_area_computed,
        'site-area-from-lookup': site_area_from_lookups
    } | extra_logs


def _years_from_node(node: dict):
    start_year = _date_year(node['startDate']) if node.get('startDate') else None
    end_year = _date_year(node['endDate']) if node.get('endDate') else None
    return list(range(start_year, end_year + 1)) if start_year and end_year else non_empty_list([start_year, end_year])


def _log_land_use_nodes(site: dict, land_use_nodes: list):
    # group by term to show together in the logs
    grouped_values = group_by_keys(land_use_nodes, ['term-id'])

    for term_id, values in grouped_values.items():
        # collect logs for every year
        logRequirements(site, model=MODEL, term=term_id, model_key=MODEL_KEY,
                        values=log_as_table([
                            omit(v, ['term', 'term-id', 'land-type', 'missing-changes']) | {
                                key: v.get(key, {}).get(v['land-type'])
                                for key in [
                                    'changes',
                                    'site-area',
                                    'site-area-from-lookup',
                                    'annualCropland',
                                    'permanentCropland',
                                ] if key in v
                            }
                            for v in values
                        ]))

        logShouldRun(site, MODEL, term_id, values[0]['isValid'], model_key=MODEL_KEY)


def _should_run(site: dict) -> tuple[bool, list, dict]:
    is_site_building = site.get('siteType') in _BUILDING_SITE_TYPES

    allowed_land_use_types = _ALLOWED_LAND_USE_TYPES + ([OTHER_LAND] if is_site_building else [])

    # get all Management `landCover` nodes from the site
    management_nodes = _collect_land_use_types([
        node for node in filter_list_term_type(site.get("management", []), TermTermType.LANDCOVER)
        if not _should_group_landCover(node)
    ])

    # get all existing dates that we should not add again
    existing_years = set(non_empty_list(flatten(map(_years_from_node, management_nodes))))

    # get the Management `landCover` nodes that are "landUse" nodes
    land_use_nodes = [
        node for node in management_nodes
        if node["landUseType"] in allowed_land_use_types
    ]

    # get the nodes over all years of management
    land_use_nodes = {
        year: omit(node, ['startDate', 'endDate']) | {'year': year}
        for node in land_use_nodes
        for year in _years_from_node(node)
    }.values()

    # add metadata
    land_use_nodes = sorted([
        node if is_site_building else _extend_site_area(site, existing_years, node)
        for node in land_use_nodes
    ], key=lambda n: n['year'])

    # for buildings, add the landCover of the building 20years prior
    land_use_nodes = [
        land_use_nodes[0] | {
            'hasNoPriorLandCoverData': True,
            'isValid': True,
            'siteArea': _COMPLETE_CHANGES_OTHER_LAND,
            'site-area-from-lookup': {}
        }
    ] if land_use_nodes and is_site_building else land_use_nodes

    # create list of land use nodes with all data
    land_use_nodes = sorted([
        omit(node, ['siteArea']) | {
            "land-type": land_type,
            "percentage": 0 if ratio == -0.0 else to_precision(ratio * 100),
            "term-id": (
                node['landCover-id'] if node.get('isPerenial') and land_type == PERMANENT_CROPLAND else
                LAND_USE_TERMS_FOR_TRANSFORMATION[land_type][0]
            )
        }
        for node in land_use_nodes
        for land_type, ratio in node.get('siteArea').items()
    ], key=lambda n: '-'.join([str(n['year']), n['term-id']]))

    land_use_nodes and _log_land_use_nodes(site, land_use_nodes)

    # filter valid values
    valid_land_use_nodes = [
        node for node in land_use_nodes if all([
            node.get('hasNoPriorLandCoverData'),
            node.get('isValid'),
        ])
    ]

    site_type_allowed = site.get("siteType") in (_ALLOWED_SITE_TYPES + _BUILDING_SITE_TYPES)

    # group by term to show global logs for each Management node in the Site
    grouped_values = group_by_keys(land_use_nodes, ['term'])

    for term_id, values in grouped_values.items():
        is_valid = any([v.get('isValid') for v in values])

        logRequirements(site, model=MODEL, term=term_id, model_key=MODEL_KEY,
                        country_id=site.get("country", {}).get("@id"),
                        site_type_allowed=site_type_allowed,
                        allowed_land_use_types=';'.join(allowed_land_use_types),
                        land_use_type=values[0]['landUseType'],
                        values=log_as_table([
                            pick(v, ['year', 'term-id', 'isValid', 'percentage']) | {
                                key: v.get(key, {}).get(v['land-type'])
                                for key in [
                                    'changes',
                                    'site-area',
                                    'site-area-from-lookup',
                                    'annualCropland',
                                    'permanentCropland',
                                ] if key in v
                            } | {
                                'missing-changes': '-'.join(v.get('missing-changes', []))
                            }
                            for v in values
                        ]))
        logShouldRun(site, MODEL, term_id, is_valid, model_key=MODEL_KEY)

    should_run = all([site_type_allowed, valid_land_use_nodes])
    return should_run, valid_land_use_nodes


def run(site: dict) -> list:
    should_run, values = _should_run(site=site)
    return _run(values) if should_run else []
