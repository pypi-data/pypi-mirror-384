from builtins import super
from holado.common.context.session_context import SessionContext
import logging

logger = logging.getLogger(__name__)


class TestServerSessionContext(SessionContext):
    
    def __init__(self):
        super().__init__("TestServerSession")
        
    def configure(self, session_kwargs=None):
        logger.info("Configuring TestServerSessionContext")
        
        super().configure(session_kwargs)
        
        # Override default registered modules
         

        
        # Register new modules
        
        from holado_test.test_server.server.core.server_manager import TestServerManager
        self.services.register_service_type("server_manager", TestServerManager,
                            lambda m: m.initialize(self.resource_manager) )
        
        
        
    def initialize(self, session_kwargs=None):
        if session_kwargs is None:
            session_kwargs = {}
        # raise_if_not_exist = session_kwargs.get("raise_if_not_exist", True)
        # do_import = session_kwargs.get("import_compiled_proto", True)
        
        # Call default initialization
        super().initialize(session_kwargs)
        
        
        
        
        
