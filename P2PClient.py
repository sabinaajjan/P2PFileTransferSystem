import socket
import argparse
import threading
import sys
import hashlib
import time
import logging


#TODO: Implement P2PClient that connects to P2PTracker

logging.basicConfig(filename="logs.log", level=logging.DEBUG, format='%(message)s', filemode='a')
logger = logging.getLogger()
parser = argparse.ArgumentParser(description="P2P Client")
parser.add_argument('-folder', type=str, required=True, help='Path to folder to read from' )
parser.add_argument('-transfer_port', type=int,required=True, help='Port number of the P2PClient')
parser.add_argument('-name', type=str, required=True, help='Name of the P2PClient')
args = parser.parse_args()
FORMAT = 'utf-8'
#client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#client.connect(("localhost", 5100))
TRACKER_ADDRESS = ('localhost', 5100)
stop_event = threading.Event()
def format_ip(ip_address):
    return "localhost" if ip_address == "127.0.0.1" else ip_address

def receive_messages(client_socket):
    while not stop_event.is_set():
        try:
            message = client_socket.recv(2048).decode(FORMAT)
        except socket.error as s:
            if not stop_event.is_set():
                print(f"A socket error occurred: {s}")
                sys.stdout.flush()
            break
        except Exception as e:
            if not stop_event.is_set():
                print(f"An error occurred: {e}")
                sys.stdout.flush()
            break
        
        
def read_local_chunks(folder):
    chunks = []
    total_chunks = 0
    with open(f"{folder}/local_chunks.txt", "r") as file:
        for line in file:
            chunk_index, message = line.strip().split(',')
            if message != 'LASTCHUNK':
                chunks.append(chunk_index)
            else:
                total_chunks = int(chunk_index)
    return chunks, total_chunks


def register_with_tracker(client_socket, local_chunks):
    for chunk in local_chunks:
        message = f"LOCAL_CHUNKS,{chunk},{format_ip(client_socket.getsockname()[0])},{args.transfer_port}"
        logger.info(f"{args.name},LOCAL_CHUNKS,{chunk},{format_ip(client_socket.getsockname()[0])},{args.transfer_port}")
        send_message(client_socket, message)
        time.sleep(1)
        


def handle_peer_request(connection, address, local_chunks, folder):
   #try:
    while True: 
        data = connection.recv(2048).decode(FORMAT)
        if data:
      
            parts = data.split(',')
            print("parts at 0: " + str(parts[0]))
            if parts[0] == 'REQUEST_CHUNK':
                chunk_index = parts[1]
                chunk_index = str(chunk_index)
                found = False
                for i in local_chunks:
                    if int(chunk_index) == int(i):
                        found = True
                if found:
                    print("If chunk_index is in local_chunks")
                    filename = f"{folder}/chunk_{chunk_index.strip()}"
                    send_file_to_peer(connection, filename)
                    print("AFTER SENDING FILE")
    #finally:
        #connection.close()
        
        
        
def request_chunk_from_peer(peer_ip, peer_port, chunk_index, folder):
    try:
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_socket.connect((peer_ip, int(peer_port)))
        send_message(peer_socket, f"REQUEST_CHUNK,{chunk_index}")
        time.sleep(1)
        logger.info(f"{args.name},REQUEST_CHUNK,{chunk_index},localhost,{peer_port}")
        
        
        print("AFTER RECEIVING FILE DATA")
    
        filename = f"{folder}/chunk_{chunk_index}"
        with open(filename, "ab") as chunk_file:
            chunk_data = peer_socket.recv(2048)
            while chunk_data:
                chunk_file.write(chunk_data)
                print("AFTER WRITING")
                try:
                    chunk_data = peer_socket.recv(2048)
                except:
                    break
        peer_socket.shutdown(peer_socket.SHUT_RDWR)
        peer_socket.close()
        return True
    except Exception as e:
                logger.error('Exception writing file')
        #finally:
            #peer_socket.close()
    return False
        
    
        
        

            
    
    


def send_message(client_socket, message):
    client_socket.send(message.encode(FORMAT))
    
def send_file_to_peer(socket, file_path):
    with open(file_path, 'rb') as f:
        while f.readable():
    
            file_data = f.read(1024)
            if not file_data:
                #socket.shutdown(socket.SHUT_RDWR)
                #socket.close()
                return
            socket.send(file_data)
    
    #file_length = len(file_data)
    #socket.sendall(file_length.to_bytes(8, byteorder='big'))
    #time.sleep(0.1)
    
    #time.sleep(0.1)
    
def close_socket(sock):
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except socket.error as e:
        logger.error(f"Error shutting down socket: {e}")
    finally:
        sock.close()
    

def handle_client_connection(client_socket, address):
    try:
        while not stop_event.is_set():
            data = client_socket.recv(2048).decode(FORMAT)
            if data:
                pass  
    finally:
        close_socket(client_socket)
        
        
    #finally:
        #client_socket.close()
        
def start_server(local_chunks, folder):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   
    try:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('', args.transfer_port))
        server_socket.listen(10)
        while True:
            try:
                conn, addr = server_socket.accept()
                #handle_peer_request(conn, addr, local_chunks, folder)
    
                threading.Thread(target=handle_peer_request, args=(conn, addr, local_chunks, folder)).start()
            except Exception as e:
                print('Exception')
    finally:
        server_socket.shutdown(server_socket.SHUT_RDWR)
        server_socket.close()




if __name__ == "__main__":
    local_chunks, total_chunks = read_local_chunks(args.folder)
    threading.Thread(target=start_server, args=(local_chunks, args.folder),daemon=True).start()
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_sock.connect((TRACKER_ADDRESS)) 
        while True:
            #response = client_sock.recv(2048).decode('utf-8') 
            #print(response)
            #sys.stdout.flush()
            #if response == "Connected": 
                #print(f"Connected to server on port 5100") 
                #sys.stdout.flush()
            register_with_tracker(client_sock, local_chunks)
            #response = client_sock.recv(2048).decode('utf-8') 
            missing_chunks = {str(i) for i in range(1, total_chunks + 1) if str(i) not in local_chunks}
            while missing_chunks:
                for chunk_index in missing_chunks.copy():
                    logger.info(f"{args.name},WHERE_CHUNK,{chunk_index}")
                    send_message(client_sock, f"WHERE_CHUNK,{chunk_index}")
                    #time.sleep(0.1)
                    
                    response = client_sock.recv(2048).decode(FORMAT)
                    parts = response.split(',')
                    print(parts)
                    command = parts[0]
                    if command == 'GET_CHUNK_FROM':
                        _, _, peer_ip, peer_port = parts[0:4]
                        if request_chunk_from_peer(peer_ip.strip(), peer_port.strip(), chunk_index, args.folder):
                            missing_chunks.remove(chunk_index)
                            #missing_chunks.append(chunk_index)
                            register_with_tracker(client_sock, [chunk_index])
                            local_chunks.append(chunk_index)
                            #logger.info(f"{args.name},LOCAL_CHUNKS,{chunk_index}, {format_ip(client_sock.getsockname()[0])}, {args.transfer_port}")
                    elif response.startswith('CHUNK_LOCATION_UNKNOWN'):
                            #logger.info(f"P2PTracker,{response}")
                            pass
    
                            
                time.sleep(1)
                        
          		
				
    except socket.error as e: 
        print(f"Connection error: {e}") 
    finally: 
        client_sock.close()
            #if not stop_event.is_set():
                #stop_event.set()
                #client_sock.close()
			
      
		

			

		
