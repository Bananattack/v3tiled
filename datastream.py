import zlib
import struct
import array
import base64

def flatten(seq):
	res = []
	for item in seq:
		if (isinstance(item, (tuple, list))):
			res.extend(flatten(item))
		else:
			res.append(item)
	return res

def ForceGridBoolean(a, width, height):
	for x in range(width):
		for y in range(height):
			a[x][y] = int(a[x][y] != 0)

def CompressGrid(a, width, height):
	#s = ""
	#for x in range(width):
	#	for y in range(height):
	#		s += struct.pack("@i", array[x][y])
	a = flatten(a)
	s = ""
	for i in range(len(a)):
		s += struct.pack("@i", a[i])
	#arr = array.array('i', a)
	#s = arr.tostring()
	s = base64.b64encode(zlib.compress(s))
	return s

class DataInputStream:
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
		output = ""
		for i in range(len(s)):
			if s[i] != "\0":
				output += s[i]
			else:
				break
		return output
				
	def readChar(self):
		v, = struct.unpack("@c", self.file.read(struct.calcsize("@c")))
		return v

	def readByte(self):
		v, = struct.unpack("@b", self.file.read(struct.calcsize("@b")))
		return v
		
	def readUnsignedByte(self):
		v, = struct.unpack("@B", self.file.read(struct.calcsize("@B")))
		return v
		
	def readShort(self):
		v, = struct.unpack("@h", self.file.read(struct.calcsize("@h")))
		return v
		
	def readUnsignedShort(self):
		v, = struct.unpack("@H", self.file.read(struct.calcsize("@H")))
		return v
		
	def readInt(self):
		v, = struct.unpack("@i", self.file.read(struct.calcsize("@i")))
		return v
		
	def readUnsignedInt(self):
		v, = struct.unpack("@I", self.file.read(struct.calcsize("@I")))
		return v
				
	def readLong(self):
		v, = struct.unpack("@l", self.file.read(struct.calcsize("@l")))
		return v
		
	def readUnsignedLong(self):
		v, = struct.unpack("@L", self.file.read(struct.calcsize("@L")))
		return v
				
	def readFloat(self):
		v, = struct.unpack("@f", self.file.read(struct.calcsize("@f")))
		return v
		
	def readDouble(self):
		v, = struct.unpack("@d", self.file.read(struct.calcsize("@d")))
		return v
	
	def close (self):
		self.file.close()