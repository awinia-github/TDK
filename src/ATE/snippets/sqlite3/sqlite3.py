# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 13:16:58 2019

@author: hoeren
"""

import os
import sqlite3



    

db_file = r'C:\Users\hoeren\__spyder_workspace__\CTCA\CTCA.sqlite3'
sql_select_statement = "SELECT Name FROM hardwaresetups ORDER BY Name ASC"

conn = sqlite3.connect(db_file)
cur = conn.cursor()
cur.execute(sql_select_statement)
rows = cur.fetchall()

result = []
for row in rows:
    result.append(row[0])

print(result)