import socket

s = socket.socket()

s.bind(("localhost", 9999))
s.listen(1)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sc, addr = s.accept()

for i in range(3):
	ricevutoByte = sc.recv(4096)
	#ricevuto = str(ricevutoByte, "ascii")
	#print("Ricevuto:", ricevuto)
	if ricevutoByte == bytes("q","ascii") or ricevutoByte == None:
		break
	command = ricevutoByte[0:4]
	if command == bytes("FIND", "ascii"):
		ricevutoByte = bytes("AFIN003"+"0"*16+"a"*99+"1"+"002"+"192.168.001.001|fc00"+":1000"*7+"12345"+"192.168.001.002|fc00"+":2000"*7+"12345"+"0"*16+"a"*99+"2"+"001"+"192.168.001.003|fc00"+":3000"*7+"12345", "UTF-8")
		#ricevutoByte = bytes("AFIN001"+"0"*16+"a"*99+"1"+"002"+"192.168.001.001|fc00"+":1000"*7+"12345", "UTF-8")
	sc.send(ricevutoByte)

print("Shutdown")
sc.close()
s.close()
