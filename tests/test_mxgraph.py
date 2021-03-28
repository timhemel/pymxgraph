
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

def test_read_vertex_geometry(cell_store):
    s = '<mxGeometry x="700" y="50" width="120" height="60" as="geometry" />'
    geom_xml = dxml.fromstring(s)
    geom = MxVertexGeometry.from_xml(cell_store, geom_xml)
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

def test_read_edge_geometry(cell_store):
    s = """
      <mxGeometry relative="1" as="geometry">
        <Array as="points">
          <mxPoint x="740" y="180"/>
        </Array>
      </mxGeometry>"""
    geom_xml = dxml.fromstring(s)
    geom = MxEdgeGeometry.from_xml(cell_store, geom_xml)
    assert geom.width == None
    assert geom.height == None
    assert len(geom.points) == 1
    assert geom.points[0].x == 740
    assert geom.points[0].y == 180
    assert geom.source_point is None
    assert geom.target_point is None

def test_read_edge_geometry_with_source_and_target_points(cell_store):
    s = """
    <mxGeometry width="50" height="50" relative="1" as="geometry">
        <mxPoint x="400" y="450" as="sourcePoint"/>
        <mxPoint x="450" y="400" as="targetPoint"/>
        <Array as="points">
          <mxPoint x="250" y="250"/>
        </Array>
      </mxGeometry>"""
    geom_xml = dxml.fromstring(s)
    geom = MxEdgeGeometry.from_xml(cell_store, geom_xml)
    assert geom.width == 50
    assert geom.height == 50
    assert len(geom.points) == 1
    assert geom.points[0].x == 250
    assert geom.points[0].y == 250
    assert geom.source_point.x == 400
    assert geom.source_point.y == 450
    assert geom.target_point.x == 450
    assert geom.target_point.y == 400

def test_create_edge_geometry():
    points = [ MxPoint(x,y) for x,y in [ (10,20), (30,40) ] ]
    geom = MxEdgeGeometry(points)
    x = geom.to_xml()
    points = x.findall('Array/mxPoint')
    assert points[0].get('x') == '10'
    assert points[0].get('y') == '20'
    assert points[1].get('x') == '30'
    assert points[1].get('y') == '40'

def test_create_edge_geometry_with_source_and_target_points(cell_store):
    points = [ MxPoint(x,y) for x,y in [ (10,20), (30,40) ] ]
    geom = MxEdgeGeometry(points)
    geom.source_point = MxPoint(50,60)
    geom.target_point = MxPoint(70,80)
    geom.width = 150
    geom.height = 160
    x = geom.to_xml()
    assert x.get('width') == '150'
    assert x.get('height') == '160'
    points = x.findall('Array/mxPoint')
    assert points[0].get('x') == '10'
    assert points[0].get('y') == '20'
    assert points[1].get('x') == '30'
    assert points[1].get('y') == '40'
    source_point_xml = x.find("mxPoint[@as='sourcePoint']")
    target_point_xml = x.find("mxPoint[@as='targetPoint']")
    assert source_point_xml.get('x') == '50'
    assert source_point_xml.get('y') == '60'
    assert target_point_xml.get('x') == '70'
    assert target_point_xml.get('y') == '80'



def test_read_root_vertex(cell_store):
    cell_string = """<mxCell id="0" />"""
    cell_xml = dxml.fromstring(cell_string)
    cell = MxCell.from_xml(cell_store, cell_xml)
    assert cell.cell_id == "0"
    assert cell.parent == None

def test_create_root_vertex(cell_store):
    cell = MxGroupCell(cell_store, '0')
    x = cell.to_xml()
    assert x.get('id') == '0'
    assert x.get('parent') == None

def test_read_mxcell_vertex(cell_store):
    parent = MxGroupCell(cell_store, '1')
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

def test_create_mxcell_vertex(cell_store):
    parent = MxGroupCell(cell_store, '1')
    cell_store.add_cell(parent)
    cell = MxVertexCell(cell_store, '42')
    cell.parent = parent
    cell_store.add_cell(cell)
    style_string = "ellipse;html=1;"
    style = MxStyle.from_string(style_string)
    cell.style = style
    geom = MxVertexGeometry(300,400,100,50)
    cell.geometry = geom
    x = cell.to_xml()
    assert x.get('id') == '42'
    assert x.get('vertex') == '1'
    assert x.get('parent') == '1'
    assert x.get('style') == style_string
    assert dict(x.find('mxGeometry').items()) == { 'x': '300', 'y': '400', 'width': '100', 'height': '50', 'as': 'geometry' }


