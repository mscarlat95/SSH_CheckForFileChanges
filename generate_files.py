from random import randint, seed
import io, sys, signal, time

# timer count down interval
interval = 10

seed()

def signal_handler(signum, frame):
	print "\nReceived signal %s. Exiting ..." % signum
	sys.exit (1)

def min (a, b):
	if a < b:	
		return a
	return b

def to_ascii(number):
	return str (unichr (number))


# write content into file 
def writeContent(fname):
	fd = open(fname, 'w')

	N = 1000
	for i in xrange (N):
			fd.write (to_ascii(randint(65, 90)))
			if (i+1) % 50 == 0:
				fd.write("\n")
	fd.close()


# create random files 
def createFile():
	signal.signal (signal.SIGINT, signal_handler)

	while True:
		fname = ""
		fname_sz = 15
		
		for i in xrange (fname_sz):
			fname += to_ascii(randint(97, 122))
		writeContent(fname)
		print "Created file %s ." % fname

		time.sleep(interval)

if __name__ == "__main__":

	if len (sys.argv) != 2:
		print "Usage: python script.py <timer countdown>"
		sys.exit (1)


	interval = int (sys.argv[1])
	createFile()

	