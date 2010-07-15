import zlib
import struct

class DataInputStream(object):
    def __init__ (self, file):
        self.file = file
        
    def read(self, length):
        return self.file.read(length)
        
    def readCompressed(self):
        uncompressedSize = self.readInt()
        compressedSize = self.readInt()
        compressedData = self.read(compressedSize)
        uncompressedData = zlib.decompress(compressedData)
        return uncompressedData
        
    def readFixedString(self, length):
        s = self.read(length)
        output = ''
        for i in range(len(s)):
            if s[i] != '\0':
                output += s[i]
            else:
                break
        return output
                
    def readChar(self):
        v, = struct.unpack('<c', self.file.read(struct.calcsize('<c')))
        return v

    def readByte(self):
        v, = struct.unpack('<b', self.file.read(struct.calcsize('<b')))
        return v
        
    def readUnsignedByte(self):
        v, = struct.unpack('<B', self.file.read(struct.calcsize('<B')))
        return v
        
    def readShort(self):
        v, = struct.unpack('<h', self.file.read(struct.calcsize('<h')))
        return v
        
    def readUnsignedShort(self):
        v, = struct.unpack('<H', self.file.read(struct.calcsize('<H')))
        return v
        
    def readInt(self):
        v, = struct.unpack('<i', self.file.read(struct.calcsize('<i')))
        return v
        
    def readUnsignedInt(self):
        v, = struct.unpack('<I', self.file.read(struct.calcsize('<I')))
        return v
                
    def readLong(self):
        v, = struct.unpack('<l', self.file.read(struct.calcsize('<l')))
        return v
        
    def readUnsignedLong(self):
        v, = struct.unpack('<L', self.file.read(struct.calcsize('<L')))
        return v
                
    def readFloat(self):
        v, = struct.unpack('<f', self.file.read(struct.calcsize('<f')))
        return v
        
    def readDouble(self):
        v, = struct.unpack('<d', self.file.read(struct.calcsize('<d')))
        return v
    
    def close (self):
        self.file.close()
        
class DataOutputStream(object):
    def __init__ (self, file):
        self.file = file
        
    def write(self, blob):
        return self.file.write(blob)
        
    def writeCompressed(self, uncompressedData):
        self.writeInt(len(uncompressedData))
        compressedData = zlib.compress(uncompressedData)
        self.writeInt(len(compressedData))
        self.write(compressedData)
        
    def writeFixedString(self, s, length):
        self.write(s + ('\0' * (length - len(s))))
                
    def writeChar(self, v):
        self.write(struct.pack('<c', v))

    def writeByte(self, v):
        self.write(struct.pack('<b', v))
        
    def writeUnsignedByte(self, v):
        self.write(struct.pack('<B', v))
        
    def writeShort(self, v):
        self.write(struct.pack('<h', v))
        
    def writeUnsignedShort(self, v):
        self.write(struct.pack('<H', v))
        
    def writeInt(self, v):
        self.write(struct.pack('<i', v))
        
    def writeUnsignedInt(self, v):
        self.write(struct.pack('<I', v))
                
    def writeLong(self, v):
        self.write(struct.pack('<l', v))
        
    def writeUnsignedLong(self, v):
        self.write(struct.pack('<L', v))
                
    def writeFloat(self, v):
        self.write(struct.pack('<f', v))
        
    def writeDouble(self, v):
        self.write(struct.pack('<d', v))
    
    def close(self):
        self.file.close()