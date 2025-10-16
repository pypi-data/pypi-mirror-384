import logging
import py4heappe.heappe_v5.core.base.logger as logger

logger = logging.getLogger(__name__)

class Py4HEAppEException(Exception):     
    """         
        Base Py4HEAppE Exception
    """
    def __init__(self,  message: str):
        self.message = message
        logger.error(message)
        super().__init__(self.message)

class Py4HEAppEInternalException(Py4HEAppEException):     
    """         
        Py4HEAppE Internal Exception
    """
    def __init__(self,  message: str):
        self.message = message

class Py4HEAppEAPIException(Py4HEAppEException):     
    """         
        Py4HEAppE API Exception
    """
    def __init__(self, title: str, message: str, error_code: int | None = None):
        if error_code is not None:            
            self.message = f"Status Code: {error_code}, {title}: {message}"
        else:
            self.message = f"{title}: {message}"
        super().__init__(self.message)

class Py4HEAppEAPIInternalException(Py4HEAppEException):     
    """         
        Py4HEAppE API Internal Exception
    """
    def __init__(self, title: str, message: str, error_code: int | None = None):
        if error_code is not None:            
            self.message = f"Status Code: {error_code}, {title}: {message}"
        else:
            self.message = f"{title}: {message}"