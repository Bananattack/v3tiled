#!/usr/bin/env python
import v3formats
        
def convertMap(name):
    map = v3formats.Map()
    print('Loading \'' + name + '\'...')
    map.loadMapFile(name)
    print('Dumping tileset...')
    map.vsp.dumpTiles()
    print('Dumping tileset obstructions...')
    map.vsp.dumpObs()
    print('Dumping zone dummy image...')
    map.dumpZoneDummyImage()
    print('Converting map...')
    f = file(name + '.tmx', 'w')
    doc = map.exportTMX()
    print('    Saving document...')
    f.write(doc.toprettyxml(indent='    '))
    f.close()
    print('    Saved to \'' + name + '.tmx\'.')
    print('Done.')

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2: 
        print('')
        print(sys.argv[0] + ': no input files')
        print('Usage: ' + sys.argv[0] + ' MAPFILE [MAPFILE ...]')
        print('')
        print('Convert maped3 formats into tmx + png files.')
        print('')
        print('MAPFILE: a map to convert (will also require the VSP the map uses)')
    else:
        print('')
        print(sys.argv[0] + '.')
        print('')
        for i in range(1, len(sys.argv)):
            convertMap(sys.argv[i])