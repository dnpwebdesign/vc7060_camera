#!/usr/bin/python
# python code for interfacing to VC0706 cameras and grabbing a photo
# pretty basic stuff
# written by ladyada. MIT license
# revisions for Raspberrry Pi by Gordon Rush

import serial 
import array

BAUD = 38400
# this is the port on the Raspberry Pi; it will be different for serial ports on other systems.
PORT = "/dev/ttyAMA0"

TIMEOUT = 0.5    # I needed a longer timeout than ladyada's 0.2 value
SERIALNUM = 0    # start with 0, each camera should have a unique ID.

COMMANDSEND = 0x56
COMMANDREPLY = 0x76
COMMANDEND = 0x00

CMD_GETVERSION = 0x11
CMD_RESET = 0x26
CMD_TAKEPHOTO = 0x36
CMD_READBUFF = 0x32
CMD_GETBUFFLEN = 0x34

FBUF_CURRENTFRAME = 0x00
FBUF_NEXTFRAME = 0x01

FBUF_STOPCURRENTFRAME = 0x00

getversioncommand = [COMMANDSEND, SERIALNUM, CMD_GETVERSION, COMMANDEND]
resetcommand = [COMMANDSEND, SERIALNUM, CMD_RESET, COMMANDEND]
takephotocommand = [COMMANDSEND, SERIALNUM, CMD_TAKEPHOTO, 0x01, FBUF_STOPCURRENTFRAME]
getbufflencommand = [COMMANDSEND, SERIALNUM, CMD_GETBUFFLEN, 0x01, FBUF_CURRENTFRAME]

def checkreply(r, b):
	r = list(r)
#	string= u''.join(r).encode('utf-8').strip()
	string = ''.join(list(map(chr,r)))
	print("the reply:",r)
	print("the reply strin:",string)
	print("The commmand = " ,b)
	if(r[0] == COMMANDREPLY and r[1] == SERIALNUM and r[2] == b and r[3] == 0x00):
		return True
	return False

def reset():
	cmd = ''.join( list(map( chr, resetcommand )) )
	s.write(bytes(cmd,"UTF-8"))
	reply = s.read(100)
	r = list(reply)
	if checkreply( r, CMD_RESET ):
		return True
	return False

def getversion():
	cmd = ''.join( list(map( chr, getversioncommand )))
	s.write(bytes(cmd,"UTF-8"))
	reply = s.read(17)
	r = list(reply)
	print (r)
	if checkreply( r, CMD_GETVERSION ):
		print (r)
		return True
	return True

def takephoto():
	cmd = ''.join( list(map( chr, takephotocommand )))
	s.write(bytes(cmd,"UTF-8"))
	reply = s.read(5)
	r = list(reply)
	# print r
	if( checkreply( r, CMD_TAKEPHOTO) and r[3] == int(0x0)):
		return True
	return False

def getbufferlength():
	cmd = ''.join( list(map( chr, getbufflencommand )))
	s.write(bytes(cmd,"UTF-8"))
	reply = s.read(10)
	r = list(reply)
	print("r[0]",r[0])
	print("r[1]",r[1])
	print("r[2]",r[2])
	print("r[3]",r[3])
	print("r[4]",r[4])
	print("buffer length", r)
	print("r[5]",r[5])
	print("r[6]",r[6])
	print("r[7]",r[7])
	print("r[8]",r[8])

	if( checkreply( r, CMD_GETBUFFLEN) and r[4] == int(0x4)):
		print("goblok", r, CMD_GETBUFFLEN)
		l = r[5]
		print(l)
		l <<= 8
		print(l)
		l += r[6]
		print(l)
		l <<= 8
		print(l)
		l += r[7]
		print(l)
		l <<= 8
		print(l)
		l += r[8]
		print(l)
		return l
	return 0

readphotocommand = [COMMANDSEND, SERIALNUM, CMD_READBUFF, 0x0c, FBUF_CURRENTFRAME, 0x0a]


def readbuffer(bytes):
	addr = 0   # the initial offset into the frame buffer
	photo = []

	# bytes to read each time (must be a mutiple of 4)
	inc = 8192

	while( addr < bytes ):
 		# on the last read, we may need to read fewer bytes.
		chunk = min( bytes-addr, inc );

		# append 4 bytes that specify the offset into the frame buffer
		command = readphotocommand + [(addr >> 24) & 0xff, 
				(addr>>16) & 0xff, 
				(addr>>8 ) & 0xff, 
				addr & 0xff]

		# append 4 bytes that specify the data length to read
		command += [(chunk >> 24) & 0xff, 
				(chunk>>16) & 0xff, 
				(chunk>>8 ) & 0xff, 
				chunk & 0xff]

		# append the delay
		command += [1,0]

		print("write command", command)
	#	print(map(hex, command))
		print ("Reading", chunk, "bytes at", addr)

		# make a string out of the command bytes.
#		cmd = ''.join(list(command))
		cmd = array.array('B', command).tostring()
#		s.write(bytes(cmd,"UTF-8"))
		s.write(cmd)

		# the reply is a 5-byte header, followed by the image data
		#   followed by the 5-byte header again.
		reply = s.read(5+chunk+5)

 		# convert the tuple reply into a list
		r = list(reply)
		if( len(r) != 5+chunk+5 ):
			# retry the read if we didn't get enough bytes back.
			print ("Read", len(r), "Retrying.")
			continue

		if( not checkreply(r, CMD_READBUFF)):
			print ("ERROR READING PHOTO")
			return
		
		# append the data between the header data to photo
		photo += r[5:chunk+5]

		# advance the offset into the frame buffer
		addr += chunk

	print (addr, "Bytes written")
	return photo


######## main

s = serial.Serial( PORT, baudrate=BAUD, timeout = TIMEOUT )

reset()

if( not getversion() ):
	print ("Camera not found")
	exit(0)

print ("VC0706 Camera found")

if takephoto():
	print ("Snap!")

bytes_to_read = getbufferlength()

print (bytes_to_read, "bytes to read")

#bts = array.array('B', bytes_to_read).tostring()
photo = readbuffer( bytes_to_read )

f = open( "photo.jpg", 'wb' )

#photodata = ''.join( photo )
photodata = array.array('B', photo).tostring()

f.write( photodata )

f.close()
