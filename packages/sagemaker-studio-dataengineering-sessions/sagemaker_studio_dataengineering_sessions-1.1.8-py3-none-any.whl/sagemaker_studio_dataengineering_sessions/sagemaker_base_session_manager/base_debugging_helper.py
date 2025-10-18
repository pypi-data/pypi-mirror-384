"""
Base debugging helper interface for SageMaker Studio Data Engineering Sessions.

This module provides an abstract base class that defines the interface for debugging helpers
used across different session managers.
"""

import abc
from typing import Any, Dict, Optional


class BaseDebuggingHelper(metaclass=abc.ABCMeta):
    """
    Abstract base class for debugging helpers.
    
    This interface defines the contract that all debugging helper implementations
    must follow, providing methods for retrieving and writing debugging information.
    """

    @abc.abstractmethod
    def get_debugging_info(self, **kwargs) -> Dict[str, Any]:
        """
        Retrieve debugging information for a session.
        
        Args:
            **kwargs: Additional parameters specific to the implementation.
            
        Returns:
            Dict[str, Any]: A dictionary containing debugging information with keys
                          representing different aspects of the system/session state.
                          
        Raises:
            NotImplementedError: If the method is not implemented by the subclass.
        """
        raise NotImplementedError("get_debugging_info must be implemented")

    @abc.abstractmethod
    def write_debugging_info(self, 
                           debugging_info: Dict[str, Any], 
                           cell_id: str,
                           **kwargs) -> bool:
        """
        Write debugging information to a specified output location.
        
        Args:
            debugging_info (Dict[str, Any]): The debugging information to write.
            output_path (Optional[str]): The path where to write the debugging info.
                                       If None, uses a default location.
            **kwargs: Additional parameters specific to the implementation.
            
        Returns:
            bool: True if the debugging information was successfully written,
                  False otherwise.
                  
        Raises:
            NotImplementedError: If the method is not implemented by the subclass.
        """
        raise NotImplementedError("write_debugging_info must be implemented")