def test_read_mxcell_edge(cell_store):
    parent = MxGroupCell(cell_store, '1')
    cell_store.add_cell(parent)
    source = MxVertexCell(cell_store, "ltYZWVSzQ5NPo-W-WjXg-3")
    cell_store.add_cell(source)
    target = MxVertexCell(cell_store, "ltYZWVSzQ5NPo-W-WjXg-2")
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
        x = cell.source

 

def test_create_mxcell_edge(cell_store):
    parent = MxGroupCell(cell_store, '1')
    cell_store.add_cell(parent)
    cell = MxEdgeCell(cell_store, '42')
    cell.parent = parent
    cell_store.add_cell(cell)
    source_vertex = MxVertexCell(cell_store, '23')
    cell_store.add_cell(source_vertex)
    target_vertex = MxVertexCell(cell_store, '54')
    cell_store.add_cell(target_vertex)
    cell.source = source_vertex
    cell.target = target_vertex
    style_string = "edgeStyle=none;curved=1;orthogonalLoop=1;jettySize=auto;html=1;"
    style = MxStyle.from_string(style_string)
    cell.style = style
    geom = MxEdgeGeometry([MxPoint(240,310)])
    cell.geometry = geom
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
    edge.style = style
    geom = cs.mxEdgeGeometry([MxPoint(240,310)])
    edge.geometry = geom
    assert source_vertex.parent == parent
    assert edge.parent == parent
    assert edge.source == source_vertex
    assert edge.target == target_vertex
    assert set(cs.cells.keys()) == set([parent.cell_id, source_vertex.cell_id, target_vertex.cell_id, edge.cell_id])

def test_cell_store_cell_id():
    # add 2 cells with existing id, see if you get a different one
    cs = CellStore()
    parent = cs.mxGroupCell()
    source_vertex = MxVertexCell(cs, str(int(parent.cell_id) + 1))
    cs.add_cell(source_vertex)
    target_vertex = MxVertexCell(cs, str(int(parent.cell_id) + 2))
    cs.add_cell(target_vertex)
    edge = cs.mxEdgeCell(parent = parent, source = source_vertex, target = target_vertex)
    assert edge.cell_id not in [ parent.cell_id, source_vertex.cell_id, target_vertex.cell_id ]

def test_read_mxgraph_model(cell_store):
    graph_string = """
    <mxGraphModel dx="1102" dy="825" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="850" pageHeight="1100" math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />
    <mxCell id="X49CK6sKVQ1RPVU1MZDR-1" value="Ext1" style="rounded=0;whiteSpace=wrap;html=1;" vertex="1" parent="1">
      <mxGeometry x="90" y="320" width="120" height="60" as="geometry" />
    </mxCell>
    <mxCell id="X49CK6sKVQ1RPVU1MZDR-6" value="" style="group" vertex="1" connectable="0" parent="1">
      <mxGeometry x="340" y="240" width="80" height="210" as="geometry" />
    </mxCell>
    <mxCell id="X49CK6sKVQ1RPVU1MZDR-2" value="P1" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;" vertex="1" parent="X49CK6sKVQ1RPVU1MZDR-6">
      <mxGeometry width="80" height="80" as="geometry" />
    </mxCell>
    <mxCell id="X49CK6sKVQ1RPVU1MZDR-3" value="P2" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;" vertex="1" parent="X49CK6sKVQ1RPVU1MZDR-6">
      <mxGeometry y="130" width="80" height="80" as="geometry" />
    </mxCell>
    <mxCell id="X49CK6sKVQ1RPVU1MZDR-4" value="" style="endArrow=classic;html=1;fontColor=#FF3333;" edge="1" parent="X49CK6sKVQ1RPVU1MZDR-6" source="X49CK6sKVQ1RPVU1MZDR-3" target="X49CK6sKVQ1RPVU1MZDR-2">
      <mxGeometry width="50" height="50" relative="1" as="geometry">
        <mxPoint x="400" y="450" as="sourcePoint" />
        <mxPoint x="450" y="400" as="targetPoint" />
      </mxGeometry>
    </mxCell>
    <mxCell id="X49CK6sKVQ1RPVU1MZDR-5" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="X49CK6sKVQ1RPVU1MZDR-6" source="X49CK6sKVQ1RPVU1MZDR-3" target="X49CK6sKVQ1RPVU1MZDR-2">
      <mxGeometry relative="1" as="geometry">
        <Array as="points">
          <mxPoint x="180" y="170" />
          <mxPoint x="180" y="40" />
        </Array>
      </mxGeometry>
    </mxCell>
  </root>
</mxGraphModel>"""
    graph_xml = dxml.fromstring(graph_string)
    mx = MxGraphModel.from_xml(cell_store, graph_xml)
    assert mx['pageWidth'] == '850'
    assert len(cell_store.items()) == 8
    assert cell_store['X49CK6sKVQ1RPVU1MZDR-5'].parent == cell_store['X49CK6sKVQ1RPVU1MZDR-6']

