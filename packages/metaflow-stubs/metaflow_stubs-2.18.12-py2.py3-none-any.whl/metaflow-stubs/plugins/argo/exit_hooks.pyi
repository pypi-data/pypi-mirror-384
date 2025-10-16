######################################################################################################
#                                 Auto-generated Metaflow stub file                                  #
# MF version: 2.18.12                                                                                #
# Generated on 2025-10-15T20:44:18.170200                                                            #
######################################################################################################

from __future__ import annotations

import typing
import metaflow
if typing.TYPE_CHECKING:
    import metaflow.plugins.argo.exit_hooks


class JsonSerializable(object, metaclass=type):
    def to_json(self):
        ...
    def __str__(self):
        ...
    ...

class Hook(object, metaclass=type):
    """
    Abstraction for Argo Workflows exit hooks.
    A hook consists of a Template, and one or more LifecycleHooks that trigger the template
    """
    def __init__(self, template: _Template, lifecycle_hooks: typing.List["_LifecycleHook"]):
        """
        The type of the None singleton.
        """
        ...
    ...

class HttpExitHook(Hook, metaclass=type):
    def __init__(self, name: str, url: str, method: str = 'GET', headers: typing.Optional[typing.Dict] = None, body: typing.Optional[str] = None, on_success: bool = False, on_error: bool = False):
        ...
    ...

class ExitHookHack(Hook, metaclass=type):
    def __init__(self, url, headers = None, body = None):
        ...
    ...

class ContainerHook(Hook, metaclass=type):
    def __init__(self, name: str, container: typing.Dict, service_account_name: str = None, on_success: bool = False, on_error: bool = False):
        ...
    ...

