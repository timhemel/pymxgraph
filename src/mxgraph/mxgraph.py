

import base64
import urllib.parse
import zlib
import defusedxml.ElementTree as dxml
import xml.etree.ElementTree as ET
from collections.abc import MutableMapping

def create_mxcell_from_xml(xml_element):
    c = MxCell()
    c.from_xml(xml_element)
    return c

def int_or_none(a):
    if a is None:
        return a
    return int(a)


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

class CellStore(MutableMapping):

    def __init__(self):
        self.current_id = 0
        self.cells = {}

    def __new_id(self):
        while str(self.current_id) in self.cells:
            self.current_id += 1
        return str(self.current_id)

    def __getitem__(self, key):
        return self.cells[key]

    def __setitem__(self, key, value):
        self.cells[key] = value

    def __delitem__(self, key):
        del self.cells[key]

    def __iter__(self):
        return iter(self.cells)

    def __len__(self):
        return len(self.cells)

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


class MxBase(MutableMapping):

    def __init__(self):
        self.attrs = {}

    def __getitem__(self, key):
        return self.attrs[key]

    def __setitem__(self, key, value):
        self.attrs[key] = value

    def __delitem__(self, key):
        del self.attrs[key]

    def __iter__(self):
        return iter(self.attrs)

    def __len__(self):
        return len(self.attrs)


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

class MxPoint(MxBase):

    def __init__(self, x,y):
        super().__init__()
        self.x = x
        self.y = y

    @classmethod
    def from_xml(cls, cell_store, xml_element):
        x = int(xml_element.get('x'))
        y = int(xml_element.get('y'))
        point = MxPoint(x,y)
        point.attrs.update(xml_element.items())
        return point

    def to_xml(self):
        point_xml = ET.Element('mxPoint')
        point_xml.set('x', str(self.x))
        point_xml.set('y', str(self.y))
        return point_xml

class MxGeometry(MxBase):
    # https://jgraph.github.io/mxgraph/docs/js-api/files/model/mxGeometry-js.html

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
                int_or_none(xml_element.get('x')),
                int_or_none(xml_element.get('y')),
                int_or_none(xml_element.get('width')),
                int_or_none(xml_element.get('height')))

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
        self.source_point = None
        self.target_point = None
        self.width = None
        self.height = None

    @classmethod
    def from_xml(cls, cell_store, xml_element):
        points = [ MxPoint.from_xml(cell_store, p) for p in xml_element.findall('Array/mxPoint') ]
        geom = MxEdgeGeometry(points)
        geom.width = int_or_none(xml_element.get('width'))
        geom.height = int_or_none(xml_element.get('height'))
        sp_xml = xml_element.find("mxPoint[@as='sourcePoint']")
        if sp_xml is not None:
            geom.source_point = MxPoint.from_xml(cell_store, sp_xml)
        tp_xml = xml_element.find("mxPoint[@as='targetPoint']")
        if tp_xml is not None:
            geom.target_point = MxPoint.from_xml(cell_store, tp_xml)
        return geom

    def to_xml(self):
        geom = ET.Element('mxGeometry')
        if self.width is not None:
            geom.set('width', str(self.width))
        if self.height is not None:
            geom.set('height', str(self.height))
        geom.set('relative', '1')
        geom.set('as', 'geometry')
        if self.source_point is not None:
            sp_xml = self.source_point.to_xml()
            sp_xml.set('as', 'sourcePoint')
            geom.append(sp_xml)
        if self.target_point is not None:
            sp_xml = self.target_point.to_xml()
            sp_xml.set('as', 'targetPoint')
            geom.append(sp_xml)
        array = ET.SubElement(geom, 'Array')
        array.set('as','points')
        array.extend([p.to_xml() for p in self.points])
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
        cell.set_attributes_from_xml(cell_store, xml_element)
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
        self.style = MxStyle.from_string(self.attrs.get('style',''))

    def to_xml(self):
        cell_xml = super().to_xml()
        cell_xml.set('style', self.style.to_string())
        return cell_xml

class MxVertexCell(MxNonGroupCell):

    def __init__(self, cell_store, cell_id):
        super().__init__(cell_store, cell_id)
        self.attrs['vertex'] = '1'

    @classmethod
    def from_xml(cls, cell_store, xml_element):
        cell = MxVertexCell(cell_store, None)
        return cell

    def to_xml(self):
        cell_xml = super().to_xml()
        geom_xml = self.geometry.to_xml()
        cell_xml.append(geom_xml)
        return cell_xml

    def set_attributes_from_xml(self, cell_store, xml_element):
        super().set_attributes_from_xml(cell_store, xml_element)
        self.geometry = MxVertexGeometry.from_xml(cell_store, xml_element.find('mxGeometry'))

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
        cell._source_id = xml_element.get('source')
        cell._target_id = xml_element.get('target')
        return cell

    def to_xml(self):
        cell_xml = super().to_xml()
        cell_xml.set('source', self.source.cell_id)
        cell_xml.set('target', self.target.cell_id)
        geom_xml = self.geometry.to_xml()
        cell_xml.append(geom_xml)
        return cell_xml

    def set_attributes_from_xml(self, cell_store, xml_element):
        super().set_attributes_from_xml(cell_store, xml_element)
        self.geometry = MxEdgeGeometry.from_xml(cell_store, xml_element.find('mxGeometry'))

    def is_edge(self):
        return True


class MxGraphModel(MxBase):
    # https://jgraph.github.io/mxgraph/docs/js-api/files/model/mxGraphModel-js.html

    def __init__(self):
        super().__init__()
        self.cells = CellStore()

    @classmethod
    def from_xml(cls, xml_element):
        g = MxGraphModel()
        g.attrs = dict(xml_element.items())
        for x in xml_element.findall('root/mxCell'):
            g.cells.add_cell(MxCell.from_xml(g.cells, x))
        return g

    def to_xml(self, cell_store):
        g_xml = ET.Element('mxGraphModel')
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

        diagram.mxgraph_model = MxGraphModel.from_xml(graph_xml)
        return diagram

    def to_xml(self):
        diagram_xml = ET.Element('diagram')
        for k,v in self.attrs.items():
            diagram_xml.set(k, v)
        graph_xml = self.mxgraph_model.to_xml(self.cell_store)
        s = dxml.tostring(graph_xml)
        co = zlib.compressobj(wbits=-zlib.MAX_WBITS)
        b = co.compress( bytes(urllib.parse.quote(s), 'ascii'))
        b += co.flush(zlib.Z_FINISH)
        s = base64.b64encode(b)
        diagram_xml.text = s.decode('utf-8')
        return diagram_xml


class MxFile(MxBase):

    @classmethod
    def from_file(cls, f):
        mxfile = MxFile()
        et = dxml.parse(f)
        root = et.getroot()
        mxfile.attrs.update(root.items())   # TODO: dict mixin
        mxfile.diagram = MxDiagram.from_xml(root.find("diagram"))
        return mxfile

    def to_file(self, f):
        # <mxfile host="Electron" modified="2021-03-20T11:18:12.728Z" agent="5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) draw.io/14.1.8 Chrome/87.0.4280.88 Electron/11.1.1 Safari/537.36" etag="kQo77z5om65T-AUhIzrJ" version="14.1.8" type="device"><diagram id="FSWUdnHGcb4EeTo7y5cW" name="Page-1">
        diagram_xml = self.diagram.to_xml()
        mxfile_xml = ET.Element('mxfile')
        for k,v in self.attrs.items():
            mxfile_xml.set(k, v)
        mxfile_xml.append(diagram_xml)
        ET.dump(mxfile_xml)
        # f.write(s)

