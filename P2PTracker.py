import socket
import argparse
import threading
import sys
import hashlib
import time
import logging


#TODO: Implement P2PTracker
print("print test")
FORMAT = 'utf-8'
chunks_known = dict()
logging.basicConfig(filename="logs.log", level=logging.DEBUG, format='%(message)s', filemode='a')
logger = logging.getLogger()
clients = []
def format_ip(ip_address):
    return "localhost" if ip_address == "127.0.0.1" else ip_address
def handle_client(conn, addr):
    conn.send("Connected".encode(FORMAT))
    buffer = ""
    while True:
        try:
            data = conn.recv(2048).decode(FORMAT)
            if not data:
                if buffer:  
                    process_message(buffer, conn)
                break  
            
            buffer += data
            if '\n' in buffer:
                while '\n' in buffer:
                    message, _, buffer = buffer.partition('\n')
                    #logger.info(f"P2PTracker,{message}")
                    process_message(message, conn)
            else:
                process_message(buffer, conn)
                buffer = ""  

        except socket.error as e:
            print(f"Socket error: {e}")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break
            
                
def process_message(message, conn): 
    parts = message.split(',')
    if message.startswith('LOCAL_CHUNKS'):
        #logger.info(f"P2PTracker,{message}")
        if len(parts) == 4:
            _, chunk_idx, ip_addr, port_number = parts
            if chunk_idx not in chunks_known:
                chunks_known[chunk_idx] = []
            chunks_known[chunk_idx].append((ip_addr, port_number))
        else:
            logger.error(f"Received malformed LOCAL_CHUNKS message: {message}")
    elif message.startswith('WHERE_CHUNK'):
        #print("Received WHERE_CHUNK message")
        if len(parts) == 2:
            print("hello")
            #logger.info(f"P2PTracker,{message}")
            _, chunk_idx = parts
            if chunk_idx in chunks_known:
                peers_info = ','.join([f"{format_ip(peer_ip)},{peer_port}" for peer_ip, peer_port in chunks_known[chunk_idx]])
                response_message = f"GET_CHUNK_FROM,{chunk_idx},{peers_info}"
                print(response_message)
                conn.send(response_message.encode(FORMAT))
                logger.info(f"P2PTracker,GET_CHUNK_FROM,{chunk_idx},{peers_info}")
            else:
                response_message = f"CHUNK_LOCATION_UNKNOWN,{chunk_idx}"
                conn.send(response_message.encode(FORMAT))
                logger.info(f"P2PTracker,CHUNK_LOCATION_UNKNOWN,{chunk_idx}")
        else:
            logger.error(f"Received malformed WHERE_CHUNK message: {message}")
                    
        

def start(server):
    server.listen()
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args = (conn, addr))
        thread.start()

port = 5100

if __name__ == "__main__":
    s_socket = socket.socket()
    s_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s_socket.bind(("", port))
    print("Running")
    sys.stdout.flush()
    start(s_socket)
		
        