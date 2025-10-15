#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for creating RDM record service config.

This module provides a preset that modifies record service config to RDM compatibility.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_checks.components import ChecksComponent
from invenio_drafts_resources.services import (
    RecordServiceConfig as DraftRecordServiceConfig,
)
from invenio_rdm_records.services.components.files import (
    RDMDraftFilesComponent as InvenioRDMDraftFilesComponent,
)
from invenio_rdm_records.services.components.internal_notes import (
    InternalNotesComponent,
)
from invenio_rdm_records.services.components.pids import (
    ParentPIDsComponent,
    PIDsComponent,
)
from invenio_rdm_records.services.components.verified import ContentModerationComponent
from invenio_rdm_records.services.config import RDMRecordServiceConfig
from oarepo_model.customizations import AddToList, ChangeBase, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator, Mapping

    from invenio_records_resources.services.base.links import (
        NestedLinks,
    )
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMRecordServiceConfigWithoutLinks(RDMRecordServiceConfig):
    """TODO: this is just a quick hack before we have links working."""

    links_item: Mapping[str, Any] = {}
    nested_links_item: tuple[NestedLinks, ...] = ()


class RDMDraftFilesComponent(InvenioRDMDraftFilesComponent):
    """A replacement for RDM draft files component that also removes draft & record file components."""

    replaces = (
        InvenioRDMDraftFilesComponent,
        "oarepo_model.presets.records_resources.services.files.file_record_service_components.RecordFilesComponent",
        "oarepo_model.presets.drafts.services.files.draft_file_record_service_components.DraftFilesComponent",
        "oarepo_model.presets.drafts.services.files.draft_file_record_service_components.DraftMediaFilesComponent",
    )


class RDMRecordServiceConfigPreset(Preset):
    """Preset for record service class."""

    modifies = ("RecordServiceConfig", "record_service_components")

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        # replace components
        yield AddToList("record_service_components", RDMDraftFilesComponent)
        yield AddToList("record_service_components", PIDsComponent)
        yield AddToList("record_service_components", ParentPIDsComponent)
        yield AddToList("record_service_components", ContentModerationComponent)
        yield AddToList("record_service_components", InternalNotesComponent)
        yield AddToList("record_service_components", ChecksComponent)
        yield ChangeBase(
            "RecordServiceConfig",
            DraftRecordServiceConfig,
            RDMRecordServiceConfigWithoutLinks,
        )
