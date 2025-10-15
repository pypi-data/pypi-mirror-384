#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""RDM presets for OARepo models.

This package provides presets for configuring Invenio RDM
components for OARepo models.
"""

from __future__ import annotations

from oarepo_rdm.model.presets.rdm.ext import RDMExtPreset
from oarepo_rdm.model.presets.rdm.records.draft_record import RDMDraftRecordPreset
from oarepo_rdm.model.presets.rdm.records.draft_record_metadata import (
    RDMDraftRecordMetadataWithFilesPreset,
)
from oarepo_rdm.model.presets.rdm.records.parent_record import RDMParentRecordPreset
from oarepo_rdm.model.presets.rdm.records.rdm_mapping import RDMMappingPreset
from oarepo_rdm.model.presets.rdm.records.record import RDMRecordPreset
from oarepo_rdm.model.presets.rdm.records.record_metadata import (
    RDMRecordMetadataWithFilesPreset,
)
from oarepo_rdm.model.presets.rdm.resources.records.resource import (
    RDMRecordResourcePreset,
)
from oarepo_rdm.model.presets.rdm.resources.records.resource_config import (
    RDMRecordResourceConfigPreset,
)
from oarepo_rdm.model.presets.rdm.services.records.permission_policy import (
    RDMPermissionPolicyPreset,
)
from oarepo_rdm.model.presets.rdm.services.records.rdm_parent_record_schema import (
    RDMParentRecordSchemaPreset,
)
from oarepo_rdm.model.presets.rdm.services.records.rdm_record_schema import (
    RDMRecordSchemaPreset,
)
from oarepo_rdm.model.presets.rdm.services.records.service import RDMRecordServicePreset
from oarepo_rdm.model.presets.rdm.services.records.service_config import (
    RDMRecordServiceConfigPreset,
)
from oarepo_rdm.model.presets.rdm.services.records.service_config_links import (
    RDMServiceConfigLinks,
)
from oarepo_rdm.model.presets.rdm.services.records.service_config_ui_links import (
    RDMServiceConfigUILinks,
)

rdm_static_preset = [
    RDMMappingPreset,
    RDMDraftRecordPreset,
    RDMParentRecordPreset,
    RDMRecordPreset,
    RDMRecordResourcePreset,
    RDMRecordResourceConfigPreset,
    RDMRecordServicePreset,
    RDMRecordServiceConfigPreset,
    RDMDraftRecordMetadataWithFilesPreset,
    RDMRecordMetadataWithFilesPreset,
    RDMExtPreset,
    RDMRecordSchemaPreset,
    RDMParentRecordSchemaPreset,
    RDMServiceConfigLinks,
    RDMServiceConfigUILinks,
    RDMPermissionPolicyPreset,
]
