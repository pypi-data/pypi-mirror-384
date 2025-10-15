#
#   Imandra Inc.
#
#   model_status.py
#

from enum import StrEnum
from pydantic import BaseModel
from imandra.u.agents.code_logician.base import FormalizationStatus

class SrcCodeStatus(StrEnum):
    """  """
    SRC_CODE_CURRENT = 'Source_code_current'
    SRC_CODE_CHANGED = 'Source_code_changed'
    SRC_CODE_DELETED = 'Source_code_deleted'

class ModelStatus(BaseModel):
    """ Represents the collective status of a model """

    src_code_status : SrcCodeStatus
    instructions_added : bool
    deps_changed : bool
    deps_need_formalization : bool
    formalization_status : FormalizationStatus

    def src_code_changed (self):
        """ Return True if source code changed """
        return self.src_code_status == SrcCodeStatus.SRC_CODE_CHANGED

    def toJSON(self):
        """ return a nice dict with the status """
        return self.model_dump_json()

    @staticmethod
    def fromJSON(d):
        """ Translated a JSON into ModelStatus object """
        return ModelStatus.model_validate_json(d)

    def __repr__(self):
        """ repr """

        s = f"Model Status:\n"
        s += f"Source code status: { self.src_code_status.name }\n"
        s += f"Instructions added: { "Yes" if self.instructions_added else "No" }\n"
        s += f"Dependencies changed: { "Yes" if self.deps_changed else "No" }\n"
        s += f"Formalization status: { self.formalization_status.name }\n"

        return s
