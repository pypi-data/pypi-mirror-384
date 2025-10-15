#!/usr/bin/env python
# -*- coding: utf-8 -*-

from color_transfer.libs.base_transfer import BaseTransfer
from color_transfer.libs.mean_std_transfer import MeanStdTransfer
from color_transfer.libs.lab_transfer import LabTransfer
from color_transfer.libs.pdf_transfer import PDFTransfer
from typing import Dict, Type


class TransferFactory:

    transfer_map: Dict[str, Type[BaseTransfer]] = {
        "mean_std": MeanStdTransfer,
        "lab": LabTransfer,
        "pdf": PDFTransfer,
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
