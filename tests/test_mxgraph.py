
import pytest
import sys
import defusedxml.ElementTree as dxml
from mxgraph.mxgraph import *

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

def test_read_geometry():
    s = '<mxGeometry x="700" y="50" width="120" height="60" as="geometry" />'
    geom_xml = dxml.fromstring(s)
    geom = MxGeometry.from_xml(geom_xml)
    assert geom.x == 700
    assert geom.y == 50
    assert geom.width == 120
    assert geom.height == 60

def test_create_geometry():
    geom = MxGeometry(50,220,120,60)
    assert geom.x == 50
    assert geom.y == 220
    assert geom.width == 120
    assert geom.height == 60
    x = geom.to_xml()
    assert x.get('x') == '50'
    assert x.get('y') == '220'
    assert x.get('width') == '120'
    assert x.get('height') == '60'

def test_read_mxcell_vertex():
    cell_string = """
    <mxCell id="ltYZWVSzQ5NPo-W-WjXg-1" value="test vertex" style="rounded=0;whiteSpace=wrap;html=1;" vertex="1" parent="1">
      <mxGeometry x="50" y="220" width="120" height="60" as="geometry"/>
    </mxCell>"""
    cell_xml = dxml.fromstring(cell_string)
    cell = MxCell.from_xml(cell_xml)
    assert cell['id'] == "ltYZWVSzQ5NPo-W-WjXg-1"
    assert cell['value'] == "test vertex"
    assert dict(cell.style.items()) == { 'rounded':'0', 'whiteSpace':'wrap', 'html': '1' }

def test_create_mxcell_vertex():
    cell = MxCell()
    cell['id'] = '42'
    cell['vertex'] = '1'
    cell['parent'] = '1'
    style_string = "ellipse;html=1;"
    style = MxStyle.from_string(style_string)
    cell.set_style(style)
    geom = MxGeometry(300,400,100,50)
    cell.set_geometry(geom)
    x = cell.to_xml()
    assert x.get('id') == '42'
    assert x.get('vertex') == '1'
    assert x.get('parent') == '1'
    assert x.get('style') == style_string
    assert dict(x.find('mxGeometry').items()) == { 'x': '300', 'y': '400', 'width': '100', 'height': '50', 'as': 'geometry' }


def test_read_mxcell_vertex():
    cell_string = """
    <mxCell id="ltYZWVSzQ5NPo-W-WjXg-1" value="test vertex" style="rounded=0;whiteSpace=wrap;html=1;" vertex="1" parent="1">
      <mxGeometry x="50" y="220" width="120" height="60" as="geometry"/>
    </mxCell>"""
    cell_xml = dxml.fromstring(cell_string)
    cell = MxCell.from_xml(cell_xml)
    assert cell['id'] == "ltYZWVSzQ5NPo-W-WjXg-1"
    assert cell['value'] == "test vertex"
    assert dict(cell.style.items()) == { 'rounded':'0', 'whiteSpace':'wrap', 'html': '1' }

def test_create_mxcell_vertex():
    cell = MxCell()
    cell['id'] = '42'
    cell['vertex'] = '1'
    cell['parent'] = '1'
    style_string = "ellipse;html=1;"
    style = MxStyle.from_string(style_string)
    cell.set_style(style)
    geom = MxGeometry(300,400,100,50)
    cell.set_geometry(geom)
    x = cell.to_xml()
    assert x.get('id') == '42'
    assert x.get('vertex') == '1'
    assert x.get('parent') == '1'
    assert x.get('style') == style_string
    assert dict(x.find('mxGeometry').items()) == { 'x': '300', 'y': '400', 'width': '100', 'height': '50', 'as': 'geometry' }



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