def test_read_edge_defined_before_vertex(cell_store):
    graph_string = """
    <mxGraphModel dx="1102" dy="825" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="850" pageHeight="1100" math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />
    <mxCell id="X49CK6sKVQ1RPVU1MZDR-1" value="Ext1" style="rounded=0;whiteSpace=wrap;html=1;" vertex="1" parent="1">
      <mxGeometry x="90" y="320" width="120" height="60" as="geometry" />
    </mxCell>
    <mxCell id="X49CK6sKVQ1RPVU1MZDR-2" value="P1" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;" vertex="1" parent="X49CK6sKVQ1RPVU1MZDR-6">
      <mxGeometry width="80" height="80" as="geometry" />
    </mxCell>
    <mxCell id="X49CK6sKVQ1RPVU1MZDR-4" value="" style="endArrow=classic;html=1;fontColor=#FF3333;" edge="1" parent="X49CK6sKVQ1RPVU1MZDR-6" source="X49CK6sKVQ1RPVU1MZDR-3" target="X49CK6sKVQ1RPVU1MZDR-2">
      <mxGeometry width="50" height="50" relative="1" as="geometry">
        <mxPoint x="400" y="450" as="sourcePoint" />
        <mxPoint x="450" y="400" as="targetPoint" />
      </mxGeometry>
    </mxCell>
    <mxCell id="X49CK6sKVQ1RPVU1MZDR-5" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="X49CK6sKVQ1RPVU1MZDR-6" source="X49CK6sKVQ1RPVU1MZDR-3" target="X49CK6sKVQ1RPVU1MZDR-2">
      <mxGeometry relative="1" as="geometry">
        <Array as="points">
          <mxPoint x="180" y="170" />
          <mxPoint x="180" y="40" />
        </Array>
      </mxGeometry>
    </mxCell>
    <mxCell id="X49CK6sKVQ1RPVU1MZDR-6" value="" style="group" vertex="1" connectable="0" parent="1">
      <mxGeometry x="340" y="240" width="80" height="210" as="geometry" />
    </mxCell>
    <mxCell id="X49CK6sKVQ1RPVU1MZDR-3" value="P2" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;" vertex="1" parent="X49CK6sKVQ1RPVU1MZDR-6">
      <mxGeometry y="130" width="80" height="80" as="geometry" />
    </mxCell>
  </root>
</mxGraphModel>"""
    graph_xml = dxml.fromstring(graph_string)
    mx = MxGraphModel.from_xml(cell_store, graph_xml)
    assert cell_store.cells['X49CK6sKVQ1RPVU1MZDR-5'].target == cell_store.cells['X49CK6sKVQ1RPVU1MZDR-2']
    assert cell_store.cells['X49CK6sKVQ1RPVU1MZDR-5'].parent == cell_store.cells['X49CK6sKVQ1RPVU1MZDR-6']


def test_create_mxgraph_model(cell_store):
    g = MxGraphModel()
    g['pageWidth'] = '850'
    cell0 = cell_store.mxGroupCell()
    cell1 = cell_store.mxGroupCell(parent = cell0)
    v1 = cell_store.mxVertexCell(parent = cell1)
    v1.style = cell_store.mxStyle(ellipse=None, x=45)
    v1.geometry = cell_store.mxVertexGeometry(10,20,400,300)
    v2 = cell_store.mxVertexCell(parent = cell1)
    v2.style = cell_store.mxStyle(ellipse=None, x=45)
    v2.geometry = cell_store.mxVertexGeometry(10,20,400,300)
    v3 = cell_store.mxEdgeCell(parent = cell1, source=v1, target=v2)
    v3.style = cell_store.mxStyle(curve=1)
    v3.geometry = cell_store.mxEdgeGeometry([MxPoint(200,10)])

    g_xml = g.to_xml(cell_store)
    assert g_xml.get('pageWidth') == '850'
    cells_xml = g_xml.findall('root/mxCell')
    assert len(cells_xml) == 5
    assert cells_xml[4].get('source') == v3.source.cell_id


def xtest_read_file():
    mx = MxGraphModel()
    mx.from_file("test.drawio")
    mx.to_file(sys.stdout)
    assert False

def main():
    mxfile = MxFile.from_file(sys.stdin)
    mxfile.to_file(sys.stdout)

if __name__=="__main__":
    main()

