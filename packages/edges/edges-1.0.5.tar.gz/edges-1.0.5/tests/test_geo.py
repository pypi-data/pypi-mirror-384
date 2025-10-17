from edges.utils import get_str
from edges.georesolver import GeoResolver
from constructive_geometries import Geomatcher


def test_geo():
    geo = Geomatcher()
    parents = [get_str(x) for x in geo.within("IT")]
    assert "RER" in parents
    assert "RER" in [get_str(x) for x in geo.within("IT")]


def test_within():
    from constructive_geometries import Geomatcher

    geo = Geomatcher()
    assert ("ecoinvent", "RER") in geo.within(
        "IT", include_self=True, exclusive=False, biggest_first=False
    )


def test_georesolver():
    geo = GeoResolver(
        weights={
            "RER": 1.0,
        }
    )
    assert "RER" in geo.resolve("IT", containing=False)
