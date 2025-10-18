#!/usr/bin/env python
# -*- coding: utf-8 -*-

from style_transfer.libs.base_transfer import BaseTransfer
from style_transfer.libs.fast_photo_style_transfer.fast_photo_style_transfer import (
    FastPhotoStyleTransfer,
)
from typing import Dict, Type


class TransferFactory:

    transfer_map: Dict[str, Type[BaseTransfer]] = {
        "fast_photo_style": FastPhotoStyleTransfer,
    }

    @classmethod
    def create(cls, transfer_type: str) -> BaseTransfer:
        """Create the reference tranfer object."""

        if transfer_type not in cls.transfer_map:
            raise Exception(
                "The transfer type is unknown. "
                + f"Please use transfer types in {list(cls.transfer_map.keys())}."
            )

        tgt = cls.transfer_map.get(transfer_type)()
        return tgt
