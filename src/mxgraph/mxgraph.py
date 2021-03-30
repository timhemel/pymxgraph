

import base64
import urllib.parse
import zlib
import defusedxml.ElementTree as dxml
import xml.etree.ElementTree as ET
from collections.abc import MutableMapping

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
    """Keeps track of cells in a graph. The store will give every edge a unique id."""

    def __init__(self):
        self.current_id = 0
        self.cells = {}
        self.prefix = ''
        self.postfix = ''

    def __make_id(self, n):
        s = ''
        if self.prefix != '':
            s += self.prefix + '-'
        s += str(n)
        if self.postfix != '':
            s += '-' + self.postfix
        return s

    def new_id(self):
        """Return a new identifier that is not used yet."""
        newid = self.__make_id(self.current_id)
        while newid in self.cells:
            self.current_id += 1
            newid = self.__make_id(self.current_id)
        return newid

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
        """Adds the cell cell to the store. It is stored under its cell_id."""
        self.cells[cell.cell_id] = cell



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

    def __init__(self, x=None, y=None, width=None, height=None, relative=False):
        super().__init__()
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.relative = relative
        self.points = []
        self.source_point = None
        self.target_point = None

    @classmethod
    def from_xml(cls, cell_store, xml_element):
        geom = MxGeometry(
                int_or_none(xml_element.get('x')),
                int_or_none(xml_element.get('y')),
                int_or_none(xml_element.get('width')),
                int_or_none(xml_element.get('height')),
                xml_element.get('relative') == '1')
        points = [ MxPoint.from_xml(cell_store, p) for p in xml_element.findall('Array/mxPoint') ]
        geom.points = points
        sp_xml = xml_element.find("mxPoint[@as='sourcePoint']")
        if sp_xml is not None:
            geom.source_point = MxPoint.from_xml(cell_store, sp_xml)
        tp_xml = xml_element.find("mxPoint[@as='targetPoint']")
        if tp_xml is not None:
            geom.target_point = MxPoint.from_xml(cell_store, tp_xml)
        return geom


    def to_xml(self):
        geom = ET.Element('mxGeometry')
        if self.x: geom.set('x', str(self.x))
        if self.y: geom.set('y', str(self.y))
        if self.width: geom.set('width', str(self.width))
        if self.height: geom.set('height', str(self.height))
        if self.relative: geom.set('relative', '1')
        geom.set('as', 'geometry')
        if self.source_point is not None:
            sp_xml = self.source_point.to_xml()
            sp_xml.set('as', 'sourcePoint')
            geom.append(sp_xml)
        if self.target_point is not None:
            sp_xml = self.target_point.to_xml()
            sp_xml.set('as', 'targetPoint')
            geom.append(sp_xml)
        if self.points:
            array = ET.SubElement(geom, 'Array')
            array.set('as','points')
            array.extend([p.to_xml() for p in self.points])
        return geom



    @classmethod
    def old_from_xml(cls, cell_store, xml_element):
        if set(['x','y','width','height']).issubset(xml_element.keys()):
            return MxVertexGeometry.from_xml(cell_store, xml_element)
        else:
            return MxEdgeGeometry.from_xml(cell_store, xml_element)

class MxVertexGeometry(MxGeometry):

    def old__init__(self, x, y, width, height, relative=False):
        super().__init__()
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.relative = relative

    @classmethod
    def old_from_xml(cls, cell_store, xml_element):
        return MxVertexGeometry(
                int_or_none(xml_element.get('x')),
                int_or_none(xml_element.get('y')),
                int_or_none(xml_element.get('width')),
                int_or_none(xml_element.get('height')))

    def old_to_xml(self):
        geom = ET.Element('mxGeometry')
        geom.set('x', str(self.x))
        geom.set('y', str(self.y))
        geom.set('width', str(self.width))
        geom.set('height', str(self.height))
        geom.set('as', 'geometry')
        return geom

