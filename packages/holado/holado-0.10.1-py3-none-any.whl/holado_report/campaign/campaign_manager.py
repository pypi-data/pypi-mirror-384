
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

from holado.common.context.session_context import SessionContext
import logging
from holado_core.common.resource.table_data_manager import TableDataManager
from holado_python.common.tools.datetime import DateTime, TIMEZONE_LOCAL
import os
from holado_system.system.filesystem.file import File
import re


logger = logging.getLogger(__name__)



class CampaignManager(object):
    """ Manage all campaigns
    """
    
    def __init__(self, db_name="campaigns"):
        super().__init__()
        
        self.__db_name = db_name
        self.__resource_manager = None
        
        self.__campaigns_table_manager = TableDataManager('campaign', 'campaigns', self.__get_campaigns_table_sql_create(), db_name=self.__db_name)
        self.__campaign_scenarios_table_manager = TableDataManager('campaign scenario', 'campaign_scenarios', self.__get_campaign_scenarios_table_sql_create(), db_name=self.__db_name)
    
    def initialize(self, resource_manager):
        self.__resource_manager = resource_manager
        
        self.__campaigns_table_manager.initialize(resource_manager)
        self.__campaigns_table_manager.ensure_db_exists()
        self.__campaign_scenarios_table_manager.initialize(resource_manager)
        self.__campaign_scenarios_table_manager.ensure_db_exists()
    
    def __get_db_client(self):
        return self.__resource_manager.get_db_client(self.__db_name)
    
    def __get_campaigns_table_sql_create(self):
        return """CREATE TABLE campaigns (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                report_path TEXT NOT NULL
            )"""

    def __get_campaign_scenarios_table_sql_create(self):
        return """CREATE TABLE campaign_scenarios (
                id INTEGER PRIMARY KEY,
                campaign_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                report_path TEXT,
                status TEXT,
                status_at TEXT,
                details TEXT
            )"""

    def update_stored_campaigns(self):
        """ Update stored reports in DB with new campaigns
        """
        # Get report paths of campaigns to import
        dt_last_camp = self.__get_last_campaign_scenario_status_datetime()
        report_paths = self.__get_campaigns_report_paths(since_datetime=dt_last_camp)
        
        # Sort reports in time order
        report_paths = sorted(report_paths, key=lambda p: os.path.getmtime(os.path.join(p, 'report_summary_scenario_all.txt')))
        logger.info(f"reports to import: {report_paths}", msg_size_limit=None)
        
        # Import reports
        for report_path in report_paths:
            self.import_campaign_reports(report_path)
    
    def __get_campaigns_report_paths(self, since_datetime):
        reports_path = SessionContext.instance().path_manager.get_reports_path()
        file_paths = SessionContext.instance().path_manager.find_files(reports_path, subdir_relative_path='report_summary_scenario_all.txt', since_datetime=since_datetime)
        return [os.path.dirname(p) for p in file_paths]
    
    def __get_last_campaign_scenario_status_datetime(self):
        """ From stored campaigns, return the datetime of the last scenario with an execution status
        """
        client = self.__get_db_client()
        
        query_str = f'''
            SELECT status_at
            FROM campaign_scenarios
            ORDER BY status_at DESC 
            LIMIT 1
        '''
        res_dict_list = client.execute(query_str, result_as_dict_list=True, as_generator=False)
        
        status_dt_str = res_dict_list[0]['status_at'] if res_dict_list else None
        status_dt = DateTime.str_2_datetime(status_dt_str, tz=TIMEZONE_LOCAL) if status_dt_str else None
        return status_dt
        
    def import_campaign_reports(self, report_path):
        """ Import reports of a campaign
        @param report_path Path to the campaign report
        """
        logger.info(f"Import campaign report '{report_path}'")
        
        # Add campaign
        camp_name = os.path.basename(report_path)
        camp_id = self.add_campaign_if_needed(camp_name, report_path)
        
        # Import scenario status
        self.__import_campaign_report_summary_scenario_all(report_path, camp_id)
    
    def get_scenario_history(self, scenario_name=None, size=None):
        client = self.__get_db_client()
        placeholder = client._get_sql_placeholder()
        
        # Get data from DB
        where_clause = ""
        where_data = []
        if scenario_name is not None:
            where_clause = f"where name = {placeholder}"
            where_data.append(scenario_name)
        
        query_str = f'''
            SELECT *
            FROM campaign_scenarios
            {where_clause}
            ORDER BY name, status_at DESC 
        '''
        camp_scenarios_gen = client.execute(query_str, *where_data, result_as_dict_list=True, as_generator=True)
        
        # Build result
        res = []
        cur_scenario_name = None
        cur_scenario_statuses = None
        for cs in camp_scenarios_gen:
            # Manage new scenario
            if cur_scenario_name is None or cur_scenario_name != cs['name']:
                cur_scenario_statuses = []
                cur_scenario_name = cs['name']
                res.append({'name':cur_scenario_name, 'statuses':cur_scenario_statuses})
            
            # Add campaign info for this scenario execution if size limit is not reached
            if size is None or len(cur_scenario_statuses) < size:
                cur_scenario_statuses.append({'at':cs['status_at'], 'status':cs['status']})
            
        return res
        
    def add_campaign_if_needed(self, name, report_path):
        filter_data = {'report_path': report_path}
        if not self.__campaigns_table_manager.has_data(filter_data):
            self.__campaigns_table_manager.add_data(filter_data, {'name': name})
        camp = self.__campaigns_table_manager.get_data(filter_data)
        return camp['id']
    
    def update_or_add_campaign_scenario(self, campaign_id, name, *, report_path=None, status=None, status_at_str=None, details=None):
        filter_data = {'campaign_id': campaign_id, 'name': name}
        data = {}
        if report_path is not None:
            data['report_path'] = report_path
        if status is not None:
            data['status'] = status
        if status_at_str is not None:
            data['status_at'] = status_at_str
        if details is not None:
            data['details'] = details
        
        self.__campaign_scenarios_table_manager.update_or_add_data(filter_data, data)
        # camp_sce = self.__campaign_scenarios_table_manager.get_data(filter_data)
        # return camp_sce['id']
    
    def __import_campaign_report_summary_scenario_all(self, report_path, camp_id):
        file_path = os.path.join(report_path, 'report_summary_scenario_all.txt')
        lines = File(file_path, mode='rt').readlines(strip_newline=True)
        
        for line in lines:
            parts = line.split(' - ')
            status_dt_str = parts[0]
            scenario_name = parts[1]
            status_info = parts[-1]
            
            m = re.match(r"^(.*?)(?: \(.*\))?$", status_info)
            status = m.group(1)
            
            self.update_or_add_campaign_scenario(camp_id, scenario_name, status=status, status_at_str=status_dt_str)
        


