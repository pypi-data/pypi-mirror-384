#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module to generate permission policy class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_rdm_records.services.permissions import RDMRecordPermissionPolicy
from invenio_records_permissions.policies.records import RecordPermissionPolicy
from oarepo_model.customizations import ChangeBase, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMPermissionPolicyPreset(Preset):
    """Preset for record service class."""

    modifies = ("PermissionPolicy",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield ChangeBase(
            "PermissionPolicy",
            RecordPermissionPolicy,
            RDMRecordPermissionPolicy,
            subclass=True,
        )
