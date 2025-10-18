
#################################################
# HolAdo (Holistic Automation do)
#
# (C) Copyright 2021-2025 by Eric Klumpp
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# The Software is provided “as is”, without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the software or the use or other dealings in the Software.
#################################################

import os
import logging

logger = logging.getLogger(__name__)



class ResourceManager():
    """
    Manage local resources, ie resources stored on disk during and through sessions.
    For example, it can be used to persist data through sessions, so that a session can adapt its behavior according previous sessions.
    """
    def __init__(self, local_resource_path):
        self.__local_resource_path = local_resource_path
        
        self.__func_db_manager = None
        self.__func_path_manager = None
        self.__db_connect_kwargs_by_name = {}
        
    def initialize(self, func_db_manager, func_path_manager):
        self.__func_db_manager = func_db_manager
        self.__func_path_manager = func_path_manager
        
        self.__path_manager.makedirs(self.__local_resource_path, is_directory=True)
        
    @property
    def __db_manager(self):
        return self.__func_db_manager()
    
    @property
    def __path_manager(self):
        return self.__func_path_manager()
        
    @property
    def local_resource_path(self):
        return self.__local_resource_path
    
    def get_path(self, *args):
        return os.path.join(self.__local_resource_path, *args)
    
    def get_db_client(self, name, is_persistent=False):
        """ Return a SQLite3 DB client to the resource DB of given name
        @param is_persistent If True, name is prefixed with 'persistent/db/'
        """
        full_name = os.path.join("persistent", "db", name) if is_persistent else name
        _, res = self.__db_manager.get_or_create(full_name, 'sqlite3', self.__get_db_connect_kwargs(full_name))
        return res
    
    def __get_db_connect_kwargs(self, full_name):
        if full_name not in self.__db_connect_kwargs_by_name:
            db_filepath = self.get_path(f"{full_name}.sqlite3")
            self.__path_manager.makedirs(db_filepath)
            
            uri = f"file:{db_filepath}?mode=rwc"
            connect_kwargs = {'database': uri,
                              'uri': True}
            self.__db_connect_kwargs_by_name[full_name] = connect_kwargs
        return self.__db_connect_kwargs_by_name[full_name]
        
    def persist_pair(self, key, value, db_name="default", table_name="pair", do_commit=True):
        client = self.get_db_client(db_name, is_persistent=True)
        client.execute(f"create table if not exists {table_name} (key, value)", do_commit=do_commit)
        
        client.execute(f"insert into {table_name} values (?, ?)", key, value, do_commit=do_commit)
        
    def has_data_table(self, table_name, db_name="default", is_persistent=False):
        client = self.get_db_client(db_name, is_persistent=is_persistent)
        return client.exist_table(table_name)
        
    def create_data_table(self, table_name, create_sql, db_name="default", is_persistent=False, raise_if_exist=False, do_commit=True, do_audit=False):
        client = self.get_db_client(db_name, is_persistent=is_persistent)
        client.create_table(table_name, create_sql, raise_if_exist=raise_if_exist, do_commit=do_commit, do_audit=do_audit)
        
    def delete_data_table(self, table_name, db_name="default", is_persistent=False, raise_if_not_exist=False, do_commit=True):
        client = self.get_db_client(db_name, is_persistent=is_persistent)
        client.drop_table(table_name, raise_if_not_exist=raise_if_not_exist, do_commit=do_commit)
        
    def check_data_table_schema(self, table_name, create_sql, db_name="default", is_persistent=False):
        client = self.get_db_client(db_name, is_persistent=is_persistent)
        result = client.select("sqlite_schema", where_data={'name':table_name}, sql_return='sql')
        if not result:
            return False
        
        sql = result[0][0].content
        return sql == create_sql
        
    def count_data(self, table_name, where_data: dict=None, where_compare_data: list=None, db_name="default", is_persistent=False):
        client = self.get_db_client(db_name, is_persistent=is_persistent)
        return client.count(table_name, where_data=where_data, where_compare_data=where_compare_data)
        
    def has_data(self, table_name, where_data: dict=None, where_compare_data: list=None, db_name="default", is_persistent=False):
        count = self.count_data(table_name, where_data=where_data, where_compare_data=where_compare_data, db_name=db_name, is_persistent=is_persistent)
        return count > 0
        
    def get_data(self, table_name, where_data: dict=None, where_compare_data: list=None, db_name="default", is_persistent=False, result_as_dict_list=False, as_generator=False):
        client = self.get_db_client(db_name, is_persistent=is_persistent)
        result = client.select(table_name, where_data=where_data, where_compare_data=where_compare_data, result_as_dict_list=result_as_dict_list, as_generator=as_generator)
        return result
        
    def add_data(self, table_name, data: dict, db_name="default", is_persistent=False, do_commit=True):
        client = self.get_db_client(db_name, is_persistent=is_persistent)
        result = client.insert(table_name, data, do_commit=do_commit)
        return result
        
    def update_data(self, table_name, data: dict, where_data: dict=None, where_compare_data: list=None, db_name="default", is_persistent=False, do_commit=True):
        client = self.get_db_client(db_name, is_persistent=is_persistent)
        result = client.update(table_name, data=data, where_data=where_data, where_compare_data=where_compare_data, do_commit=do_commit)
        return result
        
    def delete_data(self, table_name, where_data: dict=None, where_compare_data: list=None, db_name="default", is_persistent=False, do_commit=True):
        client = self.get_db_client(db_name, is_persistent=is_persistent)
        client.delete(table_name, where_data=where_data, where_compare_data=where_compare_data, do_commit=do_commit)
        
