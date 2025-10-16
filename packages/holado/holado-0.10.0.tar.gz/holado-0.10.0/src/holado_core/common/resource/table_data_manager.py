
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

import logging
from holado_core.common.exceptions.technical_exception import TechnicalException
from holado_core.common.tools.tools import Tools
import copy
from holado.common.handlers.undefined import undefined_argument

logger = logging.getLogger(__name__)



class TableDataManager():
    """
    Manage data stored in a dedicated resource table.
    """
    def __init__(self, data_name, table_name, table_sql_create, db_name="default", is_persistent=False, do_audit=False):
        self.__data_name = data_name
        self.__table_name = table_name
        self.__table_sql_create = table_sql_create
        self.__db_name = db_name
        self.__is_persistent = is_persistent
        self.__do_audit = do_audit
        
        self.__resource_manager = None
    
    def initialize(self, resource_manager):
        self.__resource_manager = resource_manager
        
    @property
    def table_name(self):
        return self.__table_name
    
    def ensure_db_exists(self):
        if self.__resource_manager.has_data_table(self.__table_name, db_name=self.__db_name, is_persistent=self.__is_persistent):
            if self.__resource_manager.check_data_table_schema(self.__table_name, self.__table_sql_create, db_name=self.__db_name, is_persistent=self.__is_persistent):
                # Table already exists with the right schema
                return
            else:
                # Table already exists but with wrong schema => delete table before creating it again
                self.__resource_manager.delete_data_table(self.__table_name, db_name=self.__db_name, is_persistent=self.__is_persistent, raise_if_not_exist=True, do_commit=True)
        
        # Create table
        # Note: method create_data_table raise an exception if it doesn't succeed to create the table
        self.__resource_manager.create_data_table(self.__table_name, self.__table_sql_create, db_name=self.__db_name, is_persistent=self.__is_persistent, raise_if_exist=True, do_commit=True, do_audit=self.__do_audit)
    
    def has_data(self, filter_data=None, filter_compare_data=None):
        return self.__resource_manager.has_data(self.__table_name, where_data=filter_data, where_compare_data=filter_compare_data, db_name=self.__db_name, is_persistent=self.__is_persistent)
        
    def get_datas(self, filter_data=None, filter_compare_data=None, as_generator=False):
        """
        Note: Whereas 'data' is already a plural, a 's' is added in method name to be coherent with other method names
        """
        return self.__resource_manager.get_data(self.__table_name, where_data=filter_data, where_compare_data=filter_compare_data, db_name=self.__db_name, is_persistent=self.__is_persistent, result_as_dict_list=True, as_generator=as_generator)

    def get_data(self, filter_data=None, filter_compare_data=None):
        """
        Note: Whereas 'datum' should be the right word in method name since method returns only one datum, method is named with 'data' in its usual singular meaning for most people.
        """
        data = self.get_datas(filter_data=filter_data, filter_compare_data=filter_compare_data)
        if len(data) > 1:
            raise TechnicalException(f"Too many ({len(data)}) {self.__data_name} found for filter {filter_data}.")
        elif len(data) == 1:
            return data[0]
        else:
            return None
        
    def count_data(self, filter_data=None, filter_compare_data=None):
        return self.__resource_manager.count_data(self.__table_name, where_data=filter_data, where_compare_data=filter_compare_data, db_name=self.__db_name, is_persistent=self.__is_persistent)

    def update_data(self, data, filter_data=None, filter_compare_data=None):
        if Tools.do_log(logger, logging.DEBUG):
            logger.debug(f"Update {self.__data_name} for {filter_data} and {filter_compare_data}: {data}")
        self.__resource_manager.update_data(self.__table_name, data, where_data=filter_data, where_compare_data=filter_compare_data, db_name=self.__db_name, is_persistent=self.__is_persistent)

    def add_data(self, data, filter_data=None):
        if Tools.do_log(logger, logging.DEBUG):
            logger.debug(f"Add {self.__data_name} for {filter_data}: {data}")
        data = copy.copy(data)
        if filter_data:
            data.update(filter_data)
        self.__resource_manager.add_data(self.__table_name, data, db_name=self.__db_name, is_persistent=self.__is_persistent)
        
    def update_or_add_data(self, filter_data, data, existing_data=undefined_argument):
        if existing_data is undefined_argument:
            has_data = self.has_data(filter_data)
        else:
            has_data = existing_data is not None
        
        if has_data:
            self.update_data(data, filter_data=filter_data)
        else:
            self.add_data(data, filter_data)
        
    def delete_data(self, filter_data):
        self.__resource_manager.delete_data(self.__table_name, where_data=filter_data, db_name=self.__db_name, is_persistent=self.__is_persistent)



