
import pytest
import sys
import defusedxml.ElementTree as dxml
from mxgraph.mxgraph import *

@pytest.fixture
def cell_store():
    return CellStore()

def test_read_mxstyle():
    style_string = "ellipse;whiteSpace=wrap;html=1;aspect=fixed;"
    style = MxStyle.from_string(style_string)
    assert style.get('ellipse') is None
    assert style['html'] == '1'
    s = style.to_string()
    assert s == style_string

def test_create_mxstyle():
    style = MxStyle()
    style['html'] = '1'
    style['ellipse'] = None
    s = style.to_string()
    assert s == "ellipse;html=1;"

def test_read_geometry(cell_store):
    s = '<mxGeometry x="700" y="50" width="120" height="60" as="geometry" />'
    geom_xml = dxml.fromstring(s)
    geom = MxGeometry.from_xml(cell_store, geom_xml)
    assert geom.x == 700
    assert geom.y == 50
    assert geom.width == 120
    assert geom.height == 60


def test_create_vertex_geometry():
    geom = MxVertexGeometry(50,220,120,60)
    assert geom.x == 50
    assert geom.y == 220
    assert geom.width == 120
    assert geom.height == 60
    x = geom.to_xml()
    assert x.get('x') == '50'
    assert x.get('y') == '220'
    assert x.get('width') == '120'
    assert x.get('height') == '60'

def test_read_root_vertex(cell_store):
    cell_string = """<mxCell id="0" />"""
    cell_xml = dxml.fromstring(cell_string)
    cell = MxCell.from_xml(cell_store, cell_xml)
    assert cell.cell_id == "0"
    assert cell.parent == None

def test_create_root_vertex():
    cell = MxGroupCell('0')
    x = cell.to_xml()
    assert x.get('id') == '0'
    assert x.get('parent') == None

def test_read_mxcell_vertex(cell_store):
    parent = MxGroupCell('1')
    cell_store.add_cell(parent)
    cell_string = """
    <mxCell id="ltYZWVSzQ5NPo-W-WjXg-1" value="test vertex" style="rounded=0;whiteSpace=wrap;html=1;" vertex="1" parent="1">
      <mxGeometry x="50" y="220" width="120" height="60" as="geometry"/>
    </mxCell>"""
    cell_xml = dxml.fromstring(cell_string)
    cell = MxCell.from_xml(cell_store, cell_xml)
    assert cell.cell_id == "ltYZWVSzQ5NPo-W-WjXg-1"
    assert cell.parent == parent
    assert cell.is_vertex()
    assert cell['value'] == "test vertex"
    assert dict(cell.style.items()) == { 'rounded':'0', 'whiteSpace':'wrap', 'html': '1' }

def test_create_mxcell_vertex():
    parent = MxGroupCell('1')
    cell = MxVertexCell('42')
    cell.set_parent(parent)
    style_string = "ellipse;html=1;"
    style = MxStyle.from_string(style_string)
    cell.set_style(style)
    geom = MxVertexGeometry(300,400,100,50)
    cell.set_geometry(geom)
    x = cell.to_xml()
    assert x.get('id') == '42'
    assert x.get('vertex') == '1'
    assert x.get('parent') == '1'
    assert x.get('style') == style_string
    assert dict(x.find('mxGeometry').items()) == { 'x': '300', 'y': '400', 'width': '100', 'height': '50', 'as': 'geometry' }


def test_read_mxcell_edge(cell_store):
    parent = MxGroupCell('1')
    cell_store.add_cell(parent)
    source = MxVertexCell("ltYZWVSzQ5NPo-W-WjXg-3")
    cell_store.add_cell(source)
    target = MxVertexCell("ltYZWVSzQ5NPo-W-WjXg-2")
    cell_store.add_cell(target)

    cell_string = """
    <mxCell id="ltYZWVSzQ5NPo-W-WjXg-15" style="edgeStyle=none;curved=1;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="ltYZWVSzQ5NPo-W-WjXg-3" target="ltYZWVSzQ5NPo-W-WjXg-2">
      <mxGeometry relative="1" as="geometry">
        <Array as="points">
          <mxPoint x="240" y="310"/>
        </Array>
      </mxGeometry>
    </mxCell>"""
    cell_xml = dxml.fromstring(cell_string)
    cell = MxCell.from_xml(cell_store, cell_xml)
    assert cell.cell_id == "ltYZWVSzQ5NPo-W-WjXg-15"
    assert cell.is_edge()
    assert cell.source == source
    assert cell.target == target
    assert dict(cell.style.items()) == { "edgeStyle": "none", "curved": "1", "orthogonalLoop": "1", "jettySize": "auto", "html": "1" }

