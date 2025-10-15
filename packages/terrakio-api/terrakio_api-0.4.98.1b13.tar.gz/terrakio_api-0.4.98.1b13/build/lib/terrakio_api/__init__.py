# terrakio_api/__init__.py
"""
Terrakio API Client

An API client for Terrakio.
"""

__version__ = "0.4.6"
from terrakio_core import AsyncClient as CoreAsyncClient
from terrakio_core import Client as CoreClient
from functools import wraps

def create_blocked_method(original_method, reason=None):
    """Create a blocked version of a method that preserves signature."""
    method_name = getattr(original_method, '__name__', str(original_method))
    reason = reason or f"not available for the current client"
    
    @wraps(original_method)
    def blocked_method(*args, **kwargs):
        raise AttributeError(f"{method_name} is {reason}")
    
    return blocked_method


class AsyncClient(CoreAsyncClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_method_blocks()
    
    def _apply_method_blocks(self):
        """Apply blocks to restricted methods across different modules."""
        
        # Define blocked methods by module
        blocked_methods = {
            'datasets': {
                'methods': ['create_dataset', 'update_dataset', 'overwrite_dataset', 'delete_dataset'],
                'reason': 'not available for dataset operations(user_level)'
            },
            'users': {
                'methods': ['get_user_by_id', 'get_user_by_email', 'edit_user', 
                           'delete_user', 'list_users', 'reset_quota'],
                'reason': 'not available for user management(user_level)'
            },
            'mass_stats': {
                'methods': ['create_pyramids'],
                'reason': 'not available for mass statistics(user_level)'
            },
            'groups': {
                'methods': ['list_groups', 'get_groups', 'delete_group', 'create_group'],
                'reason': 'not available for group management(user level)'
            },
            'space': {
                'methods': ['delete_data_in_path'],
                'reason': 'not available for space management(user level)'
            }
        }
        
        # Apply blocks
        for module_name, config in blocked_methods.items():
            module = getattr(self, module_name, None)
            if module is None:
                continue
                
            for method_name in config['methods']:
                original_method = getattr(module, method_name, None)
                if original_method is not None:
                    blocked_method = create_blocked_method(original_method, config['reason'])
                    setattr(module, method_name, blocked_method)


class Client(CoreClient):
    """Synchronous version of the Terrakio API client with user-level restrictions."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_method_blocks()
    
    def _apply_method_blocks(self):
        """Apply blocks to restricted methods across different modules."""
        
        # Define blocked methods by module (same as async version)
        blocked_methods = {
            'datasets': {
                'methods': ['create_dataset', 'update_dataset', 'overwrite_dataset', 'delete_dataset'],
                'reason': 'not available for dataset operations(user_level)'
            },
            'users': {
                'methods': ['get_user_by_id', 'get_user_by_email', 'edit_user', 
                           'delete_user', 'list_users', 'reset_quota'],
                'reason': 'not available for user management(user_level)'
            },
            'mass_stats': {
                'methods': ['create_pyramids'],
                'reason': 'not available for mass statistics(user_level)'
            },
            'groups': {
                'methods': ['list_groups', 'get_groups', 'delete_group', 'create_group'],
                'reason': 'not available for group management(user level)'
            },
            'space': {
                'methods': ['delete_data_in_path'],
                'reason': 'not available for space management(user level)'
            }
        }
        
        # Apply blocks
        for module_name, config in blocked_methods.items():
            module = getattr(self, module_name, None)
            if module is None:
                continue
                
            for method_name in config['methods']:
                original_method = getattr(module, method_name, None)
                if original_method is not None:
                    blocked_method = create_blocked_method(original_method, config['reason'])
                    setattr(module, method_name, blocked_method)


__all__ = ['AsyncClient', 'Client']