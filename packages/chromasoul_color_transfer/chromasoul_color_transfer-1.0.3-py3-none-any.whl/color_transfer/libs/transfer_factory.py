#!/usr/bin/env python
# -*- coding: utf-8 -*-

from color_transfer.libs.base_transfer import BaseTransfer
from color_transfer.libs.mean_std_transfer import MeanStdTransfer
from color_transfer.libs.lab_transfer import LABTransfer
from color_transfer.libs.pdf_transfer import PDFTransfer
from color_transfer.libs.lhm_transfer import LHMTransfer
from color_transfer.libs.pccm_transfer import PCCMTransfer
from color_transfer.libs.emd_transfer import EMDTransfer
from color_transfer.libs.sinkhorn_transfer import SinkhornTransfer
from typing import Dict, Type


class TransferFactory:

    transfer_map: Dict[str, Type[BaseTransfer]] = {
        "mean_std": MeanStdTransfer,
        "lab": LABTransfer,
        "pdf": PDFTransfer,
        "lhm": LHMTransfer,
        "pccm": PCCMTransfer,
        "emd": EMDTransfer,
        "sinkhorn": SinkhornTransfer,
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
