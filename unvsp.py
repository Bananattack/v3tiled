#!/usr/bin/env python
import v3tiled

if __name__ == '__main__':
    import sys
    
    def main():
        count = 0
        needVSP = False
        compress = True
        for i in range(1, len(sys.argv)):
            arg = sys.argv[i]
            if arg.startswith('-'):
                if False:
                    pass
                else:
                    print('')
                    sys.stderr.write(sys.argv[0] + ': unknown option \'' + arg + '\'. run with no arguments to see usage.\n')
                    sys.exit(-1)
            else:
                count += 1
                print('')
                if arg.lower().endswith('.vsp'):
                    v3tiled.convertVSP(arg)
                else:
                    sys.stderr.write(sys.argv[0] + ': file \'' + arg + '\' is not a VSP.\n')
        if count == 0:
            print('')
            sys.stderr.write(sys.argv[0] + ': no input files\n')
            print('* Usage: ' + sys.argv[0] + ' [OPTIONS] file [file ...]')
            print('')
            print('Convert a .vsp back to an image.')
            print('')
            print('file:')
            print('    a file to convert. This must be a .vsp file. If the file')
            print('    is a .vsp, it exports a .png, as well as a .anim file which')
            print('    is used to store the animation info of the original VSP.')
            print('')
            print('OPTIONS: none in this version.')
    
    main()