import socket
import json
import base64
import os
from datetime import datetime

TARGET_IP = "localhost"
TARGET_PORT = 8000

class ChatClient:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (TARGET_IP, TARGET_PORT)
        self.sock.connect(self.server_address)
        self.token_id = ""
        self.realm_id = ""

    def proses(self, cmdline):
        j = cmdline.split(" ")
        try:
            command = j[0].strip()
            if (command == 'register'):
                username = j[1].strip()
                password = j[2].strip()
                return self.register(username, password)
            elif (command == 'creategroup'):
                groupname = j[1].strip()
                return self.create_group(groupname)
            elif (command == 'joingroup'):
                groupname = j[1].strip()
                return self.join_group(groupname)
            elif (command == 'auth'):
                username = j[1].strip()
                password = j[2].strip()
                return self.login(username, password)
            elif (command == 'sendprivate'):
                usernameto = j[1].strip()
                message = ""
                for w in j[2:]:
                    message = "{} {}" . format(message, w)
                return self.sendmessage(usernameto, message)
            elif (command == 'sendgroup'):
                groupto = j[1].strip()
                message = ""
                for w in j[2:]:
                    message = "{} {}" . format(message, w)
                return self.sendmessage_group(groupto, message)
            elif (command == 'sendfile'):
                usernameto = j[1].strip()
                filepath = j[2].strip()
                return self.sendfile(usernameto, filepath)
            elif (command == 'receivefile'):
                sender = j[1].strip()
                return self.receivefile(sender)
            elif (command == 'inboxgroup'):
                groupname = j[1].strip()
                return self.inbox_group(groupname)
            elif (command == 'getallusers'):
                return self.get_all_users()
            elif (command == 'inboxbysender'):
                sender = j[1].strip()
                return self.get_inbox_by_sender(sender)
            elif(command == 'getallgroups'):
                return self.get_groups()
            else:
                return "*Maaf, command tidak benar"
        except IndexError:
            return "-Maaf, command tidak benar"

    def sendstring(self, string):
        try:
            self.sock.sendall(string.encode())
            while True:
                data = self.sock.recv(10000000)
                # print("diterima dari server", data)
                if (data):
                    # data harus didecode agar dapat di operasikan dalam bentuk string
                    receivemsg = data.decode("utf-8")
                    if receivemsg[-4:] == '\r\n\r\n':
                        data = receivemsg[:-4].strip()
                        loaded_json = json.loads(data)
                        return loaded_json
        except Exception as e:
            self.sock.close()
            return {'status': 'ERROR', 'message': 'Gagal'}
        
    def get_groups(self):
        if (self.token_id == ""):
            return "Error, not authorized"
        string = "getallgroups {} \r\n".format(self.token_id)
        result = self.sendstring(string)
        return result
    def get_inbox_by_sender(self, sender):
        if (self.token_id == ""):
            return "Error, not authorized"
        string = "inboxbysender {} {} \r\n".format(self.token_id, sender)
        result = self.sendstring(string)
        return result
    def get_all_users(self):
        string = "getallusers \r\n"
        result = self.sendstring(string)
        return result

    def register(self, username, password):
        string = "register {} {} \r\n" . format(username, password)
        result = self.sendstring(string)
        if result['status'] == 'OK':
            return "username {} successfully registered " .format(username)
        else:
            return "Error, {}" . format(result['message'])
        
    def create_group(self, groupname):
        if (self.token_id == ""):
            return "Error, not authorized"
        string = "creategroup {} \r\n" . format(groupname)
        result = self.sendstring(string)
        if result['status'] == 'OK':
            return "groupname {} successfully created " .format(groupname)
        else:
            return "Error, {}" . format(result['message'])
        
        
    def login(self, username, password):
        string = "auth {} {} \r\n" . format(username, password)
        result = self.sendstring(string)
        if result['status'] == 'OK':
            self.token_id = result['token_id']
            self.realm_id = result['realm_id']
            return "username {} logged in, token {} " .format(username, self.token_id)
        else:
            return "Error, {}" . format(result['message'])

    def sendmessage(self, usernameto="xxx", message="xxx"):
        if (self.token_id == ""):
            return "Error, not authorized"
        string = "sendprivate {} {} {} \r\n" . format(
            self.token_id, usernameto, message)
        result = self.sendstring(string)
        if result['status'] == 'OK':
            return "message sent to {}" . format(usernameto)
        else:
            return "Error, {}" . format(result['message'])
        
    def join_group(self, groupname):
        if (self.token_id == ""):
            return "Error, not authorized"
        string = "joingroup {} {} {} \r\n" . format(self.token_id, groupname, self.realm_id)
        result = self.sendstring(string)
        if result['status'] == 'OK':
            return "groupname {} successfully joined " .format(groupname)
        else:
            return "Error, {}" . format(result['message'])

    def sendmessage_group(self, groupto="xxx", message="xxx"):
        if (self.token_id == ""):
            return "Error, not authorized"
        string = "sendgroup {} {} {} \r\n" . format(
            self.token_id, groupto, message)
        result = self.sendstring(string)
        if result['status'] == 'OK':
            return "message sent to {}" . format(groupto)
        else:
            return "Error, {}" . format(result['message'])
        
    def sendfile(self, usernameto="xxx", filepath="xxx"):
        if (self.token_id == ""):
            return "Error, not authorized"
        if not os.path.exists(filepath):
            return "Error, file not found"
        
        with open(filepath, "rb") as file:
            file_content = file.read()
            encoded_content = base64.b64encode(file_content)  # Decode byte-string to UTF-8 string

        string = "sendfile {} {} {} {} \r\n" . format(self.token_id, usernameto, encoded_content, filepath)
        result = self.sendstring(string)
        if result['status'] == 'OK':
            return "file sent to {}" . format(usernameto)
        else:
            return "Error, {}" . format(result['message'])
    
    def receivefile(self,sender):
        if (self.token_id == ""):
            return "Error, not authorized"

        string = "receivefile {} {} \r\n" . format(self.token_id, sender)

        result = self.sendstring(string)
        if result['status'] == 'OK':
            for message in result['content']:
                filename = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_ConvoHub_{message['file_name']}"
                file_content = message['file_content']
                if(directories := os.path.join(os.getcwd(), "file_receive", message['receiver'])):
                    os.makedirs(directories, exist_ok=True)
                file_destination = os.path.join(os.getcwd(), "file_receive", message['receiver'], filename)

                if 'b' in file_content[0]:
                    msg = file_content[2:-1]

                with open(file_destination, "wb") as file:
                    file.write(base64.b64decode(msg))

            else:
                tail = file_content.split()
            
            return "file received"

    def inbox_group(self, groupname):
        if (self.token_id == ""):
            return "Error, not authorized"
        string = "inboxgroup {} {}\r\n" . format(self.token_id, groupname)
        result = self.sendstring(string)
        return result


if __name__ == "__main__":
    cc = ChatClient()
    while True:
        cmdline = input("Command {}:" . format(cc.token_id))
        print(cc.proses(cmdline))
