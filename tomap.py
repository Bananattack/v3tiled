#!/usr/bin/env python
import v3formats

if __name__ == '__main__':
    import sys
    
    def main():
        if len(sys.argv) == 4:
            map = v3formats.Map()
            print('Converting ' + sys.argv[2] + '...')
            try:
                map.convertFromTiled(sys.argv[2])
            except v3formats.FormatException as e:
                sys.stderr.write(sys.argv[0] + ': ' + str(e) + '\n')
                return
            map.vspFilename = sys.argv[3]
            print('    Saving document...')
            map.saveMapFile(sys.argv[1], sys.argv[3])
            print('Done.')
        else:
            print('')
            sys.stderr.write(sys.argv[0] + ': ' + (len(sys.argv) < 4 and 'insufficient' or 'too many') + ' arguments.\n')
            print('Usage: ' + sys.argv[0] + ' outputfile tmxfile vspfile')
            print('')
            print('Converts a tiled .tmx file back to Verge-friendly .map file.')
            print('')
            print('outputfile: the name of the .map file to be generated.')
            print('tmxfile: a tiled map format to convert back. This may require the tmx\'s')
            print('         functionality to be fit some restrictions to aid in the conversion')
            print('vspfile: the name of the vsp file the map needs.')
            print('         IMPORTANT: Path must be relative to the map and should not use ../')
            print('         (but this tool will not verify that.)')
    
    main()