class MxEdgeGeometry(MxGeometry):

    def old__init__(self, points):
        super().__init__()
        self.points = points
        self.source_point = None
        self.target_point = None
        self.width = None
        self.height = None

    @classmethod
    def old_from_xml(cls, cell_store, xml_element):
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

    def old_to_xml(self):
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

    def __init__(self, cell_store, cell_id, vertex=False, edge=False, **kwargs):
        super().__init__()
        self.cell_store = cell_store
        self.cell_id = cell_id
        self._parent_id = None
        # self.value = None
        self.geometry = None
        self.style = None
        self.vertex = vertex
        self.edge = edge
        # self.connectable = False
        # self.collapsed = False
        self._source_id = None
        self._target_id = None
        self.attrs.update(kwargs)

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
        if False and xml_element.get('vertex'):
            cell = MxVertexCell.from_xml(cell_store, xml_element)
        elif False and xml_element.get('edge'):
            cell = MxEdgeCell.from_xml(cell_store, xml_element)
        else:
            cell = MxCell(cell_store, xml_element.get('id'))
        cell.cell_id = xml_element.get('id')
        cell._parent_id = xml_element.get('parent')
        cell.attrs = dict(xml_element.items())
        
        if xml_element.get('style') is not None:
            cell.style = MxStyle.from_string(xml_element.get('style'))
        geom = xml_element.find('mxGeometry')
        if geom is not None:
            cell.geometry = MxGeometry.from_xml(cell_store, geom)
        if xml_element.get('source') is not None:
            cell._source_id = xml_element.get('source')
        if xml_element.get('target') is not None:
            cell._target_id = xml_element.get('target')
        cell.vertex = xml_element.get('vertex') == '1'
        cell.edge = xml_element.get('edge') == '1'
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
        if self.style is not None:
            cell_xml.set('style', self.style.to_string())
        if self.source is not None:
            cell_xml.set('source', self.source.cell_id)
        if self.target is not None:
            cell_xml.set('target', self.target.cell_id)
        if self.geometry is not None:
            geom_xml = self.geometry.to_xml()
            cell_xml.append(geom_xml)
        if self.vertex:
            cell_xml.set('vertex', '1')
        if self.edge:
            cell_xml.set('edge', '1')
        return cell_xml

    def is_vertex(self):
        return self.attrs['vertex'] == '1'

    def is_edge(self):
        return self.attrs['edge'] == '1'

    @property
    def source(self):
        if self._source_id is None:
            return None
        return self.cell_store.cells[self._source_id]

    @source.setter
    def source(self, cell):
        self._source_id = cell.cell_id

    @property
    def target(self):
        if self._target_id is None:
            return None
        return self.cell_store.cells[self._target_id]

    @target.setter
    def target(self, cell):
        self._target_id = cell.cell_id


class MxGraphModel(MxBase):
    # https://jgraph.github.io/mxgraph/docs/js-api/files/model/mxGraphModel-js.html

    def __init__(self):
        super().__init__()
        self.cells = CellStore()

    @property
    def prefix(self):
        return self.cells.prefix

    @prefix.setter
    def prefix(self, value):
        self.cells.prefix = value

    @property
    def postfix(self):
        return self.cells.postfix

    @postfix.setter
    def postfix(self, value):
        self.cells.postfix = value

    def add(self, parent, cell):
        """add the cell to the parent."""
        cell.parent = parent
        self.cells.add_cell(cell)

    @classmethod
    def from_xml(cls, xml_element):
        g = MxGraphModel()
        g.attrs = dict(xml_element.items())
        for x in xml_element.findall('root/mxCell'):
            g.cells.add_cell(MxCell.from_xml(g.cells, x))
        return g

    def to_xml(self):
        g_xml = ET.Element('mxGraphModel')
        for k,v in self.attrs.items():
            g_xml.set(k,v)
        root_xml = ET.SubElement(g_xml, 'root')
        root_xml.extend([c.to_xml() for c in self.cells.values()])
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

class MxGraph:
    def __init__(self):
        self.mxgraph_model = MxGraphModel()
        self.cells = self.mxgraph_model.cells
        self.root = MxCell(self.cells, "0")
        self.mxgraph_model.add(None, self.root)

    def _get_parent(self, parent):
        if parent is None:
            return self.root
        return parent

    def _get_cell_id(self, cell_id):
        if cell_id is None:
            return self.cells.new_id()

    def create_group_cell(self, parent = None, cell_id = None):
        parent = self._get_parent(parent)
        cell_id = self._get_cell_id(cell_id)
        cell = MxCell(self.cells, cell_id)
        self.mxgraph_model.add(parent, cell)
        return cell

    def insert_vertex(self, parent = None, cell_id = None, value = None, x = None, y = None, width = None, height = None, style = {}, relative = False):
        """https://jgraph.github.io/mxgraph/docs/js-api/files/view/mxGraph-js.html#mxGraph.insertVertex"""
        parent = self._get_parent(parent)
        cell_id = self._get_cell_id(cell_id)
        cell = MxCell(self.cells, cell_id)
        cell.style = style
        cell.geometry = MxGeometry(x=x, y=y, width=width, height=height, relative=relative)
        self.mxgraph_model.add(parent, cell)
        return cell

    def insert_edge(self, parent=None, cell_id=None, value=None, source=None, target=None, style={}):
        """https://jgraph.github.io/mxgraph/docs/js-api/files/view/mxGraph-js.html#mxGraph.insertEdge"""
        parent = self._get_parent(parent)
        cell_id = self._get_cell_id(cell_id)
        cell = MxCell(self.cells, cell_id)
        if not isinstance(source, MxCell):
            raise Exception("invalid source cell")
        if not isinstance(target, MxCell):
            raise Exception("invalid target cell")
        cell.geometry = MxGeometry(relative=True)
        cell.source = source
        cell.target = target
        cell.style = style
        self.mxgraph_model.add(parent, cell)
        return cell

    def add_edge_geometry(self, edge, points):
        edge.geometry.points = [MxPoint(*p) for p in points]

    def set_source_point(self, edge, point):
        edge.geometry.source_point = MxPoint(*point)

    def set_target_point(self, edge, point):
        edge.geometry.target_point = MxPoint(*point)

