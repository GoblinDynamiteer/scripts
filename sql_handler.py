#!/usr/bin/python
# -*- coding: utf-8 -*-
import paths, os
import MySQLdb
from printout import print_class as pr

pr = pr(os.path.basename(__file__))

class sql_connection:
    def __init__(self, remote_address, login, password, port, database_name):
        self.connected = False
        self.cursor = None
        self.sql_db_conn = MySQLdb.connect(host=remote_address, user=login, passwd=password, port=port, db=database_name)
        if self.sql_db_conn:
            self.connected = True
            self.cursor = self.sql_db_conn.cursor()

    def update(self, table, column, value, column_to_match, match_data):
        query = f"UPDATE {table} SET {column} = %s WHERE {table}.{column_to_match} = %s"
        data = (value, match_data)
        if self.__run_query(query, data):
            self.__commit()
            pr.info(f"updated: {match_data} : {column} = {value}")
            return True
        else:
            pr.warning(f"failed update: {match_data} : {column} = {value}")
            return False

    def insert(self, table, columns = [], data=[]):
        if len(columns) != len(data):
            pr.warning("columns and data doesnt match!")
            return
        query = f"INSERT INTO {table} ("
        for column in columns:
            query += f"{column},"
        query = query[:-1] + ") VALUES ("
        for column in columns:
            query += r"%s,"
        query = query[:-1] + ")"
        result = self.__run_query(query, tuple(data))
        if result:
            self.__commit()
            pr.info(f"inserted {data} into table {table}")
            return True
        else:
            return False

    def select(self, table, columns = [], column_to_match = None, match_data = None):
        column_string = ""
        if not columns:
            column_string = "*"
        else:
            for column in columns:
                column_string = f"{column_string},{column}"
        column_string = column_string.strip(',')
        query = f"SELECT {column_string} FROM {table} WHERE {column_to_match} = %s"
        data = (match_data,)
        result = self.__run_query(query, data)
        result_list = []
        if result:
            self.__commit()
            pr.info(f"selected: {columns}")
            for column_string in self.cursor:
                print(f"result: {str(column_string)}")
                result_list.append(str(column_string))
            return result
        else:
            pr.warning(f"failed select query")
            return False

    def __run_query(self, query, data):
        try:
            self.cursor.execute(query, data)
            return True
        except:
            return False

    def __commit(self):
        self.sql_db_conn.commit()
