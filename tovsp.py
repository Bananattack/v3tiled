#!/usr/bin/env python
import v3formats

if __name__ == '__main__':
    import sys
    
    def main():
        if len(sys.argv) == 4 or len(sys.argv) == 5:
            vsp = v3formats.VSP()
            vsp.buildFromExternal(sys.argv[2], sys.argv[3], len(sys.argv) == 5 and sys.argv[4] or None)
            vsp.saveVSPFile(sys.argv[1])
        else:
            print('')
            print(sys.argv[0] + ': ' + (len(sys.argv) < 4 and 'insufficient' or 'too many') + ' arguments.')
            print('Usage: ' + sys.argv[0] + ' output tile obs [anim]')
            print('')
            print('Combines images and animation information to make a .vsp file.')
            print('')
            print('output: the name of the .vsp file to be generated.')
            print('tile: a file consisting of 16x16 tiles. Any non-opaque areas')
            print('      are replaced with #ff00ff pixels.')
            print('obs: a file consisting of 16x16 obstructions. Any fully transparent area')
            print('     is treated as 0 (passible), and 1 (obstruction) otherwise.')
            print('anim: an optional .anim file which describes animations used by the ')
            print('      tileset. This is an XML format.')
    
    main()