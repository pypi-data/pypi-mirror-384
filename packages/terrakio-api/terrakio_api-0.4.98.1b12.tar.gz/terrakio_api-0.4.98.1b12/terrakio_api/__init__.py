# # terrakio_api/__init__.py
# """
# Terrakio API Client

# An API client for Terrakio.
# """

# __version__ = "0.4.98"
# from terrakio_core import AsyncClient as CoreAsyncClient
# from terrakio_core import Client as CoreClient
# from terrakio_core.endpoints.mass_stats import MassStats as CoreMassStats
# from terrakio_core.sync_client import SyncWrapper
# from functools import wraps
# from typing import cast

# def create_blocked_method(original_method, reason=None):
#     """Create a blocked version of a method that preserves signature."""
#     method_name = getattr(original_method, '__name__', str(original_method))
#     reason = reason or f"not available for the current client"
    
#     @wraps(original_method)
#     def blocked_method(*args, **kwargs):
#         raise AttributeError(f"{method_name} is {reason}")
    
#     return blocked_method


# # User-facing wrappers to provide narrowed signatures while preserving full method typing
# class _UserMassStatsAsync(CoreMassStats):
#     def __init__(self, client):
#         super().__init__(client)

#     async def create_collection(self, collection: str, collection_type: str = "basic"):
#         """Create a collection. Admin-only params 'bucket' and 'location' are not available in this client."""
#         return await super().create_collection(collection=collection, collection_type=collection_type)


# class _UserMassStatsSync(SyncWrapper):
#     """Sync wrapper exposing the narrowed create_collection signature."""

#     def create_collection(self, collection: str, collection_type: str = "basic"):
#         """Create a collection. Admin-only params 'bucket' and 'location' are not available in this client."""
#         create_collection = super().__getattr__('create_collection')
#         return create_collection(collection=collection, collection_type=collection_type)


# class AsyncClient(CoreAsyncClient):
#     mass_stats: CoreMassStats
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Rebind mass_stats to user-facing wrapper with narrowed signatures
#         self.mass_stats = _UserMassStatsAsync(self)
#         self._apply_method_blocks()
    
#     def _apply_method_blocks(self):
#         """Apply blocks to restricted methods across different modules."""
        
#         # Define blocked methods by module
#         blocked_methods = {
#             'datasets': {
#                 'methods': ['create_dataset', 'update_dataset', 'overwrite_dataset', 'delete_dataset'],
#                 'reason': 'not available for dataset operations(user_level)'
#             },
#             'users': {
#                 'methods': ['get_user_by_id', 'get_user_by_email', 'edit_user', 
#                            'delete_user', 'list_users', 'reset_quota'],
#                 'reason': 'not available for user management(user_level)'
#             },
#             'mass_stats': {
#                 'methods': ['create_pyramids'],
#                 'reason': 'not available for mass statistics(user_level)'
#             },
#             'groups': {
#                 'methods': ['list_groups_admin', 'get_group_admin', 'delete_group_admin', 'create_group_admin'],
#                 'reason': 'not available for group management(user level)'
#             },
#             'space': {
#                 'methods': ['delete_data_in_path'],
#                 'reason': 'not available for space management(user level)'
#             }
#         }
        
#         # Apply blocks
#         for module_name, config in blocked_methods.items():
#             module = getattr(self, module_name, None)
#             if module is None:
#                 continue
                
#             for method_name in config['methods']:
#                 original_method = getattr(module, method_name, None)
#                 if original_method is not None:
#                     blocked_method = create_blocked_method(original_method, config['reason'])
#                     setattr(module, method_name, blocked_method)


# class Client(CoreClient):
#     """Synchronous version of the Terrakio API client with user-level restrictions."""
#     mass_stats: CoreMassStats
    
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Rebind mass_stats to user-facing wrapper with narrowed signatures (sync)
#         self._async_client.mass_stats = _UserMassStatsAsync(self._async_client)
#         self.mass_stats = cast(CoreMassStats, _UserMassStatsSync(self._async_client.mass_stats, self))
#         self._apply_method_blocks()
    
#     def _apply_method_blocks(self):
#         """Apply blocks to restricted methods across different modules."""
        
