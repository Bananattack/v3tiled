import datastream
import struct
import base64
import zlib
import os.path
import xml.dom.minidom
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
from xml.etree import cElementTree as etree

class FormatException(Exception):
    pass

def getNodeName(node):
    if hasattr(node, 'tag'):
        return '<' + node.tag + '>'
    if type(node) == dict:
        return node.get('_node', '?')
    return '?'

def getIntegerNode(node, attr, default=None):
    if node.get(attr) is not None: 
        try:
            return int(node.get(attr))
        except:
            raise FormatException('Attribute \'' + attr + '\' on ' + getNodeName(node) + ' is not an integer.')
    elif default is not None:
        return default
    else:
        raise FormatException('Required attribute \'' + attr + '\' on ' + getNodeName(node) + ' is missing.')
        
def getNumericNode(node, attr, default=None):
    if node.get(attr) is not None: 
        try:
            return float(node.get(attr))
        except:
            raise FormatException('Attribute \'' + attr + '\' on ' + getNodeName(node) + ' is not a number.')
    elif default is not None:
        return default
    else:
        raise FormatException('Required attribute \'' + attr + '\' on ' + getNodeName(node) + ' is missing.')

def getProperties(elem):
    props = elem.find('properties')
    if not props:
        return {}
    else:
        d = {}
        d['_node'] = '<properties>'
        for prop in props.iter('property'):
            if prop.get('name'):
                d[prop.get('name')] = prop.get('value')
        return d


ANIMATION_MODE = {
    '0': 'forward',
    '1': 'reverse',
    '2': 'random',
    '3': 'ping_pong',
}

ANIMATION_MODE_OUT = dict((v, int(k)) for k, v in ANIMATION_MODE.iteritems())
    
class Animation(object):
    def __init__(self, **kwargs):
        self.id = -1
        self.name = kwargs.get('name', '')
        self.start = kwargs.get('start', -1)
        self.end = kwargs.get('end', -1)
        self.delay = kwargs.get('delay', -1)
        self.mode = kwargs.get('mode', 'forward')
    
    def readFromVSP(self, f):
        self.name = f.readFixedString(256)
        self.start = f.readInt()
        self.end = f.readInt()
        self.delay = f.readInt()
        self.mode = ANIMATION_MODE.get(f.readInt(), 'forward')
        
    def writeToVSP(self, f):
        f.writeFixedString(self.name, 256)
        f.writeInt(self.start)
        f.writeInt(self.end)
        f.writeInt(self.delay)
        f.writeInt(ANIMATION_MODE_OUT.get(self.mode, 0))
        


VSP_SIGNATURE = 5264214
VSP_VERSION = 6
VSP_FORMAT = 1
VSP_COMPRESSION = 1
VSP_TILESIZE  = 16
    
