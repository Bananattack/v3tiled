#!/usr/bin/env python
import v3formats

def convertMap(name, needVSP, needMap):
    map = v3formats.Map()
    if needVSP:
        print('Loading \'' + name + '\'...')
        map.loadMapFile(name)
        print('Converting tileset...')
        map.vsp.dumpTiles()
        print('Converting tileset obstructions...')
        map.vsp.dumpObs()
        print('Creating zone dummy image...')
        map.dumpZoneDummyImage()
        print('Exporting animation info...')
        doc = map.vsp.toAnimDocument()
        f = file(map.vsp.filename + '.anim', 'w')
        f.write(doc.toprettyxml(indent='    '))
        f.close()
        print('    Saved to \'' + map.vsp.filename + '.anim\'.')
    if needMap:
        print('Converting map...')
        f = file(name + '.tmx', 'w')
        doc = map.toTiledDocument()
        print('    Saving document...')
        f.write(doc.toprettyxml(indent='    '))
        f.close()
        print('    Saved to \'' + name + '.tmx\'.')
    print('Done.')

if __name__ == '__main__':
    import sys
    count = 0
    redundant = False
    onlyVSP = False
    onlyMap = False
    for i in range(1, len(sys.argv)):
        arg = sys.argv[i]
        if arg.startswith('-'):
            if arg ==  '-vsp-only':
                redundant = onlyVSP or onlyMap
                onlyVSP = True
            elif arg ==  '-map-only':
                redundant = onlyVSP or onlyMap
                onlyMap = True
        else:
            count += 1
            print('')
            if not onlyVSP and not onlyMap:
                convertMap(arg, True, True)
            else:
                if redundant:
                    sys.stderr.write(sys.argv[0] + ': warning: your command was a little redundant, but okay.\n')
                convertMap(arg, onlyVSP, onlyMap)
    if count == 0:
        print('')
        sys.stderr.write(sys.argv[0] + ': no input files\n')
        print('Usage: [OPTIONS]' + sys.argv[0] + ' file [file ...]')
        print('')
        print('Convert maped3 formats into tmx + png files.')
        print('')
        print('file: a map to convert (will also require the VSP that the map uses)')
        print('OPTIONS:')
        print('-vsp-only        Only convert the VSP.')
        print('-map-only        Only convert the map (assumes the VSPs exist).')