

import base64
import urllib.parse
import zlib
import defusedxml.ElementTree as dxml
import xml.etree.ElementTree as ET

def create_mxcell_from_xml(xml_element):
    c = MxCell()
    c.from_xml(xml_element)
    return c

def create_mxcell_vertex(cell_id):
    c = MxCell()
    c.set_id(cell_id)
    c.set_vertex()
    return c

def create_mxcell_edge(cell_id):
    c = MxCell()
    c.set_id(cell_id)
    c.set_edge()
    return c

def parse_style_string(s):
    def trysplit(x):
        try:
            k,v = x.split('=', maxsplit=1)
        except ValueError:
            k,v = x,None
        return k,v

    l = [ x.strip() for x in s.strip().split(';') ]
    if l[-1] == '':
        del l[-1]
    kvs = [ trysplit(x) for x in l ]
    return dict(kvs)

class CellStore:

    def __init__(self):
        self.current_id = 0
        self.cells = {}

    def __new_id(self):
        while str(self.current_id) in self.cells:
            self.current_id += 1
        return str(self.current_id)

    def get(self, key):
        return self.cells.get(key)

    def __getitem__(self, key):
        return self.cells[key]

    def __setitem__(self, key, value):
        self.cells[key] = value

    def items(self):
        return self.cells.items()

    def add_cell(self, cell):
        self.cells[cell['id']] = cell

    def mxGroupCell(self, parent=None):
        cell = MxGroupCell()
        cell['id'] = self.__new_id()
        self.add_cell(cell)
        return cell

    def mxVertexCell(self, parent=None):
        cell = MxVertexCell()
        cell['id'] = self.__new_id()
        cell.set_parent(parent)
        self.add_cell(cell)
        return cell

    def mxEdgeCell(self, parent=None, source=None, target=None):
        cell = MxEdgeCell()
        cell['id'] = self.__new_id()
        cell.set_parent(parent)
        cell.set_source(source)
        cell.set_target(target)
        self.add_cell(cell)
        return cell

    def mxStyle(self, **kwargs):
        return MxStyle(**kwargs)

    def mxEdgeGeometry(self, points):
        return MxEdgeGeometry(points)

class MxBase:

    def __init__(self):
        self.attrs = {}

    def get(self, key):
        return self.attrs.get(key)

    def __getitem__(self, key):
        return self.attrs[key]

    def __setitem__(self, key, value):
        self.attrs[key] = value

    def items(self):
        return self.attrs.items()


class MxStyle(MxBase):

    def __init__(self, **kwargs):
        self.attrs = kwargs

    @classmethod
    def from_string(cls, s):
        mxstyle = MxStyle()
        mxstyle.attrs = parse_style_string(s)
        return mxstyle

    def to_string(self):
        shapes = [ k+';' for k,v in self.attrs.items() if v is None ]
        styles = [ k+'='+str(v)+';' for k,v in self.attrs.items() if v is not None ]
        return "".join(shapes + styles)

class MxGeometry(MxBase):

    @classmethod
    def from_xml(self, cell_store, xml_element):
        if set(['x','y','width','height']).issubset(xml_element.keys()):
            return MxVertexGeometry.from_xml(cell_store, xml_element)
        else:
            return MxEdgeGeometry.from_xml(cell_store, xml_element)

class MxVertexGeometry(MxGeometry):

    def __init__(self, x, y, width, height):
        super().__init__()
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @classmethod
    def from_xml(cls, cell_store, xml_element):
        return MxVertexGeometry(
                int(xml_element.get('x')),
                int(xml_element.get('y')),
                int(xml_element.get('width')),
                int(xml_element.get('height')))

    def to_xml(self):
        geom = ET.Element('mxGeometry')
        geom.set('x', str(self.x))
        geom.set('y', str(self.y))
        geom.set('width', str(self.width))
        geom.set('height', str(self.height))
        geom.set('as', 'geometry')
        return geom

class MxEdgeGeometry(MxGeometry):

    def __init__(self, points):
        super().__init__()
        self.points = points

    @classmethod
    def from_xml(cls, cell_store, xml_element):
        return None

    def to_xml(self):
        geom = ET.Element('mxGeometry')
        geom.set('relative', '1')
        geom.set('as', 'geometry')
        array = ET.SubElement(geom, 'Array')
        # add points
        for x,y in self.points:
            point = ET.SubElement(array, 'mxPoint')
            point.set('x', str(x))
            point.set('y', str(y))
        return geom


