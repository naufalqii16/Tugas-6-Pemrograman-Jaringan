import json
import os
from pathlib import Path
from operator import itemgetter


class Database:
    def __init__(self, table_name):
        self.table_name = table_name
        base_path = Path(__file__).parent.absolute()
        self.file_name = Path(__file__).joinpath(base_path, self.table_name)
        self.data = self.read_db()
        self.realms = {}

    # read_db reads data from file
    def read_db(self):
        try:
            f = open(self.file_name, "r")
            file_data = json.load(f)
            f.close()
            return file_data["data"]
        except Exception as e:
            print("Tidak dapat membaca file ", e)
            return

    # write_db writes data in the file
    def write_db(self):
        try:
            f = open(self.file_name, "w")
            f.truncate(0)
            f.write(json.dumps({"data": self.data}, indent=4))
            f.close()
        except Exception as e:
            print("Tidak dapat menulis file ", e)
            return

    # get_all returns all the data in the database
    def get_all(self):
        return self.data
    
    def get_all_by_key(self, key):
        return [data[key] for data in self.data]

    # is_exists checks if a data exists matching by the key and value
    def is_exists(self, key, value):
        return value in [data[key] for data in self.data]

    # get_by_key_value returns a data by the matching key and value
    def get_by_key_value(self, key, value):
        lookup = {d[key]: d for d in self.data}
        print(lookup.get(value))
        return lookup.get(value)
    
    def is_user_exists_group (self, username, groupname):
        for obj in self.data:
            if obj.get("username") == username and obj.get("groupname") == groupname:
                return True
        return False
    
    # get_by_key_value for username and group in group_user_db
    def get_by_key_value_group_user(self, key, value):
        result = []
        for obj in self.data:
            if obj.get(key) == value:
                result.append(obj)
        return result
    
    def getall_by_key_value(self, key, value, key2=None, value2=None):
        result = []
        if key2 != None:
            for obj in self.data:
                if (obj.get(key) == value and obj.get(key2) == value2) or (obj.get(key) == value2 and obj.get(key2) == value):
                    result.append(obj)
            return result
        else:
            for obj in self.data:
                if obj.get(key) == value:
                    result.append(obj)
        return result
    
    # def add_realms(self, realm, ip):
    #     if realm not in self.realms and realm.startswith("D34dB33F") and realm.endswith("D34dB33F13nD"):
    #         self.realms[realm] = ip
    
    # def send_realms(self):
    #     return self.realms
    
        # lookup = {d[key]: d for d in self.data}
        # return lookup.get(value)
    


    # insert_data inserts a new data and writes it into the database
    def insert_data(self, new_data):
        self.data.append(new_data)
        self.write_db()

    # get_sorted returns the data of a table in a sorted order by one of its key
    def get_sorted(self, key, asc=False):
        return sorted(self.data, key=itemgetter(key), reverse=(not asc))


if __name__ == "__main__":
    db = Database("user.json")
    print(db.get_all())
    db.insert_data({"username": "aaa", "password": "123"})
    print(db.get_all())
    print(db.get_sorted("username", True)[0])
    print(db.is_exists("username", "aaa"))
    print(db.get_by_key_value("username", "user"))