def test_read_mxcell_edge_unknown_vertex(cell_store):
    cell_string = """
    <mxCell id="ltYZWVSzQ5NPo-W-WjXg-15" style="edgeStyle=none;curved=1;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="ltYZWVSzQ5NPo-W-WjXg-3" target="ltYZWVSzQ5NPo-W-WjXg-2">
      <mxGeometry relative="1" as="geometry">
        <Array as="points">
          <mxPoint x="240" y="310"/>
        </Array>
      </mxGeometry>
    </mxCell>"""
    cell_xml = dxml.fromstring(cell_string)
    with pytest.raises(KeyError):
        cell = MxCell.from_xml(cell_store, cell_xml)
 

def test_create_mxcell_edge():
    parent = MxGroupCell('1')
    cell = MxEdgeCell('42')
    cell.set_parent(parent)
    source_vertex = MxVertexCell('23')
    target_vertex = MxVertexCell('54')
    cell.set_source(source_vertex)
    cell.set_target(target_vertex)
    style_string = "edgeStyle=none;curved=1;orthogonalLoop=1;jettySize=auto;html=1;"
    style = MxStyle.from_string(style_string)
    cell.set_style(style)
    geom = MxEdgeGeometry([(240,310)])
    cell.set_geometry(geom)
    x = cell.to_xml()
    assert x.get('id') == '42'
    assert x.get('edge') == '1'
    assert x.get('parent') == '1'
    assert x.get('style') == style_string
    assert x.get('source') == source_vertex.cell_id
    assert x.get('target') == target_vertex.cell_id
    xml_geom = x.find('mxGeometry')
    assert xml_geom.get('relative') == '1'
    points =  xml_geom.findall('Array/mxPoint')
    assert len(points) == 1
    assert dict(points[0].items()) == { 'x': "240", 'y':"310" }

def test_cell_store():
    cs = CellStore()
    parent = cs.mxGroupCell()
    source_vertex = cs.mxVertexCell(parent = parent)
    target_vertex = cs.mxVertexCell(parent = parent)
    edge = cs.mxEdgeCell(parent = parent, source = source_vertex, target = target_vertex)
    style_string = "edgeStyle=none;curved=1;orthogonalLoop=1;jettySize=auto;html=1;"
    style = cs.mxStyle(edgeStyle='none',curved=1,orthogonalLoop=1,jettySize='auto',html=1)
    edge.set_style(style)
    geom = cs.mxEdgeGeometry([(240,310)])
    edge.set_geometry(geom)
    assert source_vertex.get_parent() == parent
    assert edge.get_parent() == parent
    assert edge.source == source_vertex
    assert edge.target == target_vertex
    assert set(cs.cells.keys()) == set([parent.cell_id, source_vertex.cell_id, target_vertex.cell_id, edge.cell_id])

def test_cell_store_cell_id():
    # add 2 cells with existing id, see if you get a different one
    cs = CellStore()
    parent = cs.mxGroupCell()
    source_vertex = MxVertexCell(str(int(parent.cell_id) + 1))
    cs.add_cell(source_vertex)
    target_vertex = MxVertexCell(str(int(parent.cell_id) + 2))
    cs.add_cell(target_vertex)
    edge = cs.mxEdgeCell(parent = parent, source = source_vertex, target = target_vertex)
    assert edge.cell_id not in [ parent.cell_id, source_vertex.cell_id, target_vertex.cell_id ]

def xtest_read_file():
    mx = MxGraph()
    mx.from_file("test.drawio")
    mx.to_file(sys.stdout)
    assert False

def main():
    mx = MxGraph()
    mx.from_file(sys.stdin)
    mx.to_file(sys.stdout)

if __name__=="__main__":
    main()

