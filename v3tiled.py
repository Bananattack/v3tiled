#!/usr/bin/env python
import v3formats

def convertMap(name, needVSP, compress):
    map = v3formats.Map()
    print('Loading \'' + name + '\'...')
    try:
        map.loadMapFile(name)
    except v3formats.FormatException as e:
        sys.stderr.write(sys.argv[0] + ': ' + str(e) + '\n')
        return
    if needVSP:
        convertVSP(vsp = map.vsp)
    print('Creating zone dummy image...')
    map.dumpZoneDummyImage()
    print('Converting map...')
    f = file(name + '.tmx', 'w')
    doc = map.toTiledDocument(compress)
    print('    Saving document...')
    f.write(doc.toprettyxml(indent='    '))
    f.close()
    print('    Saved to \'' + name + '.tmx\'.')
    print('Done.')
    
def convertVSP(name='', **kwargs):
    vsp = None
    if 'vsp' in kwargs:
        vsp = kwargs['vsp']
    else:
        vsp = v3formats.VSP()
        print('Loading \'' + name + '\'...')
        try:
            vsp.loadVSPFile(name)
        except v3formats.FormatException as e:
            sys.stderr.write(sys.argv[0] + ': ' + str(e) + '\n')
            return
    print('Converting tileset...')
    vsp.dumpTiles()
    print('Converting tileset obstructions...')
    vsp.dumpObs()
    print('Exporting animation info...')
    doc = vsp.toAnimDocument()
    f = file(vsp.filename + '.anim', 'w')
    f.write(doc.toprettyxml(indent='    '))
    f.close()
    print('    Saved to \'' + vsp.filename + '.anim\'.')    

if __name__ == '__main__':
    import sys
    
    def main():
        count = 0
        needVSP = False
        compress = True
        for i in range(1, len(sys.argv)):
            arg = sys.argv[i]
            if arg.startswith('-'):
                if arg ==  '-v':
                    needVSP = True
                elif arg ==  '-raw':
                    compress = False
                elif arg ==  '-z':
                    compress = True
                else:
                    sys.stderr.write(sys.argv[0] + ': unknown option \'' + arg + '\'. run with no arguments to see usage.\n')
                    sys.exit(-1)
            else:
                count += 1
                print('')
                if arg.lower().endswith('.map'):
                    convertMap(arg, needVSP, compress)
                elif arg.lower().endswith('.vsp'):
                    convertVSP(arg)
                else:
                    sys.stderr.write(sys.argv[0] + ': file \'' + arg + '\' has an unsupported extension.\n')
        if count == 0:
            print('')
            sys.stderr.write(sys.argv[0] + ': no input files\n')
            print('* Usage: ' + sys.argv[0] + ' [OPTIONS] file [file ...]')
            print('')
            print('Convert maped3 formats into tiled-friendly files.')
            print('')
            print('file:')
            print('    a file to convert. This can be a .map or .vsp file.')
            print('    If the file is a .map, it will assume the .vsp and its converted parts')
            print('    that the exported .tmx needs exist. Use -v if you want to convert the .vsp')
            print('    along with the map.')
            print('')
            print('    If the file is a .vsp, it exports a .png, as well as a .anim file which')
            print('    is used to store the animation info of the original VSP.')
            print('')
            print('OPTIONS:')
            print('-v               convert the .vsp used by any map, like passed on commandline.')
            print('-raw             use plain-text XML (no compression).')
            print('-z               (default) compress the .tmx map with zlib.')
    
    main()