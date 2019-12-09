# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 13:16:58 2019

@author: hoeren
"""

import os
import sqlite3


class db(object):
    
    def __init__(self):
        self.db_path = os.path.join(os.path.basename(__file__), 'database.sqlite3')
        self.db_conn = sqlite3.connect(self.db_path)
        self.db_cursor = self.db_conn.cursor()

    def __del__(self):
        self.db_conn.close()
        
    def add_hardwaresetup(self, data):
        pass
    
    



sql = "SELECT name, ProbeCard FROM hardwaresetups"

db_cursor.execute(sql)

rows = db_cursor.fetchall()
headers = [description[0] for description in db_cursor.description]

for row in rows:
    for index, header in enumerate(headers):
        print(index, header, row)
