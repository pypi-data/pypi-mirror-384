######################################################################################################
#                                 Auto-generated Metaflow stub file                                  #
# MF version: 2.18.12                                                                                #
# Generated on 2025-10-15T20:44:18.141668                                                            #
######################################################################################################

from __future__ import annotations

import metaflow
import typing
if typing.TYPE_CHECKING:
    import metaflow.decorators

from ...metadata_provider.metadata import MetaDatum as MetaDatum

TASK_ID_XCOM_KEY: str

FOREACH_CARDINALITY_XCOM_KEY: str

K8S_XCOM_DIR_PATH: str

def safe_mkdir(dir):
    ...

def push_xcom_values(xcom_dict):
    ...

class AirflowInternalDecorator(metaflow.decorators.StepDecorator, metaclass=type):
    def task_pre_step(self, step_name, task_datastore, metadata, run_id, task_id, flow, graph, retry_count, max_user_code_retries, ubf_context, inputs):
        ...
    def task_finished(self, step_name, flow, graph, is_task_ok, retry_count, max_user_code_retries):
        ...
    ...

