import uuid
import logging
import sys
sys.path.append('../')
from database.database import Database
from database.group import GroupMessage
from database.private import PrivateMessage
from database.file import FileMessage
import base64
import os
from os.path import join, dirname, realpath
from datetime import datetime
from uuid import uuid4
import socket
import json




class Chat:
    def __init__(self):
        # databases
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = ("localhost", 8080)
        self.socket.connect(self.server_address)
        self.realms = []
        self.sessions = {}
        self.server_id =  uuid4()

    def get_realms_from_db(self):
        return self.realms
    
    def send_realms_to_db(self):
        #Should add process to talk with db
        return

    def get_realm_id(self):
        return self.server_id
    
    def proses(self, data, server_id):
        self.server_id = server_id
        j = data.split(" ")
        try:
            command = j[0].strip()
            if (command == 'register'):
                username = j[1].strip()
                password = j[2].strip()
                payload = {
                    'username': username,
                    'password': password
                }
                return self.register_user(payload)
            elif (command == 'auth'):
                username = j[1].strip()
                password = j[2].strip()
                payload = {
                    'username': username,
                    'password': password
                }
                return self.autentikasi_user(payload)
            elif (command == 'sendprivate'):
                sessionid = j[1].strip()
                usernameto = j[2].strip()

                message = ""
                for w in j[3:]:
                    message = "{} {}" . format(message, w)
                usernamefrom = self.sessions[sessionid]['username']
                payload = {
                    'sessionid': sessionid,
                    'usernameto': usernameto,
                    'usernamefrom': usernamefrom,
                    'message': message
                }
                return self.send_message(payload)
            elif (command == 'sendgroup'):
                sessionid = j[1].strip()
                groupto = j[2].strip()
                message = ""
                for w in j[3:]:
                    message = "{} {}" . format(message, w)
                usernamefrom = self.sessions[sessionid]['username']
                payload = {
                    'sessionid': sessionid,
                    'groupto': groupto,
                    'usernamefrom': usernamefrom,
                    'message': message
                }
                return self.send_message_group(payload)
            elif (command == 'sendfile'):
                sessionid = j[1].strip()
                usernameto = j[2].strip()
                encoded_content = j[3].strip()
                filepath = j[4].strip()
                usernamefrom = self.sessions[sessionid]['username']
                payload= {
                    'sessionid': sessionid,
                    'usernameto': usernameto,
                    'filepath': filepath,
                    'usernamefrom': usernamefrom, 
                    'encoded_content': encoded_content,
                }
                return self.send_file(payload)
            elif (command == 'receivefile'):
                sessionid = j[1].strip()
                username = self.sessions[sessionid]['username']
                payload = {
                    'username': username,
                }
                return self.receive_file(payload)
            elif(command == 'creategroup'):
                groupname = j[1].strip()
                payload = {
                    'groupname': groupname
                }
                return self.register_group(payload)
            elif(command == 'joingroup'):
                sessionid = j[1].strip()
                groupname = j[2].strip()
                realmid = j[3].strip()
                username = self.sessions[sessionid]['username']
                payload = {
                    'sessionid': sessionid,
                    'groupname': groupname,
                    'realmid': realmid,
                    'username': username,
                }
                return self.join_group(payload)
            elif (command == 'inboxgroup'):
                sessionid = j[1].strip()
                groupname = j[2].strip()
                username = self.sessions[sessionid]['username']
                payload = {
                    'sessionid': sessionid,
                    'groupname': groupname,
                    'username': username
                }
                return self.get_inbox_group(payload)
            elif (command == 'getallusers'):
                return self.get_users()
            elif (command == 'inboxbysender'):
                sessionid = j[1].strip()
                username = self.sessions[sessionid]['username']
                sender = j[2].strip()
                return self.get_inbox_by_sender(username, sender)
            elif (command == 'getallgroups'):
                sessionid = j[1].strip()
                return self.get_groups(sessionid)
            else:
                return {'status': 'ERROR', 'message': '**Protocol Tidak Benar'}
        except KeyError:
            return {'status': 'ERROR', 'message': 'Informasi tidak ditemukan'}
        except IndexError:
            return {'status': 'ERROR', 'message': '--Protocol Tidak Benar'}

    def get_groups(self, sessionid):
        username = self.sessions[sessionid]['username']
        self.socket.send(f'getallgroups\r\nusername:{username}\r\n'.encode())
        return self.socket.recv(100000).decode('utf-8')
    def get_users(self):
        self.socket.send(f'getallusers\r\n'.encode())
        return self.socket.recv(100000).decode('utf-8')
    
    def get_inbox_by_sender(self, username, sender):
        self.socket.send(f'inboxbysender\r\nusername:{username}\r\nsender:{sender}\r\n'.encode())
        return self.socket.recv(4096).decode('utf-8')
    
    def autentikasi_user(self, payload):
        #TODO: send to main server to check if user exists
        username = payload['username']
        password = payload['password']
        self.socket.send(f'auth\r\nusername:{username}\r\npassword:{password}\r\n'.encode())

        data = json.loads(self.socket.recv(4096).decode('utf-8'))
        if (data['status'] != 'ERROR'):
            tokenid = data['token_id']
            self.sessions[tokenid] = {
                'username': username
            }
        return json.dumps(data)
    
    def register_user(self, payload):
        username = payload['username']
        password = payload['password']
        self.socket.send(f'register\r\nusername:{username}\r\npassword:{password}\r\nrealm_id:{self.server_id}\r\n'.encode())
        return self.socket.recv(4096).decode('utf-8')
    
    def join_group(self, payload):
        username = payload['username']
        realm_id = payload['realmid']
        groupname = payload['groupname']
        self.socket.send(f'joingroup\r\nusername:{username}\r\ngroupname:{groupname}\r\nrealm_id:{realm_id}\r\n'.encode())
        return self.socket.recv(4096).decode('utf-8')
    
    
    def register_group(self, payload):
        groupname = payload['groupname']
        self.socket.send(f'creategroup\r\ngroupname:{groupname}\r\n'.encode())
        return self.socket.recv(4096).decode('utf-8')

    def send_message(self, payload):
        if (payload['sessionid'] not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}

        usernamefrom = payload['usernamefrom']
        usernameto = payload['usernameto']
        message = payload['message']
        self.socket.send(f'sendprivate\r\nusername_from:{usernamefrom}\r\nusername_to:{usernameto}\r\nmessage:{message}\r\n'.encode())
        data = self.socket.recv(4096).decode('utf-8')
        return data
    
    def send_file(self, payload):
        if (payload['sessionid'] not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}


        usernameto = payload['usernameto']
        usernamefrom = payload['usernamefrom']
        encoded_content = payload['encoded_content']
        filename = os.path.basename(payload['filepath'])
                        

        #PAYLOAD SEND MESSAGE FILE
        status = self.socket.send(f'sendfile\r\nusernamefrom:{usernamefrom}\r\nusernameto:{usernameto}\r\nencoded_content:{encoded_content}\r\nfilename:{filename}\r\n'.encode())
        return self.socket.recv(4096).decode('utf-8')
    
    def receive_file(self, payload):

        username = payload['username']

        self.socket.send(f'receivefile\r\nusername:{username}\r\n'.encode())

        data = self.socket.recv(10000000).decode('utf-8')
        return data
    

    def send_message_group(self, payload):
        groupto = payload['groupto']
        usernamefrom = payload['usernamefrom']
        message = payload['message']
        if (payload['sessionid'] not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}

        #PAYLOAD SEND MESSAGE GROUP
        self.socket.send(f'sendgroup\r\nusernamefrom:{usernamefrom}\r\ngroupto:{groupto}\r\nmessage:{message}\r\n'.encode())

        return self.socket.recv(4096).decode('utf-8')
    
    def get_inbox_by_sender(self, username, sender):
        self.socket.send(f'inbox\r\nusername:{username}\r\nsender:{sender}\r\n'.encode())
        return self.socket.recv(4096).decode('utf-8')

    def get_inbox_group(self, payload):
        #PAYLOAD CHECK IF USER IN GROUP
        groupname = payload['groupname']
        username = payload['username']
        if (payload['sessionid'] not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}

        #PAYLOAD GET MESSAGE IN GROUP
        self.socket.send(f'inboxgroup\r\nusername:{username}\r\ngroupname:{groupname}\r\n'.encode())
        return self.socket.recv(4096).decode('utf-8')
        
    @staticmethod
    def list_messages(msgs):
        messages = ''
        for msg in msgs:
            messages +=  '['+ msg['sender'] + ': ' + msg['message'] + '], '
        return messages
        




if __name__ == "__main__":
    j = Chat()
    sesi = j.proses("auth messi surabaya")
    print(sesi)
    # sesi = j.autentikasi_user('messi','surabaya')
    # print sesi
    tokenid = sesi['tokenid']
    print(j.proses("send {} henderson hello gimana kabarnya son " . format(tokenid)))
    print(j.proses("send {} messi hello gimana kabarnya mess " . format(tokenid)))

    # print j.send_message(tokenid,'messi','henderson','hello son')
    # print j.send_message(tokenid,'henderson','messi','hello si')
    # print j.send_message(tokenid,'lineker','messi','hello si dari lineker')

    print("isi mailbox dari messi")
    print(j.get_inbox('messi'))
    print("isi mailbox dari henderson")
    print(j.get_inbox('henderson'))
