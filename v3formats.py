import datastream
import struct
import base64
import zlib
import os.path
import xml.dom.minidom
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

class FormatException(Exception):
    pass



ANIMATION_MODE = {
    '0': 'forward',
    '1': 'reverse',
    '2': 'random',
    '3': 'ping_pong',
}
    
class Animation(object):
    def __init__(self):
        self.id = -1
    
    def readFromVSP(self, f):
        self.name = f.readFixedString(256)
        self.start = f.readInt()
        self.end = f.readInt()
        self.delay = f.readInt()
        self.mode = ANIMATION_MODE.get(f.readInt(), 'forward')



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
            raise FormatException('The VSP file \'' + filename + '\' was not found.')
        
        signature = f.readInt()
        version = f.readInt()
        
        if signature != VSP_SIGNATURE:
            raise FormatException('The VSP file \'' + filename + '\' has a bad signature of ' + signature)
        if version != VSP_VERSION:
            raise FormatException('The VSP file \'' + filename + '\' has a bad version of ' + str(version))
            
        tilesize = f.readInt()
        format = f.readInt()
        self.tileCount = f.readInt()
        compression = f.readInt()
        
        self.tileset = []
        
        self.tilePixels = f.readCompressed()
        self.tileImageName = '.tile.png'
        self.tileLastGID = (self.tileCount // 20 + 1) * 20
            
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
        self.obsLastGID = (self.obsCount // 20 + 1) * 20 + self.tileLastGID + 1

        f.close()
        
    def dumpTiles(self):
        pixels = self.tilePixels
        tileImage = PIL.Image.new('RGBA', (20 * 16, (self.tileCount // 20 + 1) * 16))
        
        image = tileImage.load()
        for tile in range(self.tileCount):
            y, x = tile // 20 * 16, tile % 20 * 16
            for i in range(16 * 16):
                idx = tile * 16 * 16 + i
                r, g, b = struct.unpack('@BBB', pixels[idx * 3 : idx * 3 + 3])
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
                pixel, = struct.unpack('@B', pixels[idx])
                pixel = pixel and (255, 255, 255, 127) or (0, 0, 0, 0)
                image[x + i % 16, y + i / 16] = pixel
        obsImage.save(self.filename + self.obsImageName, 'PNG')
        print('    Saved to \'' + self.filename + self.obsImageName + '\'.')
        
    def toAnimDocument(self):
        doc = xml.dom.minidom.Document()
        animations = doc.createElement('animations')
        for anim in self.animation:
            node = doc.createElement('animation')
            node.setAttribute('id', str(anim.id))
            node.setAttribute('name', str(anim.name))
            node.setAttribute('tile_begin', str(anim.start))
            node.setAttribute('tile_end', str(anim.end))
            node.setAttribute('delay', str(anim.delay))
            node.setAttribute('mode', str(anim.mode))
            animations.appendChild(node)
        doc.appendChild(animations)
        return doc



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
        
        lucent = f.readByte()
        self.alpha = 1 - lucent / 100
        
        layerdata = f.readCompressed()
        for i in range(len(layerdata) / 2):
            self.data[i], = struct.unpack('@H', layerdata[i * 2 : i * 2 + 2])
        
        self.xOffset = 0
        self.yOffset = 0



class Zone(object):
    def __init__(self):
        self.id = -1
    
    def readFromMap(self, f):
        self.name = f.readFixedString(256)
        self.activationEvent = f.readFixedString(256)
        self.chance = f.readUnsignedByte() / 255.0
        self.delay = f.readUnsignedByte()
        self.method = f.readUnsignedByte()



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

ENTITY_MOVEMENT = {
    '0': 'none',
    '1': 'wander_zone',
    '2': 'wander_rect',
    '3': 'script',
}

class Entity(object):
    def __init__(self):
        self.id = -1
        
    def readFromMap(self, f):
        self.x = f.readShort()
        self.y = f.readShort()
        self.direction = ENTITY_DIR.get(f.readByte(), 'north')
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



MAP_SIGNATURE = 'V3MAP\0'
MAP_VERSION = 2
        
class Map(object):
    def __init__(self):
        pass
        
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
        self.musicFilename = f.readFixedString(256)
        self.rstring = f.readFixedString(256).split(',')
        self.renderItem = {}
        self.startEvent = f.readFixedString(256)

        # Starting location. If not specificied in script, use the map's default.
        self.startX = f.readUnsignedShort()
        self.startY = f.readUnsignedShort()
        self.vsp = VSP()
        self.vsp.loadVSPFile(os.path.dirname(self.filename) + '/' + self.vspFilename)

        # Layers!
        layerCount = f.readInt()
        self.layer = []
        for i in range(layerCount):
            layer = Layer()
            layer.id = i
            layer.readFromMap(f)
            self.layer.append(layer)
            self.renderItem[str(layer.id + 1)] = layer

        # Dimensions!
        self.width = self.layer[0].width
        self.height = self.layer[0].height

        # Obstructions layer!
        self.obsLayer = [False] * (self.width * self.height)
        layerdata = f.readCompressed()
        for i in range(len(layerdata)):
            self.obsLayer[i], = struct.unpack('@b', layerdata[i])

        # Zone layer!
        self.zoneLayer = [None] * (self.width * self.height)
        layerdata = f.readCompressed()
        for i in range(len(layerdata) / 2):
            self.zoneLayer[i], = struct.unpack('@H', layerdata[i * 2 : i * 2 + 2])

        # Zone info!
        zoneCount = f.readInt()
        self.zone = []
        for i in range(zoneCount):
            zone = Zone()
            zone.id = i
            zone.readFromMap(f)
            self.zone.append(zone)

        # Entities!
        self.entity = []
        entityCount = f.readInt()
        for i in range(entityCount):
            ent = Entity()
            ent.id = i
            ent.readFromMap(f)
            self.entity.append(ent)
            
        # We're done with the map file
        f.close()
    
    def dumpZoneDummyImage(self):
        font = PIL.ImageFont.load_default()
        zoneCount = len(self.zone)
        image = PIL.Image.new('RGBA', (20 * 16, (zoneCount // 20 + 1) * 16))
        draw = PIL.ImageDraw.Draw(image)
        bg = (127, 0, 127, 127)
        textColor = (255, 255, 255, 255)
        for i in range(1, zoneCount):
            x, y = i % 20 * 16, i / 20 * 16
            draw.rectangle((x, y, x + 16, y + 16), fill = bg)
            draw.text((x, y), str(i), font = font, fill = textColor)
        image.save(self.zoneDummyFilename, 'PNG')
        print('    Saved to \'' + self.zoneDummyFilename + '\'.')
        
    def toTiledDocument(self, compress=False, embedAnim=False):
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
        
        print('    Exporting tileset animation info...')
        props = doc.createElement('properties')
        addProperty(doc, props, 'title', self.mapName)
        addProperty(doc, props, 'music', self.musicFilename)
        addProperty(doc, props, 'start_event', self.startEvent)
        addProperty(doc, props, 'start_x', str(self.startX))
        addProperty(doc, props, 'start_y', str(self.startY))
        
        if embedAnim:
            for anim in self.vsp.animation:
                addProperty(doc, props, 'vsp_anim_' + str(anim.id) + '_name', str(anim.name))
                addProperty(doc, props, 'vsp_anim_' + str(anim.id) + '_start', str(anim.start))
                addProperty(doc, props, 'vsp_anim_' + str(anim.id) + '_end', str(anim.end))
                addProperty(doc, props, 'vsp_anim_' + str(anim.id) + '_delay', str(anim.delay))
                addProperty(doc, props, 'vsp_anim_' + str(anim.id) + '_mode', str(anim.mode))
        
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
            addProperty(doc, props, 'activation_chance', str(float(z.chance)))
            addProperty(doc, props, 'activation_delay', str(z.delay))
            tile.appendChild(props)
            tileset.appendChild(tile)
        map.appendChild(tileset)
        
        # Tile layers (probably needs rstring reordering)
        first = True
        print('    Visible layers...')
        for key in self.rstring:
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
                    addProperty(doc, props, 'filename', str(entity.filename))
                    addProperty(doc, props, 'direction', str(entity.direction))
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
                addProperty(doc, props, 'layer_index', str(layer.id))
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