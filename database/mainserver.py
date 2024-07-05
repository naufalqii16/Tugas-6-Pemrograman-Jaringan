from socket import *
import socket
import threading
import json
import logging
import sys
# sys.path.append('../')
from database import Database
from group import GroupMessage
from private import PrivateMessage
from file import FileMessage
import os 
from os.path import join, dirname, realpath
import datetime
import uuid
import base64

class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address, user_db, group_db, group_user_db, private_message_db, group_message_db, file_message_db):
        self.connection = connection
        self.address = address
        self.user_db = user_db
        self.group_db = group_db
        self.group_user_db = group_user_db
        self.private_message_db = private_message_db
        self.group_message_db = group_message_db
        self.file_message_db = file_message_db
        threading.Thread.__init__(self)

    def run(self):
        rcv = ""
        while True:
            data = self.connection.recv(4096)
            if data:
                d = data.decode('utf-8')
                rcv = rcv+d
                if rcv[-2:] == '\r\n':
                    # end of command, proses string
                    logging.warning("data dari client: {}" . format(rcv))
                    hasil = json.dumps(self.proses(rcv))
                    logging.warning("balas ke  client: {}" . format(hasil))
                    self.connection.sendall(hasil.encode('utf-8'))
                    rcv = ""
            else:
                break
        self.connection.close()
    
    def proses(self, data):
        j = data.split("\r\n")
        try:
            command = j[0].strip()
            if (command == 'register'):
                username = j[1].strip()
                password = j[2].strip()
                server_id = j[3].strip()
                logging.warning(
                    "REGISTER: register {} {}" . format(username, password))
                return self.register_user(username, password, server_id)
            elif (command == 'auth'):
                username = j[1].strip()
                password = j[2].strip()
                logging.warning(
                    "AUTH: auth {} {}" . format(username, password))
                return self.autentikasi_user(username, password)
            elif (command == 'sendprivate'):
                usernamefrom = j[1].strip()
                usernameto = j[2].strip()
                message = j[3]
                logging.warning("SEND: send message from {} to {}" . format(
                    usernamefrom, usernameto))
                return self.send_message(usernamefrom, usernameto, message)
            elif (command == 'sendgroup'):
                usernamefrom = j[1].strip()
                groupto = j[2].strip()
                message = j[3]
                logging.warning("SEND GROUP: send message from {} to {}" . format(
                    usernamefrom, groupto))
                return self.send_message_group(usernamefrom, groupto, message)
            elif (command == 'sendfile'):
                usernamefrom = j[1].strip()
                usernameto = j[2].strip()
                encoded_content = j[3].strip()
                filename = j[4].strip()
                logging.warning("SEND FILE: send file from {} to {}" . format(usernamefrom, usernameto))
                return self.send_file(usernamefrom, usernameto, encoded_content, filename)
            elif (command == 'receivefile'):
                username = j[1].strip()
                logging.warning("RECEIVE FILE: Username {} received file" . format(username))
                return self.receive_file(username)
            elif(command == 'creategroup'):
                groupname = j[1].strip()
                logging.warning(
                    "CREATE GROUP: createing '{}' group" . format(groupname))
                return self.register_group(groupname)
            elif(command == 'joingroup'):
                username = j[1].strip()
                groupname = j[2].strip()
                realmid = j[3].strip()
                # logging.warning("JOIN GROUP: {} {} {} {}" . format(sessionid, groupname, username, realmid))
                return self.join_group(username, groupname, realmid)
            elif (command == 'inbox'):
                username = j[1].strip()
                sender = j[2].strip()
                logging.warning("INBOX: {}")
                return self.get_inbox_by_spesisic_sender(username,sender)
            elif (command == 'inboxgroup'):
                username = j[1].strip()
                groupname = j[2].strip()
                logging.warning("INBOX GROUP: {} {}" . format(username, groupname))
                return self.get_inbox_group(username, groupname)
            elif (command == 'getallusers'):
                return self.get_all_users()
            elif (command == 'getallgroups'):
                username = j[1].strip()
                return self.get_all_groups(username)
            else:
                return {'status': 'ERROR', 'message': '**Protocol Tidak Benar', 'command': command}
        except KeyError:
            return {'status': 'ERROR', 'message': 'Informasi tidak ditemukan'}
        except IndexError:
            return {'status': 'ERROR', 'message': '--Protocol Tidak Benar', 'command': j}

    def get_all_groups(self, username):
        username = username.split(':')[1].strip()
        groups = self.group_user_db.get_by_key_value_group_user('username', username)
        if(len(groups) == 0):
            return {'status': 'ERROR', 'message': 'User tidak memiliki akses ke grup'}
        else:
            return {'status': 'OK', 'groups': groups}
    def get_all_users(self):
        users = self.user_db.get_all_by_key('username')
        return {'status': 'OK', 'users': users}
    def autentikasi_user(self, username, password):
        username = username.split(':')[1].strip()
        password = password.split(':')[1].strip()
        user = self.user_db.get_by_key_value('username', username)
        if not user:
            return {'status': 'ERROR', 'message': 'user tidak ditemukan'}
        if user['password'] != password:
            return {'status': 'ERROR', 'message': 'password salah'}
        tokenid = str(uuid.uuid4())
        return {'status': 'OK', 'token_id': tokenid, 'realm_id': user['realm_id']}
    
    def register_user(self, username, password, server_id):
        username = username.split(':')[1]
        password = password.split(':')[1]
        server_id = server_id.split(':')[1]
        is_user_exist = self.get_user(username)
        if is_user_exist:
            return {'status': 'ERROR', 'message': 'user telah terdaftar'}
        else:
            new_user = {
                'username': username,
                'password': password,
                'realm_id': server_id
            }
            self.user_db.insert_data(new_user)
            return {'status': 'OK', 'realm_id': new_user['realm_id']}
    
    def join_group(self, username, groupname, realmid):
        username = username.split(':')[1].strip()
        groupname = groupname.split(':')[1].strip()
        realmid = realmid.split(':')[1].strip()
        user = self.get_user(username)
        group = self.get_group(groupname)
        if(not user):
            return {'status': 'ERROR', 'message': 'User tidak ditemukan'}
        if(not group):
            return {'status': 'ERROR', 'message': 'Group tidak ditemukan'}
        group_user = {
            'username': user['username'],
            'groupname': group['name'],
            'realm_id': realmid
        }
        self.group_user_db.insert_data(group_user)
        return {'status': 'OK', 'message': 'User berhasil join group'}
    
    
    def register_group(self, groupname):
        groupname=groupname.split(':')[1].strip()
        is_group_exist = self.get_group(groupname)
        if is_group_exist:
            return {'status': 'ERROR', 'message': 'group telah terdaftar'}
        else:
            new_group = {
                'name': groupname,
            }
            self.group_db.insert_data(new_group)
            return {'status': 'OK', 'groupname':groupname}

    def get_user(self, username):
        user = self.user_db.get_by_key_value('username', username)
        if (not user):
            return False
        return user

    def get_group(self, groupname):
        group = self.group_db.get_by_key_value('name', groupname)
        if (not group):
            return False
        return group

    def send_message(self, username_from, username_dest, message):
        username_from = username_from.split(':')[1].strip()
        username_dest = username_dest.split(':')[1].strip()
        message = message.split('message:')[1].strip()
        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)

        if (s_fr == False or s_to == False):
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}

        message = PrivateMessage(
            s_fr['username'],
            s_fr['realm_id'],
            s_to['username'],
            s_to['realm_id'],
            message
        )

        self.private_message_db.insert_data(message.toDict())

        return {'status': 'OK', 'message': 'Message Sent'}
    
    def send_file(self, username_from, username_to, encoded_content, filepath):
        username_from = username_from.split(':')[1].strip()
        username_to = username_to.split(':')[1].strip()
        encoded_content = encoded_content.split(':')[1].strip()
        filename = filepath.split(':')[1].strip()
    
        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_to)
    
        if (s_fr == False or s_to == False):
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
        
        message = FileMessage(
            s_fr['username'],
            s_fr['realm_id'],
            s_to['username'],
            s_to['realm_id'],
            encoded_content,
            filename
        )
    
        self.file_message_db.insert_data(message.toDict())

        return {"status": "OK", "message": "File Sent"}
    
    def receive_file(self, username):
        username = username.split(':')[1].strip()
        msgs = self.file_message_db.getall_by_key_value('receiver', username)

        return {'status': 'OK', 'content': msgs}
    

    def send_message_group(self, username_from, groupname_dest, message):
        username_from = username_from.split(':')[1].strip()
        groupname_dest = groupname_dest.split(':')[1].strip()
        message = message.split('message:')[1].strip()
        
        isUserInGroup = self.group_user_db.is_user_exists_group(username_from, groupname_dest)
        if (isUserInGroup == False):
            return {'status': 'ERROR', 'message': 'User tidak memiliki akses ke grup ini'}
        
        s_fr = self.get_user(username_from)
        s_to = self.get_group(groupname_dest)

        if (s_fr == False or s_to == False):
            return {'status': 'ERROR', 'message': 'Grup Tidak Ditemukan'}

        message = GroupMessage(
            s_fr['username'],
            s_fr['realm_id'],
            s_to['name'],
            message
        )

        self.group_message_db.insert_data(message.toDict())

        return {'status': 'OK', 'message': 'Message Sent'}
    
    def get_inbox_by_spesisic_sender(self, username, sender):
        username = username.split(':')[1].strip()
        sender = sender.split(':')[1].strip()
        msgs = self.private_message_db.getall_by_key_value('receiver', username, 'sender', sender)
        return {'status': 'OK', 'messages': msgs}

    def get_inbox_group(self, username ,groupname):
        username = username.split(':')[1].strip()
        groupname = groupname.split(':')[1].strip()
        isUserInGroup = self.group_user_db.is_user_exists_group(username, groupname)
        if (isUserInGroup == False):
            return {'status': 'ERROR', 'message': 'User tidak memiliki akses ke grup ini'}

        msgs = self.group_message_db.getall_by_key_value('receiver_group', groupname)
        return {'status': 'OK', 'messages': msgs}
    
    @staticmethod
    def list_messages(msgs):
        messages = ''
        for msg in msgs:
            messages +=  '['+ msg['sender'] + ': ' + msg['message'] + '], '
        return messages

    
    def commands(payload):
        
        return



class Server(threading.Thread):
    def __init__(self):
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.user_db = Database('user.json')
        self.group_db = Database('group.json')
        self.group_user_db = Database('group_user.json')
        self.private_message_db = Database('private_message.json')
        self.group_message_db = Database('group_message.json')
        self.file_message_db = Database('file_message.json')
        threading.Thread.__init__(self)

    def run(self):
        self.my_socket.bind(('localhost', 8080))
        self.my_socket.listen(1)
        while True:
            self.connection, self.client_address = self.my_socket.accept()
            logging.warning("connection from {}" . format(self.client_address))

            clt = ProcessTheClient(self.connection, self.client_address, self.user_db, self.group_db, self.group_user_db, self.private_message_db, self.group_message_db, self.file_message_db)
            clt.start()
            self.the_clients.append(clt)
    
    

def main():
    svr = Server()
    svr.start()
    logging.warning(' REALM1: running server on port 8080')


if __name__ == "__main__":
    main()