class MxCell(MxBase):

    @classmethod
    def from_xml(cls, cell_store, xml_element):
        # https://jgraph.github.io/mxgraph/docs/js-api/files/model/mxCell-js.html
        # cell = MxCell()
        if xml_element.get('vertex'):
            cell = MxVertexCell.from_xml(cell_store, xml_element)
        elif xml_element.get('edge'):
            cell = MxEdgeCell.from_xml(cell_store, xml_element)
        cell.set_attributes_from_xml(cell_store, xml_element)
        cell_store.add_cell(cell)
        return cell

    def set_attributes_from_xml(self, cell_store, xml_element):
        self.geometry = MxGeometry.from_xml(cell_store, xml_element.find('mxGeometry'))
        self.attrs = dict(xml_element.items())
        self.style = MxStyle.from_string(self.attrs.get('style',''))

    def set_parent(self, parent):
        self.parent = parent
        if parent is not None:
            self.attrs['parent'] = parent['id']

    def get_parent(self):
        return self.parent

    def to_xml(self):
        cell = ET.Element('mxCell')
        for k,v in self.attrs.items():
            cell.set(k,v)
        cell.set('style', self.style.to_string())
        geom = self.geometry.to_xml()
        cell.append(geom)
        return cell

    def is_vertex(self):
        return False

    def is_edge(self):
        return False

    def set_geometry(self, geom):
        self.geometry = geom

    def set_style(self, style):
        self.style = style

class MxGroupCell(MxCell):
    pass

class MxVertexCell(MxCell):

    def __init__(self):
        super().__init__()
        self.attrs['vertex'] = '1'

    @classmethod
    def from_xml(cls, cell_store, xml_element):
        cell = MxVertexCell()
        return cell

    def is_vertex(self):
        return True


class MxEdgeCell(MxCell):

    def __init__(self):
        super().__init__()
        self.attrs['edge'] = '1'

    @classmethod
    def from_xml(cls, cell_store, xml_element):
        cell = MxEdgeCell()
        source = cell_store[xml_element.get('source')]
        cell.set_source(source)
        target = cell_store[xml_element.get('target')]
        cell.set_target(target)
        # lookup source and target vertex
        return cell

    def is_edge(self):
        return True

    def set_source(self, vertex):
        self.source = vertex
        self.attrs['source'] = vertex['id']

    def set_target(self, vertex):
        self.target = vertex
        self.attrs['target'] = vertex['id']

    def get_source(self):
        return self.source

    def get_target(self):
        return self.target


class MxGraphModel(MxBase):
    pass


class MxGraph:
    def __init__(self):
        pass

    def set_shapes(self, graph_xml):
        # print(dxml.tostring(graph_xml).decode('utf-8'))
        print(graph_xml.items())
        self.cells = [create_mxcell_from_xml(x) for x in graph_xml.findall('root/mxCell')]
        # print(self.cells)
        # for c in self.cells: # print(c)

    def from_file(self, f):
        et = dxml.parse(f)
        root = et.getroot()
        diagram = root.findall("diagram")[0]
        # print(diagram.text)
        # t = urllib.parse.unquote(zlib.decompress(base64.b64decode(diagram.text), -15))
        t = urllib.parse.unquote(zlib.decompress(base64.b64decode(diagram.text), -zlib.MAX_WBITS).decode("utf-8"))
        self.graph_string = t
        self.graph_xml = dxml.fromstring(t)
        self.set_shapes(self.graph_xml)
        # print(self.graph_xml)

    def shapes_to_xml(self):
        pass
        # drawio adds to default parent cells id 0 and 1, 1 having 0 as the parent

    def to_file(self, f):
        # <mxfile host="Electron" modified="2021-03-20T11:18:12.728Z" agent="5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) draw.io/14.1.8 Chrome/87.0.4280.88 Electron/11.1.1 Safari/537.36" etag="kQo77z5om65T-AUhIzrJ" version="14.1.8" type="device"><diagram id="FSWUdnHGcb4EeTo7y5cW" name="Page-1">
        s = dxml.tostring(self.graph_xml)
        co = zlib.compressobj(wbits=-zlib.MAX_WBITS)
        b = co.compress( bytes(urllib.parse.quote(s), 'ascii'))
        b += co.flush(zlib.Z_FINISH)
        s = base64.b64encode(b)
        mxfile = ET.Element('mxfile')
        mxfile.set('host','pymxgraph')
        mxfile.set('type','device')
        diagram = ET.SubElement(mxfile,'diagram')
        diagram.set('id','pymx-0000')
        diagram.set('name','Page-1')
        diagram.text = s.decode('utf-8')
        ET.dump(mxfile)
        # f.write(s)

