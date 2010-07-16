#!/usr/bin/env python
import v3formats

if __name__ == '__main__':
    import sys
    
    def main():
        vsp = v3formats.VSP()
        vsp.buildFromExternal('../grue0030.vsp.tile.png', '../grue0030.vsp.obs.png', '../grue0030.vsp.anim')
        vsp.saveVSPFile('../grue0030.vsp')
    
    main()