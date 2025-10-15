import asyncio
from ...serializer.osw.osw_normalizer import OSWWayNormalizer, OSWNodeNormalizer, OSWPointNormalizer, OSWLineNormalizer, OSWZoneNormalizer, OSWPolygonNormalizer
from ...serializer.osm.osm_graph import OSMGraph


async def count_entities(osm_file_path: str, counter_class):
    loop = asyncio.get_event_loop()
    counter = counter_class()
    await loop.run_in_executor(None, counter.apply_file, osm_file_path)
    return counter.count


async def get_osm_graph(osm_file_path):
    loop = asyncio.get_event_loop()
    OG = await loop.run_in_executor(
        None,
        OSMGraph.from_osm_file,
        osm_file_path,
        osw_way_filter,
        osw_node_filter,
        osw_point_filter,
        osw_line_filter,
        osw_zone_filter,
        osw_polygon_filter
    )

    return OG


def osw_way_filter(tags):
    normalizer = OSWWayNormalizer(tags)
    return normalizer.filter()


def osw_node_filter(tags):
    normalizer = OSWNodeNormalizer(tags)
    return normalizer.filter()


def osw_point_filter(tags):
    normalizer = OSWPointNormalizer(tags)
    return normalizer.filter()


def osw_line_filter(tags):
    normalizer = OSWLineNormalizer(tags)
    return normalizer.filter()


def osw_zone_filter(tags):
    normalizer = OSWZoneNormalizer(tags)
    return normalizer.filter()


def osw_polygon_filter(tags):
    normalizer = OSWPolygonNormalizer(tags)
    return normalizer.filter()


async def simplify_og(og):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, og.simplify)


async def construct_geometries(og):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, og.construct_geometries)