class VSP(object):
    def __init__(self):
        pass
        
    def loadVSPFile(self, filename):
        self.filename = filename
        try:
            f = datastream.DataInputStream(file(filename, 'rb'))
        except IOError:
            raise FormatException('VSP file \'' + filename + '\' was not found.')
        
        signature = f.readInt()
        version = f.readInt()
        
        if signature != VSP_SIGNATURE:
            raise FormatException('VSP has a bad signature of ' + signature)
        if version != VSP_VERSION:
            raise FormatException('VSP has a bad version of ' + str(version))
            
        tilesize = f.readInt()
        format = f.readInt()
        self.tileCount = f.readInt()
        compression = f.readInt()
        
        self.tileset = []
        
        self.tilePixels = f.readCompressed()
        self.tileImageName = '.tile.png'
        self.tileLastGID = ((self.tileCount + 19) // 20) * 20
            
        self.animation = []
        animationCount = f.readInt()
        for i in range(animationCount):
            anim = Animation()
            anim.id = i
            anim.readFromVSP(f)
            self.animation.append(anim)
        
        self.obs = []
        self.obsCount = f.readInt()
        self.obsImageName = '.obs.png' 
        self.obsPixels = f.readCompressed()
        self.obsLastGID = ((self.obsCount + 19) // 20) * 20 + self.tileLastGID + 1

        f.close()
        
    def saveVSPFile(self, filename):
        self.filename = filename
        try:
            f = datastream.DataOutputStream(file(filename, 'wb'))
        except IOError:
            raise FormatException('The VSP file \'' + filename + '\' could not be opened for writing!')
        f.writeInt(VSP_SIGNATURE)
        f.writeInt(VSP_VERSION)
        f.writeInt(16) # tilesize
        f.writeInt(1) # format
        f.writeInt(self.tileCount)
        f.writeInt(1) # compression
        f.writeCompressed(struct.pack('<' + str(self.tileCount * 16 * 16 * 3) + 'B', *self.tilePixels))
        f.writeInt(len(self.animation))
        for anim in self.animation:
            anim.writeToVSP(f)
        self.obs = []
        f.writeInt(self.obsCount)
        f.writeCompressed(struct.pack('<' + str(self.obsCount * 16 * 16) + 'B', *self.obsPixels))
        f.close()
        
        
    def dumpTiles(self):
        pixels = self.tilePixels
        tileImage = PIL.Image.new('RGBA', (20 * 16, (self.tileCount // 20 + 1) * 16))
        
        image = tileImage.load()
        for tile in range(self.tileCount):
            y, x = tile // 20 * 16, tile % 20 * 16
            for i in range(16 * 16):
                idx = tile * 16 * 16 + i
                r, g, b = struct.unpack('<BBB', pixels[idx * 3 : idx * 3 + 3])
                a = 255
                if r == 255 and g == 0 and b == 255:
                    a = 0
                image[x + i % 16, y + i / 16] = (r, g, b, a)
        tileImage.save(self.filename + self.tileImageName, 'PNG')
        print('    Saved to \'' + self.filename + self.tileImageName + '\'.')
        
    def dumpObs(self):
        pixels = self.obsPixels
        obsImage = PIL.Image.new('RGBA', (20 * 16, (self.obsCount // 20 + 1) * 16))
        
        image = obsImage.load()
        for tile in range(self.obsCount):
            y, x = tile // 20 * 16, tile % 20 * 16
            for i in range(16 * 16):
                idx = tile * 16 * 16 + i
                pixel, = struct.unpack('<B', pixels[idx])
                pixel = pixel and (255, 255, 255, 127) or (0, 0, 0, 0)
                image[x + i % 16, y + i / 16] = pixel
        obsImage.save(self.filename + self.obsImageName, 'PNG')
        print('    Saved to \'' + self.filename + self.obsImageName + '\'.')
        
    def toAnimDocument(self):
        animations = etree.Element('animations')
        for anim in self.animation:
            node = etree.SubElement(animations, 'animation')
            node.set('name', str(anim.name))
            node.set('tile_begin', str(anim.start))
            node.set('tile_end', str(anim.end))
            node.set('tile_end', str(anim.delay))
            node.setAttribute('mode', str(anim.mode))
        tree = etree.ElementTree(root)
        return tree

    def buildFromExternal(self, tileFile, obsFile, animFile=None):
        try:
            img = PIL.Image.open(tileFile)
        except:
            raise FormatException('Failure attempting to load ' + filename + '.')
        w, h = img.size
        if w % 16 or h % 16:
            raise FormatException('The tile image file \'' + tileFile + '\' has invalid size ' + str(w) + 'x' + str(h) + '! Must be multiples of 16 in size.')
        pixels = img.load() 
        self.tileCount = (w // 16) * (h // 16)
        tilePixels = []
        for t in range(self.tileCount): 
            x = t * 16 % w
            y = t * 16 // w * 16
            for j in range(16):
                for i in range(16):
                    p = pixels[x + i, y + j]
                    if p[3] < 255:
                        tilePixels.append(255)
                        tilePixels.append(0)
                        tilePixels.append(255)
                    else:
                        tilePixels.append(p[0])
                        tilePixels.append(p[1])
                        tilePixels.append(p[2])
        self.tilePixels = tilePixels
        
        try:
            img = PIL.Image.open(obsFile)
        except:
            raise FormatException('Failure attempting to load ' + filename + '.')
        w, h = img.size
        if w % 16 or h % 16:
            raise FormatException('The obstruction image file \'' + obsFile + '\' has invalid size ' + str(w) + 'x' + str(h) + '! Must be multiples of 16 in size.')
        pixels = img.load() 
        self.obsCount = (w // 16) * (h // 16)
        obsPixels = []
        for t in range(self.obsCount): 
            x = t * 16 % w
            y = t * 16 // w * 16
            for j in range(16):
                for i in range(16):
                    obsPixels.append((pixels[x + i, y + j][3] != 0) and 1 or 0)
        self.obsPixels = obsPixels
        
        self.animation = []
        if animFile:
            try:
                animations = etree.parse(animFile).getroot()
            except:
                raise FormatException('Failure attempting to parse ' + filename + '.')
            i = 0
            
            try:
                for node in animations.iter('animation'):
                    delay = getIntegerNode(node, 'delay')
                    start = getIntegerNode(node, 'tile_begin')
                    end = getIntegerNode(node, 'tile_end')
                    mode = node.get('mode', 'forward')
                    name = node.get('name', '')
                    
                    anim = Animation(delay = delay, start = start, end = end, mode = mode, name = name)
                    anim.id = i
                    self.animation.append(anim)
                    i += 1
            except FormatException as e:
                raise FormatException('Animation file \'' + str(animFile) + '\' contains an invalid animation: ' + str(e))

class Layer(object):
    def __init__(self):
        self.id = -1
        
    def readFromMap(self, f):
        self.name = f.readFixedString(256)
        self.parallaxX = f.readDouble()
        self.parallaxY = f.readDouble()
        self.width = f.readShort()
        self.height = f.readShort()
        self.data = [0] * (self.width * self.height)
        self.alpha = 1 - float(f.readUnsignedByte()) / 100.0
        
        layerdata = f.readCompressed()
        for i in range(len(layerdata) / 2):
            self.data[i], = struct.unpack('<H', layerdata[i * 2 : i * 2 + 2])
            
    def writeToMap(self, f):
        f.writeFixedString(self.name, 256)
        f.writeDouble(self.parallaxX)
        f.writeDouble(self.parallaxY)
        f.writeShort(self.width)
        f.writeShort(self.height)
        f.writeUnsignedByte(100 - int(self.alpha * 100.0 + 0.5))
        f.writeCompressed(struct.pack('<' + str(self.width * self.height) + 'H', *self.data))

    def convertFromTiled(self, node):
        self.name = node.get('name', '')
        self.width = getIntegerNode(node, 'width')
        self.height = getIntegerNode(node, 'height')
        self.alpha = getNumericNode(node, 'opacity', 1.0)
        props = getProperties(node)
        self.id = getIntegerNode(props, 'id')
        self.parallaxX = getNumericNode(props, 'parallax_x', 1.0)
        self.parallaxY = getNumericNode(props, 'parallax_y', 1.0)
        data = node.find('data')
        if data != None:
            if data.get('encoding') or data.get('compression'):
                if data.get('encoding') == 'base64' and data.get('compression') == 'zlib':
                    # Convert base64'd zlib'd chunk of 32-bit integers into a list of ints [max(N - 1, 0)...].
                    self.data = [max(t - 1, 0) for t in struct.unpack('<' + str(self.width * self.height) + 'i', zlib.decompress(base64.b64decode(str(data.text))))]
                else:
                    raise FormatException('Cannot parse layers with ' + str(data.get('encoding')) + ' encoding and ' + str(data.get('compression')) + ' compression.')
            else:
                # Convert <tile gid='N'/>... into a list of ints [max(N - 1, 0)...].
                self.data = [max(int(t.get('gid', '1')) - 1, 0) for t in data.iter('tile')]
                if len(self.data) != self.width * self.height:
                    raise FormatException('Layer does not contain exactly ' + str(self.width * self.height) + ' tiles in a layer that is ' + str(self.width) + 'x' + str(self.height) + ' in size.')
        else:
            raise FormatException('Mising <data> tag.')

class Zone(object):
    def __init__(self):
        self.id = -1
        self.name = ''
        self.activationEvent = ''
        self.chance = 255
        self.delay = 0
        self.method = 1
    
    def readFromMap(self, f):
        self.name = f.readFixedString(256)
        self.activationEvent = f.readFixedString(256)
        self.chance = f.readUnsignedByte()
        self.delay = f.readUnsignedByte()
        self.method = f.readUnsignedByte()
        
    def writeToMap(self, f):
        f.writeFixedString(self.name, 256)
        f.writeFixedString(self.activationEvent, 256)
        f.writeUnsignedByte(self.chance)
        f.writeUnsignedByte(self.delay)
        f.writeUnsignedByte(self.method)
        
    def convertFromTiled(self, node):
        props = getProperties(node)
        self.name = props.get('name', '')
        self.activationEvent = props.get('activation_event', '')
        self.chance = getIntegerNode(props, 'activation_chance', 255)
        self.delay = getIntegerNode(props, 'activation_delay', 0)
        self.method = props.get('allow_adjacent') == 'true' and 1 or 0


ENTITY_DIR = {
    '0': 'north',
    '1': 'south',
    '2': 'west',
    '3': 'east',
    '4': 'north_west',
    '5': 'north_east',
    '6': 'south_west',
    '7': 'south_east',
}

ENTITY_DIR_OUT = dict((v, int(k)) for k, v in ENTITY_DIR.iteritems())

ENTITY_MOVEMENT = {
    '0': 'none',
    '1': 'wander_zone',
    '2': 'wander_rect',
    '3': 'script',
}

ENTITY_MOVEMENT_OUT = dict((v, int(k)) for k, v in ENTITY_MOVEMENT.iteritems())

class Entity(object):
    def __init__(self):
        self.id = -1
        
    def readFromMap(self, f):
        self.x = f.readShort()
        self.y = f.readShort()
        self.direction = ENTITY_DIR.get(f.readByte(), 'south')
        self.isObstructable = f.readByte()
        self.isObstruction = f.readByte()
        self.autoface = f.readByte()
        self.speed = f.readShort()
        crap = f.readByte() # unused activation mode
        self.movementMode = ENTITY_MOVEMENT.get(str(f.readByte()), 'none')        
        self.wanderX1 = f.readShort() 
        self.wanderY1 = f.readShort()
        self.wanderX2 = f.readShort() 
        self.wanderY2 = f.readShort()
        self.wanderDelay = f.readShort()
        crap = f.readInt() # unused 'expand' flag
        self.movescript = f.readFixedString(256)
        self.filename = f.readFixedString(256)
        self.description = f.readFixedString(256)
        self.activationEvent = f.readFixedString(256)
        
    def writeToMap(self, f):
        f.writeShort(self.x)
        f.writeShort(self.y)
        f.writeByte(ENTITY_DIR_OUT[self.direction])
        f.writeByte(self.isObstructable)
        f.writeByte(self.isObstruction)
        f.writeByte(self.autoface)
        f.writeShort(self.speed)
        f.writeByte(0) # unused activation mode
        f.writeByte(ENTITY_MOVEMENT_OUT[self.movementMode])
        f.writeShort(self.wanderX1)
        f.writeShort(self.wanderY1)
        f.writeShort(self.wanderX2)
        f.writeShort(self.wanderY2)
        f.writeShort(self.wanderDelay)
        f.writeInt(0) # unused expand flag
        f.writeFixedString(self.movescript, 256)
        f.writeFixedString(self.filename, 256)
        f.writeFixedString(self.description, 256)
        f.writeFixedString(self.activationEvent, 256)
        
    def convertFromTiled(self, node):
        self.x = getIntegerNode(node, 'x') // VSP_TILESIZE
        self.y = getIntegerNode(node, 'y') // VSP_TILESIZE
        self.description = node.get('name')
        props = getProperties(node)
        self.id = getIntegerNode(props, 'id')
        self.filename = props.get('filename', '')
        self.activationEvent = props.get('activation_event', '')
        self.direction = props.get('direction', 'south')
        if self.direction not in ENTITY_DIR_OUT:
            raise FormatException('Invalid direction ' + repr(self.direction) + '.')
        self.isObstructable = props.get('is_obstructable') == 'true' and 1 or 0
        self.isObstruction = props.get('is_obstruction') == 'true' and 1 or 0
        self.autoface = props.get('autoface') == 'true' and 1 or 0
        self.speed = getIntegerNode(props, 'speed', 100)
        self.movementMode = props.get('movement_mode', 'none')
        if self.movementMode not in ENTITY_MOVEMENT_OUT:
            raise FormatException('Invalid movement mode ' + repr(self.movementMode) + '.')
        self.wanderX1 = getIntegerNode(props, 'wander_x1', 0)
        self.wanderY1 = getIntegerNode(props, 'wander_y1', 0)
        self.wanderX2 = getIntegerNode(props, 'wander_x2', 0)
        self.wanderY2 = getIntegerNode(props, 'wander_y2', 0)
        self.wanderDelay = getIntegerNode(props, 'wander_delay', 0)
        self.movescript = props.get('movescript', '')



MAP_SIGNATURE = 'V3MAP\0'
MAP_VERSION = 2
        
class Map(object):
    def __init__(self):
        pass
        
    def dumpZoneDummyImage(self):
        font = PIL.ImageFont.load_default()
        zoneCount = len(self.zone)
        image = PIL.Image.new('RGBA', (20 * 16, ((zoneCount + 19) // 20) * 16))
        draw = PIL.ImageDraw.Draw(image)
        bg = (127, 0, 127, 127)
        textColor = (255, 255, 255, 255)
        for i in range(1, zoneCount):
            x, y = i % 20 * 16, i / 20 * 16
            draw.rectangle((x, y, x + 15, y + 15), fill = bg)
            draw.text((x, y), str(i), font = font, fill = textColor)
        image.save(self.zoneDummyFilename, 'PNG')
        print('    Saved to \'' + self.zoneDummyFilename + '\'.')
        
    def loadMapFile(self, filename):
        self.filename = filename
        self.zoneDummyFilename = filename + '.zone.png'
        try:
            f = datastream.DataInputStream(file(filename, 'rb'))
        except IOError:
            raise FormatException('The MAP file \'' + filename + '\' was not found.')

        # Header stuff!
        signature = f.read(len(MAP_SIGNATURE))
        version = f.readInt()

        # Verify the map has the right signature
        if signature != MAP_SIGNATURE:
            raise FormatException('The MAP file \'' + filename + '\' has a bad signature of ' + signature)
        # Verify the map is the right version
        if version != MAP_VERSION:
            raise FormatException('The MAP file \'' + filename + '\' has a bad version of ' + str(version))

        # Skip vc offset.
        version = f.readInt()

        # String data of various use.
        self.mapName = f.readFixedString(256)
        self.vspFilename = f.readFixedString(256)
        self.vsp = VSP()
        self.vsp.loadVSPFile(os.path.dirname(self.filename) + '/' + self.vspFilename)
        self.musicFilename = f.readFixedString(256)
        self.renderOrder = f.readFixedString(256).split(',')
        self.renderItem = {}
        self.startEvent = f.readFixedString(256)

        # Starting location. If not specificied in script, use the map's default.
        self.startX = f.readUnsignedShort()
        self.startY = f.readUnsignedShort()

        # Layers!
        layerCount = f.readInt()
        self.layer = []
        for i in range(layerCount):
            layer = Layer()
            layer.id = i
            layer.readFromMap(f)
            self.layer.append(layer)
            self.renderItem[str(layer.id + 1)] = layer
        self.width = self.layer[0].width
        self.height = self.layer[0].height
        self.obsLayer = [i for i in struct.unpack('<' + str(self.width * self.height) + 'B', f.readCompressed())]
        self.zoneLayer = [i for i in struct.unpack('<' + str(self.width * self.height) + 'H', f.readCompressed())]

        # Zone info!
        self.zone = []
        for i in range(f.readInt()):
            zone = Zone()
            zone.id = i
            zone.readFromMap(f)
            self.zone.append(zone)

        # Entities!
        self.entity = []
        for i in range(f.readInt()):
            ent = Entity()
            ent.id = i
            ent.readFromMap(f)
            self.entity.append(ent)
            
        # We're done with the map file
        f.close()

    def saveMapFile(self, filename, vspFilename):
        try:
            f = datastream.DataOutputStream(file(filename, 'wb'))
        except IOError:
            raise FormatException('The MAP file \'' + filename + '\' could not be opened for writing.')

        f.write(MAP_SIGNATURE)
        f.writeInt(MAP_VERSION)
        
        # Write a dummy offset for now, but this needs to be backpatched, once the real map is completed.
        vc = f.tell()
        f.writeInt(0)
        
        # The usual crap.
        f.writeFixedString(self.mapName, 256)
        f.writeFixedString(vspFilename, 256)
        f.writeFixedString(self.musicFilename, 256)
        f.writeFixedString(','.join(self.renderOrder), 256)
        f.writeFixedString(self.startEvent, 256)
        f.writeUnsignedShort(self.startX)
        f.writeUnsignedShort(self.startY)
        f.writeInt(len(self.layer))
        for lay in self.layer:
            lay.writeToMap(f)
        f.writeCompressed(struct.pack('<' + str(self.width * self.height) + 'b', *self.obsLayer))
        f.writeCompressed(struct.pack('<' + str(self.width * self.height) + 'H', *self.zoneLayer))
        f.writeInt(len(self.zone))
        for z in self.zone:
            z.writeToMap(f)
        f.writeInt(len(self.entity))
        for ent in self.entity:
            ent.writeToMap(f)

        # Write the vc offset.
        end = f.tell()
        f.seek(vc)
        f.writeInt(end)
        f.close()
        
    def convertFromTiled(self, filename):
        self.zoneDummyFilename = filename + '.zone.png'
        try:
            tree = etree.parse(filename)
        except:
            raise FormatException('Failure attempting to parse ' + filename + '.')
        map = tree.getroot()
        if map.get('version') != '1.0':
            raise FormatException('Unsupported version ' + map.get('version') + '. This only supports tiled 1.0 maps.')
        if map.get('orientation') != 'orthogonal':
            raise FormatException('Uses unsupported orientation \'' + map.get('orientation') + '\'. Only orthogonal maps are allowed.')
        if map.get('tilewidth') != '16' or map.get('tileheight') != '16':
            raise FormatException('Unsupported map tile size ' + str(map.get('tilewidth')) + 'x' + str(map.get('tileheight')) + '. Only 16x16 is supported.') 
        
        props = getProperties(map)
        print('    Importing properties...')
        try:
            self.mapName = props.get('title', os.path.splitext(filename)[0])
            self.musicFilename = props.get('music', '')
            self.startEvent = props.get('start_event', '')
            self.startX = getIntegerNode(props, 'start_x', 0)
            self.startY = getIntegerNode(props, 'start_y', 0)
        except FormatException as e:
            raise FormatException('Bad map property: ' + str(e)) 
        
        print('    Importing tileset references...')
        hasTiles = False
        hasObs = False
        obsGID = 0
        hasZones = False
        zoneGID = 0
        zoneData = {}
        for tileset in map.iter('tileset'):
            if tileset.get('tilewidth') != '16' or tileset.get('tileheight') != '16':
                raise FormatException('Unsupported tile size ' + str(map.get('tilewidth')) + 'x' + str(map.get('tileheight')) + ' on tileset ' + repr(tileset.get('name')) + '. Only 16x16 is supported.')

            if tileset.get('name') == 'tiles':
                if hasTiles:
                    raise FormatException('This file has more than one \'tiles\' <tileset>.') 
                hasTiles = True
            elif tileset.get('name') == 'obstructions':
                if hasObs:
                    raise FormatException('This file has more than one \'obstructions\' <tileset>.') 
                obsGID = getIntegerNode(tileset, 'firstgid')
                hasObs = True
            elif tileset.get('name') == 'zones':
                if hasZones:
                    raise FormatException('This file has more than one \'zones\' <tileset>.')
                zoneGID = getIntegerNode(tileset, 'firstgid')
                for tile in tileset.iter('tile'):
                    if tile.get('id'):
                        try:
                            zone = Zone()
                            zone.convertFromTiled(tile)
                            zoneData[tile.get('id')] = zone
                        except FormatException as e:
                            raise FormatException('Invalid zone with id=' + repr(tile.get('id')) + ': ' + str(e))
                    else:
                        raise FormatException('There is a <tile> in the \'zones\' <tileset> without an id.')
                hasZones = True
            else:
                raise FormatException('Tileset ' + repr(tileset.get('name')) + ' that cannot be exported. Must be named \'tiles\', \'obstructions\' or \'zones\'') 
        if not hasTiles:
            raise FormatException('Missing a \'tiles\' tileset.')
            
        # Now convert a sparse map of id -> zone into a list of zones with a size of max id.
        self.zone = [None] * max(int(id) + 1 for id, zone in zoneData.iteritems())
        for id, zone in zoneData.iteritems():
            self.zone[int(id)] = zone
        # Fill any gaps with default zones:
        for i in range(len(self.zone)):
            self.zone[i] = self.zone[i] or Zone()
            self.zone[i].id = i
            
        self.renderOrder = []
        self.renderItem = {}

        print('    Layers, retrace and entities...')
        layerData = {}
        # First pass, renderables.
        for layer in map.iter():
            if layer.tag == 'objectgroup':
                if layer.get('name') == 'Entities':
                    entData = {}
                    self.renderOrder.append('E')
                    for ob in layer.iter('object'):
                        try:
                            ent = Entity()
                            ent.convertFromTiled(ob)
                            entData[ent.id] = ent
                        except FormatException as e:
                            raise FormatException('Invalid entity with name=' + repr(ob.get('name')) + ': ' + str(e))                    

                    self.entity = [None] * max(int(id) + 1 for id, ent in entData.iteritems())
                    for id, ent in entData.iteritems():
                        self.entity[int(id)] = ent
                    # Error if there are any gaps in the list.
                    for i in range(len(self.entity)):
                        if not self.entity[i]:
                            raise FormatException('Invalid map. All entities must have a id property, and these must be consecutive (no gaps). '
                                                + 'Expected entity with id of ' + str(i) + '. '
                                                + 'Maximum id was determined to be ' + str(len(self.entity) - 1) + ', so there should id from 0 up to and including '
                                                + str(len(self.entity) - 1) + '.')
                elif layer.get('name') == 'Retrace':
                    self.renderOrder.append('R')
                else:
                    raise FormatException('Object layer ' + repr(tileset.get('name')) + ' cannot be exported. Must be named \'Retrace\' or \'Entities\'') 
            if layer.tag == 'layer':        
                if layer.get('name') != 'Obstructions' and layer.get('name') != 'Zones':
                    lay = Layer()
                    try:
                        lay.convertFromTiled(layer)
                    except FormatException as e:
                        raise FormatException('Invalid layer with name=\'' + layer.get('name') + '\': ' + str(e))
                    layerData[lay.id] = lay
                    self.renderOrder.append(str(lay.id + 1))
                    self.renderItem[lay.id + 1] = lay

        # Now convert a sparse map of id -> zone into a list of layers with a size of max id.
        self.layer = [None] * max(int(id) + 1 for id, lay in layerData.iteritems())
        if not len(self.layer):
            raise FormatException('Invalid map. Must contain at least one layer.')
        for id, lay in layerData.iteritems():
            self.layer[int(id)] = lay
        # Error if there are any gaps in the list.
        for i in range(len(self.layer)):
            if not self.layer[i]:
                raise FormatException('Invalid map. All layers must have a id property, and these must be consecutive (no gaps). '
                    + 'Expected layer with id of ' + str(i) + '. '
                    + 'Maximum id was determined to be ' + str(len(self.layer) - 1) + ', so there should id from 0 up to and including '
                    + str(len(self.layer) - 1) + '.')

        self.width = self.layer[0].width
        self.height = self.layer[0].height

        print('    Zones and obstructions...')
        # Second pass: obstructions and zones.
        for layer in map.iter('layer'):
            if layer.get('name') == 'Obstructions':
                if not hasObs:
                    raise FormatException('This map has an \'Obstructions\' layer but is missing the \'obstructions\' tileset.')
                data = layer.find('data')
                if data != None:
                    if data.get('encoding') or data.get('compression'):
                        if data.get('encoding') == 'base64' and data.get('compression') == 'zlib':
                            # Convert base64'd zlib'd chunk of 32-bit integers into a list of obs
                            self.obsLayer = [t - obsGID for t in struct.unpack('<' + str(self.width * self.height) + 'i', zlib.decompress(base64.b64decode(str(data.text))))]
                        else:
                            raise FormatException('Cannot parse Obstructions layer with ' + str(data.get('encoding')) + ' encoding and ' + str(data.get('compression')) + ' compression.')
                    else:
                        # Convert <tile gid='N'/>... into a list of ints [obs, obs, obs...].
                        self.obsLayer = [int(t.get('gid', str(obsGID))) - obsGID for t in data.iter('tile')]
                else:
                    raise FormatException('Obstructions layer is missing <data> tag.')
            elif layer.get('name') == 'Zones':
                if not hasZones:
                    raise FormatException('This map has an \'Zones\' layer but is missing the \'zones\' tileset.')
                data = layer.find('data')
                if data != None:
                    if data.get('encoding') or data.get('compression'):
                        if data.get('encoding') == 'base64' and data.get('compression') == 'zlib':
                            # Convert base64'd zlib'd chunk of 32-bit integers into a list of zones
                            self.zoneLayer = [t - zoneGID for t in struct.unpack('<' + str(self.width * self.height) + 'i', zlib.decompress(base64.b64decode(str(data.text))))]
                        else:
                            raise FormatException('Cannot parse Zones layer with ' + str(data.get('encoding')) + ' encoding and ' + str(data.get('compression')) + ' compression.')
                    else:
                        # Convert <tile gid='N'/>... into a list of ints [zone, zone, zone...].
                        self.zoneLayer = [int(t.get('gid', str(zoneGID))) - zoneGID for t in data.iter('tile')]
                else:
                    raise FormatException('Zones layer is missing <data> tag.')
        print('    ...OK.')
        
    def toTiledDocument(self, compress=False):
        doc = xml.dom.minidom.Document()
        
        def addProperty(doc, props, key, value):
            prop = doc.createElement('property')
            prop.setAttribute('name', key)
            prop.setAttribute('value', value)
            props.appendChild(prop)
        
        # Map data
        map = doc.createElement('map')
        map.setAttribute('version', '1.0')
        map.setAttribute('orientation', 'orthogonal')
        map.setAttribute('width', str(self.width))
        map.setAttribute('height', str(self.height))
        map.setAttribute('tilewidth', str(VSP_TILESIZE))
        map.setAttribute('tileheight', str(VSP_TILESIZE))
        
        print('    Exporting properties...')
        props = doc.createElement('properties')
        addProperty(doc, props, 'title', self.mapName)
        addProperty(doc, props, 'music', self.musicFilename)
        addProperty(doc, props, 'start_event', self.startEvent)
        addProperty(doc, props, 'start_x', str(self.startX))
        addProperty(doc, props, 'start_y', str(self.startY))
        
        map.appendChild(props)
        
        # Tiles
        print('    Adding tileset reference...')
        tileset = doc.createElement('tileset')
        tileset.setAttribute('firstgid', '1')
        tileset.setAttribute('name', 'tiles')
        tileset.setAttribute('tilewidth', str(VSP_TILESIZE))
        tileset.setAttribute('tileheight', str(VSP_TILESIZE))
        
        image = doc.createElement('image')
        image.setAttribute('source', self.vspFilename + self.vsp.tileImageName)
        tileset.appendChild(image)
        map.appendChild(tileset)
        
        # Obstructions
        print('    Adding obstruction tileset reference...')
        tileset = doc.createElement('tileset')
        tileset.setAttribute('firstgid', str(self.vsp.tileLastGID + 1))
        tileset.setAttribute('name', 'obstructions')
        tileset.setAttribute('tilewidth', str(VSP_TILESIZE))
        tileset.setAttribute('tileheight', str(VSP_TILESIZE))
        
        image = doc.createElement('image')
        image.setAttribute('source', self.vspFilename + self.vsp.obsImageName)
        tileset.appendChild(image)
        map.appendChild(tileset)
        
        # Zone
        print('    Zone bank...')
        tileset = doc.createElement('tileset')
        tileset.setAttribute('firstgid', str(self.vsp.obsLastGID + 1))
        tileset.setAttribute('name', 'zones')
        tileset.setAttribute('tilewidth', str(VSP_TILESIZE))
        tileset.setAttribute('tileheight', str(VSP_TILESIZE))
        
        image = doc.createElement('image')
        image.setAttribute('source', os.path.basename(self.zoneDummyFilename))
        tileset.appendChild(image)
        
        for i in range(1, len(self.zone)):
            tile = doc.createElement('tile')
            tile.setAttribute('id', str(i))
            props = doc.createElement('properties')
            z = self.zone[i]
            addProperty(doc, props, 'name', z.name)
            addProperty(doc, props, 'allow_adjacent', str(z.method and 'true' or 'false'))
            addProperty(doc, props, 'activation_event', str(z.activationEvent))
            addProperty(doc, props, 'activation_chance', str(z.chance))
            addProperty(doc, props, 'activation_delay', str(z.delay))
            tile.appendChild(props)
            tileset.appendChild(tile)
        map.appendChild(tileset)
        
        # Tile layers (iterated in order by the map's rstring data)
        first = True
        print('    Visible layers...')
        for key in self.renderOrder:
            if key == 'E':
                print('        Entities...')
                lay = doc.createElement('objectgroup')
                lay.setAttribute('width', str(self.width))
                lay.setAttribute('height', str(self.height))
                lay.setAttribute('name', 'Entities')
                lay.setAttribute('color', '#99ff00')
                for entity in self.entity:
                    obj = doc.createElement('object')
                    obj.setAttribute('name', str(entity.description))
                    obj.setAttribute('type', 'entity')
                    obj.setAttribute('x', str(entity.x * VSP_TILESIZE))
                    obj.setAttribute('y', str(entity.y * VSP_TILESIZE))
                    obj.setAttribute('width', str(VSP_TILESIZE))
                    obj.setAttribute('height', str(VSP_TILESIZE))
                    
                    props = doc.createElement('properties')
                    addProperty(doc, props, 'id', str(entity.id))
                    addProperty(doc, props, 'filename', str(entity.filename))
                    addProperty(doc, props, 'direction', str(entity.direction))
                    addProperty(doc, props, 'is_obstructable', str(entity.isObstruction and 'true' or 'false'))
                    addProperty(doc, props, 'is_obstruction', str(entity.isObstruction and 'true' or 'false'))
                    addProperty(doc, props, 'autoface', str(entity.autoface and 'true' or 'false'))
                    addProperty(doc, props, 'speed', str(entity.speed))
                    addProperty(doc, props, 'movement_mode', str(entity.movementMode))
                    if entity.movementMode == 'wander_rect':
                        addProperty(doc, props, 'wander_x1', str(entity.wanderX1))
                        addProperty(doc, props, 'wander_y1', str(entity.wanderY1))
                        addProperty(doc, props, 'wander_x2', str(entity.wanderX2))
                        addProperty(doc, props, 'wander_y2', str(entity.wanderY2))
                        addProperty(doc, props, 'wander_delay', str(entity.wanderDelay))
                    elif entity.movementMode == 'wander_zone':
                        addProperty(doc, props, 'wander_delay', str(entity.wanderDelay))
                    elif entity.movementMode == 'script':
                        addProperty(doc, props, 'movescript', str(entity.movescript))
                    addProperty(doc, props, 'activation_event', str(entity.activationEvent))
                    obj.appendChild(props)
                    
                    lay.appendChild(obj)
                map.appendChild(lay)
            elif key == 'R':
                # This object layer needs to exist solely to give a render position to HookRetrace.
                print('        Retrace...')
                lay = doc.createElement('objectgroup')
                lay.setAttribute('width', str(self.width))
                lay.setAttribute('height', str(self.height))
                lay.setAttribute('name', 'Retrace')
                map.appendChild(lay)
            else:
                layer = self.renderItem[key]
                print('        Layer #' + str(layer.id) + ': ' + layer.name + '...')
                lay = doc.createElement('layer')
                lay.setAttribute('name', layer.name)
                lay.setAttribute('width', str(layer.width))
                lay.setAttribute('height', str(layer.height))
                lay.setAttribute('opacity', str(layer.alpha))
                
                props = doc.createElement('properties')
                addProperty(doc, props, 'id', str(layer.id))
                addProperty(doc, props, 'parallax_x', str(layer.parallaxX))
                addProperty(doc, props, 'parallax_y', str(layer.parallaxY))
                lay.appendChild(props)
                
                data = doc.createElement('data')
                # tile 0 is drawn as-is on the first layer, but is completely transparent on higher layers.
                if first:
                    if compress:
                        data.setAttribute('encoding', 'base64')
                        data.setAttribute('compression', 'zlib')                        
                        text = doc.createTextNode(base64.b64encode(zlib.compress(struct.pack('<' + str(layer.width * layer.height) + 'i', *[t + 1 for t in layer.data]))))
                        data.appendChild(text)
                    else:
                        for t in layer.data:
                            tile = doc.createElement('tile')
                            tile.setAttribute('gid', str(t + 1))
                            data.appendChild(tile)
                    first = False
                else:
                    if compress:
                        data.setAttribute('encoding', 'base64')
                        data.setAttribute('compression', 'zlib')
                        text = doc.createTextNode(base64.b64encode(zlib.compress(struct.pack('<' + str(layer.width * layer.height) + 'i', *[t != 0 and t + 1 or 0 for t in layer.data]))))
                        data.appendChild(text)
                    else:
                        for t in layer.data:
                            tile = doc.createElement('tile')
                            tile.setAttribute('gid', t != 0 and str(t + 1) or '0')
                            data.appendChild(tile)
                lay.appendChild(data)
                map.appendChild(lay)
        
        # Obstructions
        print('    Obstruction layer...')
        lay = doc.createElement('layer')
        lay.setAttribute('name', 'Obstructions')
        lay.setAttribute('width', str(self.width))
        lay.setAttribute('height', str(self.height))
        lay.setAttribute('opacity', '1')
        
        data = doc.createElement('data')
        id = self.vsp.tileLastGID + 1
        if compress:
            data.setAttribute('encoding', 'base64')
            data.setAttribute('compression', 'zlib')
            text = doc.createTextNode(base64.b64encode(zlib.compress(struct.pack('<' + str(self.width * self.height) + 'i', *[t + id for t in self.obsLayer]))))
            data.appendChild(text)
        else:
            for t in self.obsLayer:
                tile = doc.createElement('tile')
                tile.setAttribute('gid', str(t + id))
                data.appendChild(tile)
        lay.appendChild(data)
        map.appendChild(lay)
        
        # Zones
        print('    Zone layer...')
        lay = doc.createElement('layer')
        lay.setAttribute('name', 'Zones')
        lay.setAttribute('width', str(self.width))
        lay.setAttribute('height', str(self.height))
        lay.setAttribute('opacity', str(1))
        
        data = doc.createElement('data')
        id = self.vsp.obsLastGID + 1
        if compress:
            data.setAttribute('encoding', 'base64')
            data.setAttribute('compression', 'zlib')
            text = doc.createTextNode(base64.b64encode(zlib.compress(struct.pack('<' + str(self.width * self.height) + 'i', *[t + id for t in self.zoneLayer]))))
            data.appendChild(text)
        else:
            for t in self.zoneLayer:
                tile = doc.createElement('tile')
                tile.setAttribute('gid', str(t + id))
                data.appendChild(tile)
        lay.appendChild(data)
        map.appendChild(lay)
        
        # Done!
        doc.appendChild(map)
        return doc