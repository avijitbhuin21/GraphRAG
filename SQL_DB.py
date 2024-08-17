import os
import requests
import csv

import mysql.connector
from mysql.connector import Error
from miscellenous import get_in_chunks, get_sql_query
from Custom_LLM import groq_llm

class SQL_LOADER:
    def __init__(self, table_name) -> None:
        self.connection = mysql.connector.connect(
            host=os.environ.get('SQL_HOST'),
            user=os.environ.get('SQL_USERNAME'),
            password=os.environ.get('SQL_PASSWARD'),
            database=os.environ.get('SQL_DATABASE')
        )
        self.cursor = self.connection.cursor()
        self.table_name = table_name
        try:
            self.sql_schema, self.sql_data = self.load_sql_details()
        except:
            print("Table Not found.. Please load data first.")

    def load_sql_details(self):
        self.cursor.execute(f"SELECT * FROM {self.table_name}")
        data = self.cursor.fetchall()
        schema =  self.cursor.description
        return schema

    def close_conn(self):
        self.connection.commit()
        self.cursor.close()
        self.connection.close()

    def load_data (self, path, name):
        print(path)
        data = []
        if path.startswith('https://'):
            res = requests.get(path)
            res = res.text
            res = res.split('\n')
            header = [i.strip() for i in res [0].split(',')]
            body = res[1:]
            for row in body:
                row = row.split(',')
                if len(row) == 7:  # Ensure the row has exactly 7 elements
                    try:
                        x=[]
                        for i in row:
                            temp = i if i != '' else (lambda: (_ for _ in ()).throw(ValueError("Column cannot be empty")))()
                            x.append(temp)
                        data.append(tuple(x))
                    except ValueError as e:
                            print(f"Skipping row due to error: {e, row}")
        
        else:
            with open(path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                header = next(reader)
                for row in reader:
                    if len(row) == 7:  # Ensure the row has exactly 7 elements
                        try:
                            x=[]
                            for i in row:
                                temp = i if i != '' else (lambda: (_ for _ in ()).throw(ValueError("Column cannot be empty")))()
                                x.append(temp)
                            data.append(tuple(x))
                        except ValueError as e:
                            print(f"Skipping row due to error: {e, row}")

        
        self.cursor.execute(f"DROP TABLE IF EXISTS {name}")
        self.cursor.execute(f'''CREATE TABLE {name} (
                                                        {",".join([i+' TEXT' for i in header])}
                                                    );
                                                    ''')

        for row in data:
            self.cursor.execute(f"""
                INSERT INTO {name} ({", ".join(header)})
                VALUES ({", ".join(["%s" for _ in header])})
            """, row)
        self.sql_schema, self.sql_data = self.load_sql_details()
        self.close_conn()

    def Check_bland_sqlDb(self, question ):
        x = groq_llm()
        schema = [i[0] for i in self.sql_schema]
        search_text = get_in_chunks(question=question, schema=schema)
        ret = []
        for i in schema:
            for j in search_text:
                where_clause = f"`{i}` LIKE '%{j}%'"
                query = f"SELECT * FROM `{self.table_name}` WHERE {where_clause};"
                self.cursor.execute(query)
                ans = self.cursor.fetchall()
                if ans != []:
                    for j in ans:
                            ret.append([f"{schema[i]}:{j[i]}" for i in range(len(schema))])
        if ret != []:
            data = x.sql_db_all(question=question, data=f'''SQL_DATABASE_CONTEXT (by searching for main keywords, in this case {str(search_text)}):\nSchema: {schema}\nData:\n{str(ret)}''')
            print(f'''Manually Provided Context: {data}''')
            return f'''Manually Provided Context: {data}'''
        else:
            return None
    
    def sql_llm_check(self, question):
        schema = [i[0] for i in self.sql_schema]
        conv = [f"""
                Write a SQL Query given the table name {self.table_name} and columns as a list {schema} for the given question : 
                {question}.
                """]
        for i in range(5):
            if i!=0:
                print(f"Retrying: {i}")
            try:
                query = get_sql_query("\n".join(conv))
                print(f"Generated SQL Query: {query}")
                self.cursor.execute(query)
                ans = self.cursor.fetchall()
                print(f'''SQL_DATABASE_CONTEXT (by running the following query: {query}): \n{ans}''')
                return f'''SQL_DATABASE_CONTEXT (by running the following query: {query}): \n{ans}'''
            except Error as e:
                print("Failed!!")
                conv.append(f"After running the query: {query}, i got this error: {e}")
                continue

            
