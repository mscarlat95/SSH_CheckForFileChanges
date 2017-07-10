import paramiko, sys, mysql.connector
import threading, time
from mysql.connector import Error

################################################################################


def getHashset(lst):
	hashSet = {}
	hashSet["inode"] = lst[0]
	hashSet["permissions"] = lst[1]
	hashSet["links"] = lst[2]
	hashSet["owner"] = lst[3]
	hashSet["groups"] = lst[4]
	hashSet["size"] = lst[5]
	hashSet["last_modified"] = "%s %s %s" % (lst[6], lst[7], lst[8])
	hashSet["name"] = lst[9]

	return hashSet

def parseSSHResult (str):	
	result = []
	for line in str.splitlines():
		lst = line.split()
		if len (lst) == 10:
			result.append (getHashset (lst))
	return result

################################################################################

conn = ""
def db_connect():
	global conn;
	try:
		conn = mysql.connector.connect (host = "localhost",
						database = "demoDB",
						user = "root",
						password = "root")
		if conn.is_connected():
			print "Connection to database: Established !"
	except Error as e:
		print "Error during connecting to the database! Exiting ..."
		sys.exit (1)

def performQuery(command):
	global conn
	cursor = ""

	try:
		cursor = conn.cursor()
		cursor.execute (command)
	except Error as e:
		print e
	finally:
		return cursor


def createTable(tableName, hashset):
	global conn

	command = "CREATE TABLE IF NOT EXISTS %s (" % tableName
	for key, value in hashset.iteritems():
		command += key + " varchar(30), "
	command = command[0: len(command) - 2] + ");"
	performQuery(command)


def insertIntoTable(tableName, hashset):
	global conn
	keys = values = ""

	for key, value in hashset.iteritems():
		keys += key + ", "
		values += "\"" + value + "\", "

	keys = keys[0: len(keys) - 2]
	values = values[0: len(values) - 2]

	command = "INSERT INTO %s(%s) values(%s);" % (tableName, keys, values)
	performQuery(command)
	conn.commit()


################################################################################


def performSSHConnection(server, uname, passwd, command):
	result = ""

	try:
		ssh = paramiko.SSHClient()
		ssh.load_system_host_keys()
		ssh.set_missing_host_key_policy (paramiko.WarningPolicy)

		ssh.connect (server, username=uname, password=passwd)

		ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command (command)
		result = ssh_stdout.read()
	except Exception as e:
		print e
	finally:
		ssh.close()
		return result


################################################################################



def getPropertiesFromTable(tableName, field, condition):
	command = "SELECT %s FROM %s WHERE inode = %s;" % (field, tableName, condition)
	cursor = performQuery(command)
	row = cursor.fetchall()

	result = ""
	if len (row) != 0:
		result = str (((row[0])[0]).encode ('ascii', 'ignore'))
	
	return result


def updateRecord(tableName, field, new_value, condition):
	global conn

	command = "UPDATE %s SET %s = \"%s\" WHERE inode = %s;" % (tableName, field, new_value, condition)
	performQuery(command)
	conn.commit()


def checkForChanges(tableName, actual_result):

	global_changes = False
	for line in actual_result:
		changed = False

		for key, value in line.iteritems():
			properties = getPropertiesFromTable(tableName, key, line["inode"]) 
			
			if properties == "":
				print "Insert new record corresponding to inode = %s" % line["inode"]
				changed = True
				insertIntoTable(tableName, line)
				break

			elif value != properties:
				changed = True
				updateRecord (tableName, key, value, line["inode"])

		if  changed == True:
			global_changes = True
			print "Found differences corresponding to inode = %s" % line["inode"] 

	if global_changes == False:
		print "No changed at all !"

################################################################################




def run(server, uname, passwd):
	# connect via ssh
	command = "ls -li /root"
	result = performSSHConnection(server, uname, passwd, command)
	print result

	# parse resulted output 
	parsed_result = parseSSHResult (result)
	if parsed_result == []:
		print "No files in the given directory"
		sys.exit (1)

	# add info into the database
	tableName = "SSH_Table"
	db_connect()
	createTable(tableName, parsed_result[0])
	checkForChanges(tableName, parsed_result)

	# do it periodically
	thread = threading.Timer(10, function=run, args=(server, uname, passwd))
	thread.start()
	thread.join()
	

if __name__ == "__main__":

	if len (sys.argv) != 4:
		print "Usage: pyhthon remote.py <hostname> <username> <password>"
		sys.exit (1)

	server = sys.argv[1]
	uname = sys.argv[2]
	passwd = sys.argv[3]

	if server == "" or uname == "" or passwd == "" :
		print "Invalid arguments"
		sys.exit (1)

	run (server, uname, passwd)