#         # Define blocked methods by module (same as async version)
#         blocked_methods = {
#             'datasets': {
#                 'methods': ['create_dataset', 'update_dataset', 'overwrite_dataset', 'delete_dataset'],
#                 'reason': 'not available for dataset operations(user_level)'
#             },
#             'users': {
#                 'methods': ['get_user_by_id', 'get_user_by_email', 'edit_user', 
#                            'delete_user', 'list_users', 'reset_quota'],
#                 'reason': 'not available for user management(user_level)'
#             },
#             'mass_stats': {
#                 'methods': ['create_pyramids'],
#                 'reason': 'not available for mass statistics(user_level)'
#             },
#             'groups': {
#                 'methods': ['list_groups_admin', 'get_group_admin', 'delete_group_admin', 'create_group_admin'],
#                 'reason': 'not available for group management(user level)'
#             },
#             'space': {
#                 'methods': ['delete_data_in_path'],
#                 'reason': 'not available for space management(user level)'
#             }
#         }
        
#         # Apply blocks
#         for module_name, config in blocked_methods.items():
#             module = getattr(self, module_name, None)
#             if module is None:
#                 continue
                
#             for method_name in config['methods']:
#                 original_method = getattr(module, method_name, None)
#                 if original_method is not None:
#                     blocked_method = create_blocked_method(original_method, config['reason'])
#                     setattr(module, method_name, blocked_method)


# __all__ = ['AsyncClient', 'Client']


"""
Terrakio API Client

An API client for Terrakio.
"""

__version__ = "0.4.98"
from terrakio_core import AsyncClient as CoreAsyncClient
from terrakio_core import Client as CoreClient
from terrakio_core.endpoints.mass_stats import MassStats as CoreMassStats
from terrakio_core.sync_client import SyncWrapper
from functools import wraps
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    # This code only runs during type checking (IDE autocomplete)
    # We can lie to the type checker to get the autocomplete we want!
    
    class _UserMassStatsAsync(CoreMassStats):
        """Type hint: like CoreMassStats but create_collection is restricted."""
        async def create_collection(self, collection: str, collection_type: str = "basic"): ...
    
    class _UserMassStatsSync(CoreMassStats):
        """Type hint: like CoreMassStats but create_collection is restricted."""
        def create_collection(self, collection: str, collection_type: str = "basic"): ...
else:
    # This is the actual runtime implementation
    class _UserMassStatsAsync(CoreMassStats):
        """User-level mass stats with restricted create_collection signature."""
        
        async def create_collection(self, collection: str, collection_type: str = "basic"):
            """Create a collection. Admin-only params 'bucket' and 'location' are not available."""
            return await super().create_collection(collection=collection, collection_type=collection_type)
    
    class _UserMassStatsSync(SyncWrapper):
        """Sync wrapper with narrowed create_collection - all other methods via __getattr__."""
        
        def create_collection(self, collection: str, collection_type: str = "basic"):
            """Create a collection. Admin-only params 'bucket' and 'location' are not available."""
            coro = self._async_obj.create_collection(
                collection=collection, 
                collection_type=collection_type
            )
            return self._sync_client._run_async(coro)


def create_blocked_method(original_method, reason=None):
    """Create a blocked version of a method that preserves signature."""
    method_name = getattr(original_method, '__name__', str(original_method))
    reason = reason or f"not available for the current client"
    
    @wraps(original_method)
    def blocked_method(*args, **kwargs):
        raise AttributeError(f"{method_name} is {reason}")
    
    return blocked_method


class AsyncClient(CoreAsyncClient):
    mass_stats: _UserMassStatsAsync
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mass_stats = _UserMassStatsAsync(self)
        self._apply_method_blocks()
    
    def _apply_method_blocks(self):
        """Apply blocks to restricted methods across different modules."""
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
    mass_stats: _UserMassStatsSync
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._async_client.mass_stats = _UserMassStatsAsync(self._async_client)
        self.mass_stats = _UserMassStatsSync(self._async_client.mass_stats, self)
        self._apply_method_blocks()
    
    def _apply_method_blocks(self):
        """Apply blocks to restricted methods across different modules."""
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