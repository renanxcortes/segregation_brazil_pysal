import shutil
import subprocess

import networkx as nx
import pytest
from shapely.geometry import box

from netseg import osm_extract

# Five nodes along a line near Porto Alegre (~96 m apart) plus two ways that must be filtered out.
OSM_XML = """<?xml version='1.0' encoding='UTF-8'?>
<osm version="0.6" generator="test">
  <node id="1" version="1" lat="-30.0300" lon="-51.2300"/>
  <node id="2" version="1" lat="-30.0300" lon="-51.2290"/>
  <node id="3" version="1" lat="-30.0300" lon="-51.2280"/>
  <node id="4" version="1" lat="-30.0300" lon="-51.2270"/>
  <node id="5" version="1" lat="-30.0290" lon="-51.2280"/>
  <node id="6" version="1" lat="-30.0280" lon="-51.2280"/>
  <node id="7" version="1" lat="-30.0270" lon="-51.2280"/>
  <way id="10" version="1"><nd ref="1"/><nd ref="2"/><nd ref="3"/><nd ref="4"/>
    <tag k="highway" v="residential"/><tag k="oneway" v="yes"/></way>
  <way id="11" version="1"><nd ref="3"/><nd ref="5"/>
    <tag k="highway" v="footway"/></way>
  <way id="12" version="1"><nd ref="5"/><nd ref="6"/>
    <tag k="highway" v="motorway"/></way>
  <way id="13" version="1"><nd ref="6"/><nd ref="7"/>
    <tag k="highway" v="service"/><tag k="access" v="private"/></way>
  <way id="14" version="1"><nd ref="4"/><nd ref="7"/>
    <tag k="highway" v="path"/><tag k="foot" v="no"/></way>
</osm>
"""


def test_walk_rules_parsed_from_osmnx():
    rules = osm_extract.WALK_RULES
    assert ("highway", "exists", None) in rules
    assert any(k == "foot" and op == "not_match" for k, op, _ in rules)


@pytest.mark.parametrize("tags, ok", [
    ({"highway": "residential"}, True),
    ({"highway": "footway"}, True),
    ({"highway": "steps"}, True),
    ({"highway": "motorway"}, False),
    ({"highway": "motorway_link"}, False),     # overpass regex is unanchored: "motor" matches
    ({"highway": "cycleway"}, False),
    ({"highway": "service", "access": "private"}, False),
    ({"highway": "path", "foot": "no"}, False),
    ({"highway": "primary", "sidewalk": "separate"}, False),
    ({"building": "yes"}, False),              # no highway tag
])
def test_is_walkable_matches_osmnx_walk_filter(tags, ok):
    assert osm_extract.is_walkable(tags) is ok


def test_graph_from_osm_xml_filters_and_is_bidirectional(tmp_path):
    f = tmp_path / "city.osm"
    f.write_text(OSM_XML, encoding="utf-8")
    G = osm_extract.graph_from_osm_xml(f, box(-51.24, -30.04, -51.22, -30.02))
    assert G.graph["crs"] == "epsg:4326" or str(G.graph["crs"]).lower() == "epsg:4326"
    hw = {d["highway"] for _, _, d in G.edges(data=True)}
    assert hw == {"residential", "footway"}          # motorway, private service, foot=no dropped
    assert set(G.nodes) == {1, 3, 4, 5}                # simplified: node 2 is interstitial
    assert G.has_edge(4, 3) and G.has_edge(3, 4)       # walking ignores oneway


def test_graph_from_osm_xml_truncates_to_polygon(tmp_path):
    f = tmp_path / "city.osm"
    f.write_text(OSM_XML, encoding="utf-8")
    # polygon holds nodes 1-2 only; truncate_by_edge keeps neighbour 3 (as graph_from_polygon does), not 4 or 5
    G = osm_extract.graph_from_osm_xml(f, box(-51.2305, -30.0305, -51.2285, -30.0295))
    assert 4 not in G.nodes and 5 not in G.nodes and 3 in G.nodes


@pytest.mark.skipif(shutil.which("osmium") is None and not osm_extract.OSMIUM.exists(), reason="osmium not installed")
def test_extract_city_osm_clips_pbf(tmp_path):
    xml = tmp_path / "all.osm"
    xml.write_text(OSM_XML, encoding="utf-8")
    pbf = tmp_path / "all.osm.pbf"
    subprocess.run([str(osm_extract.OSMIUM), "cat", str(xml), "-o", str(pbf)], check=True)
    out = tmp_path / "clip.osm"
    osm_extract.extract_city_osm(pbf, box(-51.2305, -30.0305, -51.2275, -30.0295), out)
    txt = out.read_text(encoding="utf-8")
    assert 'id="1"' in txt and 'id="7"' not in txt


def test_make_extract_downloader_caches_graphml(tmp_path, monkeypatch):
    calls = {"n": 0}

    def fake_extract(src, poly, out):
        calls["n"] += 1
        out.write_text(OSM_XML, encoding="utf-8")

    monkeypatch.setattr(osm_extract, "extract_city_osm", fake_extract)
    dl = osm_extract.make_extract_downloader(tmp_path / "brazil.osm.pbf", tmp_path / "work")
    poly = box(-51.24, -30.04, -51.22, -30.02)
    G1 = dl(poly, tmp_path / "osm" / "c.graphml")
    G2 = dl(poly, tmp_path / "osm" / "c.graphml")
    assert calls["n"] == 1 and isinstance(G2, nx.MultiDiGraph)
    assert G1.number_of_edges() == G2.number_of_edges()
