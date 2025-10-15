# terrakio_api/__init__.py
"""
Terrakio API Client

An API client for Terrakio.
"""

__version__ = "0.4.98.1"
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


# User-facing wrappers to provide narrowed signatures with delegation
class _UserMassStatsAsync:
    def __init__(self, core_mass_stats):
        self._ms = core_mass_stats

    def __dir__(self):
        attrs = [attr for attr in dir(self._ms) if not attr.startswith('_')]
        wrapper_attrs = [attr for attr in object.__dir__(self) if not attr.startswith('_')]
        # Ensure the narrowed method appears
        if 'create_collection' not in wrapper_attrs:
            wrapper_attrs.append('create_collection')
        return list(set(attrs + wrapper_attrs))

    def __getattr__(self, name):
        return getattr(self._ms, name)

    async def create_collection(self, collection: str, collection_type: str = "basic"):
        """Create a collection. Admin-only params 'bucket' and 'location' are not available in this client."""
        return await self._ms.create_collection(collection=collection, collection_type=collection_type)


class _UserMassStatsSync:
    def __init__(self, sync_wrapper):
        # sync_wrapper is terrakio_core.sync_client.SyncWrapper over async mass_stats
        self._sw = sync_wrapper

    def __dir__(self):
        attrs = [attr for attr in dir(self._sw) if not attr.startswith('_')]
        wrapper_attrs = [attr for attr in object.__dir__(self) if not attr.startswith('_')]
        if 'create_collection' not in wrapper_attrs:
            wrapper_attrs.append('create_collection')
        return list(set(attrs + wrapper_attrs))

    def __getattr__(self, name):
        return getattr(self._sw, name)

    def create_collection(self, collection: str, collection_type: str = "basic"):
        """Create a collection. Admin-only params 'bucket' and 'location' are not available in this client."""
        return self._sw.create_collection(collection=collection, collection_type=collection_type)


class AsyncClient(CoreAsyncClient):
    mass_stats: "_UserMassStatsAsync"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rebind mass_stats to user-facing wrapper with narrowed signatures
        self.mass_stats = _UserMassStatsAsync(self.mass_stats)
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
                'methods': ['list_groups_admin', 'get_group_admin', 'delete_group_admin', 'create_group_admin'],
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
    mass_stats: "_UserMassStatsSync"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rebind mass_stats to user-facing wrapper with narrowed signatures (sync)
        self.mass_stats = _UserMassStatsSync(self.mass_stats)
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
                'methods': ['list_groups_admin', 'get_group_admin', 'delete_group_admin', 'create_group_admin'],
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