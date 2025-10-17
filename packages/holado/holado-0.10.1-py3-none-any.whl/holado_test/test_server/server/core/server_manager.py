
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
from behave.model_core import Status
from holado_core.common.tools.tools import Tools
import logging
# from holado_report.report.builders.json_execution_historic_report_builder import JsonExecutionHistoricReportBuilder
from holado_report.report.builders.detailed_scenario_failed_report_builder import DetailedScenarioFailedReportBuilder
from holado_report.report.builders.summary_report_builder import SummaryReportBuilder
from holado_report.report.builders.summary_scenario_failed_report_builder import SummaryScenarioFailedReportBuilder
from holado_report.report.builders.short_scenario_failed_report_builder import ShortScenarioFailedReportBuilder
from holado_report.report.reports.base_report import BaseReport
from holado_scripting.common.tools.evaluate_parameters import EvaluateParameters
from holado_report.report.builders.summary_scenario_report_builder import SummaryScenarioReportBuilder
from holado_report.report.builders.failure_report_builder import FailureReportBuilder
from holado_report.campaign.campaign_manager import CampaignManager
# from holado_core.scenario.scenario_duration_manager import ScenarioDurationManager

logger = logging.getLogger(__name__)




class TestServerManager(object):
    """ Manage test server
    """
    
    def __init__(self):
        super().__init__()
        
        self.__campaign_manager = CampaignManager(db_name="server/campaigns")
    
    def initialize(self, resource_manager):
        self.__campaign_manager.initialize(resource_manager)
    
    @property
    def campaign_manager(self):
        return self.__campaign_manager
    
    



