

import base64
import urllib.parse
import zlib
import defusedxml.ElementTree as dxml
import xml.etree.ElementTree as ET

def create_mxcell_from_xml(xml_element):
    c = MxCell()
    c.from_xml(xml_element)
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
        self.cells[cell.cell_id] = cell

    def mxGroupCell(self, parent=None):
        cell_id = self.__new_id()
        cell = MxGroupCell(self, cell_id)
        cell.parent = parent
        self.add_cell(cell)
        return cell

    def mxVertexCell(self, parent=None):
        cell_id = self.__new_id()
        cell = MxVertexCell(self, cell_id)
        cell.parent = parent
        self.add_cell(cell)
        return cell

    def mxEdgeCell(self, parent=None, source=None, target=None):
        cell_id = self.__new_id()
        cell = MxEdgeCell(self, cell_id)
        cell.parent = parent
        cell.source = source
        cell.target = target
        self.add_cell(cell)
        return cell

    def mxStyle(self, **kwargs):
        return MxStyle(**kwargs)

    def mxVertexGeometry(self, x, y, width, height):
        return MxVertexGeometry(x, y, width, height)

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
    def from_xml(cls, cell_store, xml_element):
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

    def __init__(self, cell_store, cell_id):
        self.cell_store = cell_store
        self.cell_id = cell_id
        self._parent_id = None
        super().__init__()

    @property
    def parent(self):
        if self._parent_id is None:
            return None
        return self.cell_store[self._parent_id]

    @parent.setter
    def parent(self, cell):
        if cell is not None:
            self._parent_id = cell.cell_id
        else:
            self._parent_id = None

    @classmethod
    def from_xml(cls, cell_store, xml_element):
        # https://jgraph.github.io/mxgraph/docs/js-api/files/model/mxCell-js.html
        if xml_element.get('vertex'):
            cell = MxVertexCell.from_xml(cell_store, xml_element)
        elif xml_element.get('edge'):
            cell = MxEdgeCell.from_xml(cell_store, xml_element)
        else:
            cell = MxGroupCell.from_xml(cell_store, xml_element)
        cell.cell_id = xml_element.get('id')
        cell._parent_id = xml_element.get('parent')
        # if parent_id:
        #    cell.parent = cell_store[parent_id]
        # else:
        #    cell.parent = None
        # cell.parent = None
        cell.set_attributes_from_xml(cell_store, xml_element)
        cell_store.add_cell(cell)
        return cell

    def set_attributes_from_xml(self, cell_store, xml_element):
        self.attrs = dict(xml_element.items())

    def to_xml(self):
        cell_xml = ET.Element('mxCell')
        for k,v in self.attrs.items():
            cell_xml.set(k,v)
        cell_xml.set('id', self.cell_id)
        if self.parent is not None:
            cell_xml.set('parent', self.parent.cell_id)
        return cell_xml

    def is_vertex(self):
        return False

    def is_edge(self):
        return False

class MxGroupCell(MxCell):

    @classmethod
    def from_xml(cls, cell_store, xml_element):
        cell = MxGroupCell(cell_store, None)
        return cell

class MxNonGroupCell(MxCell):

    def set_attributes_from_xml(self, cell_store, xml_element):
        super().set_attributes_from_xml(cell_store, xml_element)
        self.geometry = MxGeometry.from_xml(cell_store, xml_element.find('mxGeometry'))
        self.style = MxStyle.from_string(self.attrs.get('style',''))

    def to_xml(self):
        cell_xml = super().to_xml()
        cell_xml.set('style', self.style.to_string())
        geom_xml = self.geometry.to_xml()
        cell_xml.append(geom_xml)
        return cell_xml

class MxVertexCell(MxNonGroupCell):

    def __init__(self, cell_store, cell_id):
        super().__init__(cell_store, cell_id)
        self.attrs['vertex'] = '1'

    @classmethod
    def from_xml(cls, cell_store, xml_element):
        cell = MxVertexCell(cell_store, None)
        return cell

    def is_vertex(self):
        return True


class MxEdgeCell(MxNonGroupCell):

    def __init__(self, cell_store, cell_id):
        super().__init__(cell_store, cell_id)
        self.attrs['edge'] = '1'
        self._source_id = None
        self._target_id = None

    @property
    def source(self):
        return self.cell_store.cells[self._source_id]

    @source.setter
    def source(self, cell):
        self._source_id = cell.cell_id

    @property
    def target(self):
        return self.cell_store.cells[self._target_id]

    @target.setter
    def target(self, cell):
        self._target_id = cell.cell_id

    @classmethod
    def from_xml(cls, cell_store, xml_element):
        cell = MxEdgeCell(cell_store, None)
        # source = cell_store[xml_element.get('source')]
        cell._source_id = xml_element.get('source')
        # cell.source = None
        cell._target_id = xml_element.get('target')
        # target = cell_store[xml_element.get('target')]
        # cell.target = None
        return cell

    def to_xml(self):
        cell_xml = super().to_xml()
        cell_xml.set('source', self.source.cell_id)
        cell_xml.set('target', self.target.cell_id)
        return cell_xml

    def is_edge(self):
        return True


class MxGraphModel(MxBase):
    pass


class MxGraph(MxBase):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_xml(cls, cell_store, xml_element):
        g = MxGraph()
        g.attrs = dict(xml_element.items())
        cells = [ MxCell.from_xml(cell_store, x) for x in xml_element.findall('root/mxCell') ]
        return g

    def to_xml(self, cell_store):
        g_xml = ET.Element('mxGraph')
        for k,v in self.attrs.items():
            g_xml.set(k,v)
        root_xml = ET.SubElement(g_xml, 'root')
        root_xml.extend([c.to_xml() for c in cell_store.cells.values()])
        return g_xml

class MxDiagram(MxBase):

    @classmethod
    def from_xml(cls, xml_element):
        diagram = MxDiagram()
        diagram.attrs.update(dict(xml_element.items()))

        t = urllib.parse.unquote(zlib.decompress(base64.b64decode(xml_element.text), -zlib.MAX_WBITS).decode("utf-8"))
        graph_string = t
        graph_xml = dxml.fromstring(t)

        diagram.cell_store = CellStore()
        diagram.mxgraph = MxGraph.from_xml(diagram.cell_store, graph_xml)
        return diagram


class MxFile(MxBase):

    @classmethod
    def from_file(cls, f):
        mxfile = MxFile()
        et = dxml.parse(f)
        root = et.getroot()
        mxfile.attrs.update(dict(root.items()))   # TODO: dict mixin
        diagram = MxDiagram.from_xml(root.find("diagram"))
        return mxfile

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

