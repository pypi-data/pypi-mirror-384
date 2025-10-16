"""Functionality specific to GeologyCore.

The contents of this module are not guaranteed to function unless the connected
application is GeologyCore.

"""
###############################################################################
#
# (C) Copyright 2022, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from .database import DrillholeDatabase
from .desurvey_method import DesurveyMethod
from .drillholes import Drillhole
from .errors import (DatabaseVersionNotSupportedError, TableNotFoundError,
                     FieldTypeNotSupportedError, DataTypeNotSupportedError,
                     DuplicateFieldTypeError, FieldNotFoundError,
                     DuplicateFieldNameError, OrphanDrillholeError,
                     EmptyTableError, DuplicateTableTypeError,
                     MissingRequiredFieldsError, DeletedFieldError,
                     UnitNotSupportedError, FieldDoesNotSupportUnitsError,
                     DesurveyMethodNotSupportedError, DuplicateTableNameError)
from .fields import DrillholeFieldType
from .tables import (DrillholeTableType, BaseDrillholeTable)
