#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""RDM model for oarepo-model package."""

from __future__ import annotations

from .presets import rdm_basic_preset, rdm_complete_preset, rdm_minimal_preset

__all__ = (
    "rdm_basic_preset",
    "rdm_complete_preset",
    "rdm_minimal_preset",
)
