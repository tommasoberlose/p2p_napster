import socket
import hashlib
import string
import threading
import os
import random
import sys
import shutil

# Variabile di sessione col server
global sessionID

################ Inizio Server del peer ################

# Funzione che definisce il comportamento del thread server
def daemon(myHost):
	
	s = None
	for res in socket.getaddrinfo(myHost, 3000, socket.AF_UNSPEC,socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
	    af, socktype, proto, canonname, sa = res
	    try:
	        s = socket.socket(af, socktype, proto)
	    except socket.error as msg:
	        s = None
	        continue
	    try:
	        s.bind(sa)
	        s.listen(5)
	    except socket.error as msg:
	        s.close()
	        s = None
	        continue
	    break
	if s is None:
		write_daemon_text(myHost, 'Error: Daemon could not open socket in upload on ' + myHost)
		sys.exit(1)
	#write_daemon_text(myHost, 'Start Daemon')
	while 1:
		conn, addr = s.accept()
		write_daemon_text(myHost, 'Connected by ' + addr[0])
		ricevutoByte = conn.recv(1024)
		if not ricevutoByte:
			break
		md5 = ricevutoByte[4:36]
		fileName = searchName(md5)
		upload(fileName, conn, myHost)
		conn.close()
		
	write_daemon_text(myHost, 'End Daemon')
	s.close()

# Avvio del demone che in background gestisce le connessioni per l'upload
print("\n\t***Inserimento del proprio IP***\n")
nElGroup = input("Inserisci il tuo numero all'interno del gruppo: ")
if int(nElGroup) < 10:
	nElGroup = "0" + nElGroup
ipv4 = "172.030.002.0" + nElGroup
ipv6 = "fc00:0000:0000:0000:0000:0000:0002:00" + nElGroup
daemonThreadv6 = threading.Thread(target=daemon, args=(ipv6, ))
daemonThreadv4 = threading.Thread(target=daemon, args=(ipv4, ))
daemonThreadv6.start()
daemonThreadv4.start()				

################ Inizio funzioni Client ################

# Funzione di login
def login(nEl):
	pack = "LOGI172.030.002.0" + nEl + "|fc00:0000:0000:0000:0000:0000:0002:00" + nEl + "03000" 
	s.sendall(bytes(pack, "UTF-8"))
	ricevutoByte = s.recv(1024)
	sessionID = ricevutoByte[4:20]
	print ("Inviato: ", pack, "\nRicevuto: ", sessionID.decode("ascii"))
	return sessionID

# Funzione di aggiunta
def add_file(nomeFile, sessionID):
	# Controllo esistenza file
	if os.path.exists("FileCondivisi/" + nomeFile):
		md5File = hashlib.md5(open(("FileCondivisi/" + nomeFile),'rb').read()).hexdigest()
		print ("MD5: ", md5File)
		nSpazi = 100 - len(nomeFile)
		nomeFileTot = nomeFile + " " * nSpazi
		pack = bytes("ADDF","ascii") + sessionID + bytes(md5File, "ascii") + bytes(nomeFileTot, "ascii")
		print ("Inviato: ", pack) 
		s.sendall(pack)
		add_element(md5File, nomeFile)
		ricevutoByte = s.recv(1024)
		nCopy = ricevutoByte[4:7]
		print ("Numero di copie:", nCopy.decode("ascii"))
	else:
		error("file_not_exists")

# Funzione di rimozione
def rem_file(nomeFile, sessionID):
	# Controllo esistenza file
	if os.path.exists("FileCondivisi/" + nomeFile):
		md5File = hashlib.md5(open(("FileCondivisi/" + nomeFile),'rb').read()).hexdigest()
		print ("MD5: ", md5File)
		pack = bytes("DELF","ascii") + sessionID + bytes(md5File, "ascii")
		print ("Inviato: ", pack)
		s.sendall(pack)
		rem_element(md5File)
		ricevutoByte = s.recv(1024)
		nCopy = ricevutoByte[4:7]
		if nCopy == bytes("999", "ascii"):
			print("Il file non è stato rimosso poichè non esisteva.")
		else:
			print ("Il file è stato rimosso.")
	else:
		error("file_not_exists")


# Funzione di ricerca
def search(query, sessionID, ipD):
	nSpazi = 20 - len(query)
	queryTot = query + " " * nSpazi
	pack = bytes("FIND", "ascii") + sessionID + bytes(queryTot, "ascii")
	print ("Inviato: ", pack.decode("ascii"))
	s.sendall(pack)
	ricevutoByte = s.recv(4096)
	print ("RicevutoByte: ", ricevutoByte)

	nIdmd5 = int(ricevutoByte[4:7])
	if(nIdmd5 != 0):
		pointer = 7
		id = 0
		listFile = []


		for j in range(0, nIdmd5):
			md5 = ricevutoByte[pointer:pointer + 32]
			nomeFile = ricevutoByte[pointer + 32:pointer + 132]
			nCopy = int(ricevutoByte[pointer + 132:pointer + 135])

			pointer = pointer + 135

			for i in range(0, nCopy):
				ip = ricevutoByte[pointer:pointer + 55]
				port = ricevutoByte[pointer + 55:pointer + 60]
				id = id + 1
				pointer = pointer + 60
				fixList = [id, md5, nomeFile, ip, port]
				listFile.append(fixList)

		print ("\n\nLista file disponibili: \n")
		print (listFile)
		
		selectId = input("\nInserire il numero di file che vuoi scaricare (0 per uscire): ")
		
		if(selectId != "0"):
			for i in range (0, id):
				if listFile[i][0] == int(selectId):
					selectFile = listFile[i]
					break

			download(sessionID, selectFile, ipD)

	else:
		error("file_not_exists")

# Funzione di download
def download(sessionID, selectFile, ipD):	

	print ("Il file selezionato ha questi parametri: ", selectFile)

	md5 = selectFile[1]
	nomeFile = selectFile[2]
	ip = selectFile[3]
	port = selectFile[4]

	# Con probabilità 0.5 invio su IPv4, else IPv6
	ip = roll_the_dice(ip.decode("ascii"))
	print(ip)

	# Mi connetto al peer

	sP = None
	for res in socket.getaddrinfo(ip, int(port), socket.AF_UNSPEC, socket.SOCK_STREAM):
	    af, socktype, proto, canonname, sa = res
	    try:
	        sP = socket.socket(af, socktype, proto)
	    except socket.error as msg:
	        sP = None
	        continue
	    try:
	        sP.connect(sa)
	    except socket.error as msg:
	        sP.close()
	        sP = None
	        continue
	    break
	if sP is None:
	    print ('Error: could not open socket in download')
	    sys.exit(1)

	pack = bytes("RETR", "ascii") + md5
	sP.sendall(pack)
	ricevutoHeader = sP.recv(10)
	nChunk = int(ricevutoHeader[4:10])

	print(ricevutoHeader)

	ricevutoByte = b''

	i = 0
	
	while i != nChunk:
		ricevutoLen = sP.recv(5)
		print(ricevutoLen)
		while (len(ricevutoLen) < 5):
			ricevutoLen = ricevutoLen + sP.recv(5 - int(ricevutoLen))
		buff = sP.recv(int(ricevutoLen))
		while(len(buff) < int(ricevutoLen)):
			buff = buff + sP.recv(int(ricevutoLen) - len(buff))
		ricevutoByte = ricevutoByte + buff
		print(len(buff), buff)
		i = i + 1

	sP.close()

	print ("Il numero di chunk è: ", nChunk)

	""""pointer = 0

	data = []

	for i in range(1, nChunk+1):
		l = 1024
		if i == nChunk:
			l = int(ricevutoLen)
		data.append(ricevutoByte[pointer:pointer + l]) 
		pointer = pointer + l

	fileReceived = bytes(b''.join(data))"""
	
	# Salvare il file data
	open(("Download/" + nomeFile.decode("ascii")),'wb').write(ricevutoByte)

	# connessione con la directory per comunicare informazioni

	pack = bytes("DREG", "ascii") + sessionID + md5
	s.sendall(pack)
	ricevutoByte = s.recv(1024)
	nDownload = int(ricevutoByte[4:9])
	print ("Inviato: ", pack, "\nIl file è stato scaricato ", nDownload, " volte.")

# Funzione di upload dei file
def upload(nomeFile, ss, myHost):
	write_daemon_text(myHost, "DAEMONTHREAD WARNING - Start Upload di: " + nomeFile.decode("ascii"))
	f = open(("FileCondivisi/" + nomeFile.decode("ascii")), 'rb')

	fileLength = os.stat("FileCondivisi/" + nomeFile.decode("ascii")).st_size
	nChunk = int(fileLength / 1024) + 1 

	dimChunk = "0" * (6 - len(str(nChunk))) 
	pack = bytes("ARET", "ascii") + bytes(dimChunk + str(nChunk), "ascii")
	ss.sendall(pack)

	write_daemon_text(myHost, "Inizio invio File")
	i = 0
	while True:
		line = f.read(1024)
		dimLine = "0" * (5 - len(str(len(line))))
		pack = bytes(dimLine + str(len(line)), "ascii") + line
		ss.sendall(pack)
		#print(pack)
		i = i + 1
		if i == nChunk:
			break
	write_daemon_text(myHost, "Fine invio File")


def logout(sessionID):
	pack = bytes("LOGO", "ascii") + sessionID
	s.sendall(pack)
	ricevutoByte = s.recv(1024)
	nFileDeleted = ricevutoByte[4:7].decode("ascii")
	print ("Inviato: ", pack, "\nFile eliminati: ", nFileDeleted)

def error(code):
	if (code == "directory"):
		print ("\nErrore nella connessione alla directory.")
	if (code == "wrong_choice"):
		print ("\nErrore nella scelta dell'azione.")
	if (code == "file_not_exists"):
		print ("\nErrore, file non esistente.")

def roll_the_dice(ip):
	#return random.choice([ip[0:15], ip[16:55]])
	return ip[0:15] 

def	write_right_text(text):
	print(str(text).rjust(shutil.get_terminal_size((80, 20))[0] - 5))

def write_daemon_text(host, text):
	write_right_text("\n")
	write_right_text("Daemon connected on " + host)
	write_right_text(text)

################ FUNZIONI GESTIONE FILE ################

# Funzioni di aggiunta file in elenco.txt
def add_element(md5, nomeFile):
	nSpazi = 100 - len(nomeFile)
	nomeFileTot = nomeFile + " " * nSpazi
	if os.path.exists("elenco.txt"):
		open(("elenco.txt"),'ab').write(bytes(md5, "ascii") + bytes(nomeFileTot, "ascii"))
	else:
		open(("elenco.txt"),'wb+').write(bytes(md5, "ascii") + bytes(nomeFileTot, "ascii"))


# Funzione di rimozione file da elenco.txt
def rem_element(md5):
	lista = []
	ramLista = []
	nuovaLista = []

	text = open("elenco.txt",'rb+').read()
	sizeFile = len(text)
	
	pointer = 0

	for i in range(sizeFile):
		md5File = text[pointer:pointer + 32]
		nomeFile = text[pointer + 32:pointer + 132]
		ramLista = [md5File, nomeFile]
		# print(md5File, md5)
		if md5File != md5: 
			lista.append(ramLista)
		pointer = pointer + 132

	text = open("elenco.txt",'wb+')

	for i in range(len(lista)):
		riga = bytes(b''.join([lista[i][0], lista[i][1]]))
		text.write(riga)

	text.close()

# Funzione di ricerca di un nome di file in elenco.txt
def searchName(md5):

	fileT = open("elenco.txt",'rb')
	text = fileT.read()

	sizeFile = os.stat("elenco.txt").st_size
	
	pointer = 0

	for i in range(sizeFile):
		md5File = text[pointer:pointer + 32]
		nomeFile = text[pointer + 32:pointer + 132]
		if md5File == md5: 
			nomeFileTrovato = nomeFile
		pointer = pointer + 132

	fileReturn =  nomeFileTrovato.strip();
 
	print("Il nome del file collegato a ", md5, " è ", fileReturn)

	fileT.close()
	
	return fileReturn



################ Inizio programma Client ################

# Mi connetto a una directory, inserire porta 3000
print("\n\t***Connessione alla Directory***\n")
nGroup = input("Inserire il numero del gruppo: ")
nElement = input("Inserire il numero dell'elemento del gruppo: ")
if int(nGroup) < 10:
	nGroup = "0" + nGroup
host = roll_the_dice("172.030.0" + nGroup + ".00" + nElement + "|fc00:0000:0000:0000:0000:0000:00" + nGroup + ":000" + nElement)

s = None
for res in socket.getaddrinfo(host, 3000, socket.AF_UNSPEC, socket.SOCK_STREAM):
    af, socktype, proto, canonname, sa = res
    try:
        s = socket.socket(af, socktype, proto)
    except socket.error as msg:
        s = None
        continue
    try:
        s.connect(sa)
    except socket.error as msg:
        s.close()
        s = None
        continue
    break
if s is None:
    print ('Error: could not open socket')
    sys.exit(1)

sessionID = login(nElGroup)
if (sessionID == ("0" * 16)):
	error("directory")

# Menù di interazione
while True:
	choice = input("\n\nScegli azione:\na - Add File\nr - Remove File\nd - Search and Download File\nq - Quit\n\nScelta: ")

	if (choice == "a"):
		nomeFile = input("\n\nInserisci il nome del file da aggiungere: ")
		add_file(nomeFile, sessionID)

	elif (choice == "r"):
		nomeFile = input("\n\nInserisci il nome del file da rimuovere: ")
		rem_file(nomeFile, sessionID)

	elif (choice == "d"):
		query = input("\n\nInserisci il nome del file da cercare: ")
		search(query, sessionID, host)

	elif (choice == "q"):
		logout(sessionID)
		print ("\n\nLogout eseguito con successo, a presto.")
		s.close()
		break

	else:
		error("wrong_choice")
