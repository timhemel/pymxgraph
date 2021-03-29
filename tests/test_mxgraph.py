
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
    geom = MxGeometry.from_xml(cell_store, geom_xml)
    assert geom.x == 700
    assert geom.y == 50
    assert geom.width == 120
    assert geom.height == 60


def test_create_vertex_geometry():
    geom = MxGeometry(x=50,y=220,width=120,height=60)
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
    geom = MxGeometry.from_xml(cell_store, geom_xml)
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
    geom = MxGeometry.from_xml(cell_store, geom_xml)
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
    geom = MxGeometry(relative=True)
    geom.points = [ MxPoint(x,y) for x,y in [ (10,20), (30,40) ] ]
    x = geom.to_xml()
    points = x.findall('Array/mxPoint')
    assert points[0].get('x') == '10'
    assert points[0].get('y') == '20'
    assert points[1].get('x') == '30'
    assert points[1].get('y') == '40'

def test_create_edge_geometry_with_source_and_target_points(cell_store):
    geom = MxGeometry(relative=True)
    geom.points = [ MxPoint(x,y) for x,y in [ (10,20), (30,40) ] ]
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
    geom = MxGeometry(x=300,y=400,width=100,height=50)
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
    geom = MxGeometry(relative=True)
    geom.points = [MxPoint(240,310)]
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
    parent = MxGroupCell(cs, '0')
    cs.add_cell(parent)
    source_vertex = MxVertexCell(cs, cs.new_id())
    cs.add_cell(source_vertex)
    target_vertex = MxVertexCell(cs, cs.new_id())
    cs.add_cell(target_vertex)
    edge = MxEdgeCell(cs, cs.new_id())
    cs.add_cell(edge)

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



def test_read_mxgraph_model():
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
    mx = MxGraphModel.from_xml(graph_xml)
    assert mx['pageWidth'] == '850'
    assert len(mx.cells) == 8
    assert mx.cells['X49CK6sKVQ1RPVU1MZDR-5'].parent == mx.cells['X49CK6sKVQ1RPVU1MZDR-6']

def test_read_edge_defined_before_vertex():
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
    mx = MxGraphModel.from_xml(graph_xml)
    assert mx.cells['X49CK6sKVQ1RPVU1MZDR-5'].target == mx.cells['X49CK6sKVQ1RPVU1MZDR-2']
    assert mx.cells['X49CK6sKVQ1RPVU1MZDR-5'].parent == mx.cells['X49CK6sKVQ1RPVU1MZDR-6']


def test_create_mxgraph_model():
    gm = MxGraphModel()
    gm['pageWidth'] = '850'
    cell0 = gm.cells.mxGroupCell()
    cell1 = gm.cells.mxGroupCell(parent = cell0)
    v1 = gm.cells.mxVertexCell(parent = cell1)
    v1.style = MxStyle(ellipse=None, x=45)
    v1.geometry = MxGeometry(x=10,y=20,width=400,height=300)
    v2 = gm.cells.mxVertexCell(parent = cell1)
    v2.style = MxStyle(ellipse=None, x=45)
    v2.geometry = MxGeometry(x=10,y=20,width=400,height=300)
    v3 = gm.cells.mxEdgeCell(parent = cell1, source=v1, target=v2)
    v3.style = MxStyle(curve=1)
    v3.geometry = MxGeometry(relative=True)
    v3.geometry.points = [MxPoint(200,10)]

    gm_xml = gm.to_xml()
    assert gm_xml.get('pageWidth') == '850'
    cells_xml = gm_xml.findall('root/mxCell')
    assert len(cells_xml) == 5
    assert cells_xml[4].get('source') == v3.source.cell_id

def test_create_mxgraphmodel_prefix_and_postfix():
    gm = MxGraphModel()
    gm.prefix="abc"
    gm.postfix="xyz"
    cell0 = gm.cells.mxGroupCell()
    v1 = gm.cells.mxVertexCell(parent = cell0)
    v1.style = MxStyle(ellipse=None, x=45)
    v1.geometry = MxGeometry(x=10,y=20,width=400,height=300)
    gm_xml = gm.to_xml()
    assert gm_xml.findall('root/mxCell')[1].get('id') == f'abc-1-xyz'

def test_mxgraph_add_to_default_root():
    g = MxGraph()
    parent = g.create_group_cell()
    assert parent.parent == g.root

def test_mxgraph_insert_vertex():
    g = MxGraph()
    parent = g.create_group_cell()
    style = { 'ellipse': None, 'whiteSpace': 'wrap', 'html': '1', 'aspect': 'fixed' }
    source_vertex = g.insert_vertex(parent = parent, value="Hello!", x=100, y=200, width=400, height=300, style=style, relative=False)

    assert source_vertex.parent == parent
    assert source_vertex.geometry.x == 100
    assert source_vertex.geometry.width == 400
    assert source_vertex.geometry.relative == False
    assert source_vertex.style == style

def test_mxgraph_insert_edge():
    g = MxGraph()
    parent = g.create_group_cell()
    style = { 'ellipse': None, 'whiteSpace': 'wrap', 'html': '1', 'aspect': 'fixed' }
    source_vertex = g.insert_vertex(parent=parent, value="Hello!", x=100, y=200, width=400, height=300, style=style, relative=False)
    target_vertex = g.insert_vertex(parent=parent, value="Goodbye!", x=400, y=200, width=400, height=300, style=style, relative=False)
    edge_style = { 'edgeStyle': 'none', 'curved': '1', 'orthogonalLoop': '1', 'jettySize': 'auto', 'html': '1' }
    edge = g.insert_edge(parent=parent, source=source_vertex, target=target_vertex, style=edge_style)
    g.add_edge_geometry(edge, [(10,20),(30,40)])
    g.set_source_point(edge, (50,60))
    g.set_target_point(edge, (70,80))
    assert edge.source == source_vertex
    assert edge.target == target_vertex
    assert edge.parent == parent
    assert edge.style == edge_style
    assert len(edge.geometry.points) == 2
    assert edge.geometry.points[0].x == 10
    assert edge.geometry.points[0].y == 20
    assert edge.geometry.points[1].x == 30
    assert edge.geometry.points[1].y == 40
    assert edge.geometry.source_point.x == 50
    assert edge.geometry.source_point.y == 60
    assert edge.geometry.target_point.x == 70
    assert edge.geometry.target_point.y == 80


def bla():
    edge = cs.mxEdgeCell(parent = parent, source = source_vertex, target = target_vertex)
    style_string = "edgeStyle=none;curved=1;orthogonalLoop=1;jettySize=auto;html=1;"
    style = MxStyle(edgeStyle='none',curved=1,orthogonalLoop=1,jettySize='auto',html=1)
    edge.style = style
    edge.geometry = MxGeometry(relative=True)
    edge.geometry.points = [MxPoint(240,310)]
    assert source_vertex.parent == parent
    assert edge.parent == parent
    assert edge.source == source_vertex
    assert edge.target == target_vertex
    assert set(cs.cells.keys()) == set([parent.cell_id, source_vertex.cell_id, target_vertex.cell_id, edge.cell_id])


def xtest_read_file():
    mx = MxGraphModel()
    mx.from_file("test.drawio")
    mx.to_file(sys.stdout)
    assert False

def main():
    mxfile = MxFile.from_file(sys.stdin)
    ET.dump(mxfile.diagram.mxgraph_model.to_xml(mxfile.diagram.cell_store))
    # mxfile.to_file(sys.stdout)

if __name__=="__main__":
    main()

