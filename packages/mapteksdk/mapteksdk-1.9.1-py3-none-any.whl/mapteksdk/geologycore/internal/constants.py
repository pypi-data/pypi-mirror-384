"""Constants used throughout the geologycore module.

Warnings
--------
Vendors and clients should not develop scripts or applications against this
file.
"""
###############################################################################
#
# (C) Copyright 2022, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from collections import namedtuple

_DatabaseConstants = namedtuple("_DatabaseConstants", [
  "VERSION", # The version of the database schema.
  "NAME", # The name of a table or field.
  "DESCRIPTION", # The description of a table or field.
  "UNIT", # The unit of a field.
  "TABLES", # The list of tables in a database.
  "TABLE_TYPE", # The type of a table.
  "FIELDS", # The list of fields in a table.
  "FIELD_TYPE", # The type of a field (e.g. Assay).
  "FIELD_DATA_TYPE", # The type of data stored in a field (e.g. integer).
])
"""The class of DatabaseConstants.

This is a namedtuple to make the constants defined here immutable.
"""

_FieldTypeConstants = namedtuple("_FieldTypeConstants", [
  "BOOLEAN", "INTEGER_32_S", "FLOAT", "DOUBLE", "STRING", "DATETIME"
])
"""The class of FieldTypeConstants.

This is a namedtuple to make the constants defined here immutable.
"""

DATABASE_CONSTANTS = _DatabaseConstants(
  VERSION="Version",
  NAME="Name",
  DESCRIPTION="Description",
  UNIT="Unit",
  TABLES="Tables",
  TABLE_TYPE="Table type",
  FIELDS="Fields",
  FIELD_TYPE="Field type",
  FIELD_DATA_TYPE="Type"
)
"""Constants representing the fields used to describe a drillhole database.

These are the names of the fields in the JSON objects used to represent
the schema of a Drillhole Database in JSON.
"""

FIELD_TYPE_CONSTANTS = _FieldTypeConstants(
  BOOLEAN="Boolean",
  INTEGER_32_S="Int32s",
  FLOAT="Float",
  DOUBLE="Double",
  STRING="String",
  DATETIME="DateTime",
)
"""Constants representing the field data types."""
