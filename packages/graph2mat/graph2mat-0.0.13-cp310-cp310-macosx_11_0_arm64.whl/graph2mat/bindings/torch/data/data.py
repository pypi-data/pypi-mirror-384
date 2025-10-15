"""Implements the Data class to use in pytorch models."""
from typing import Any, Optional

import torch

from torch_geometric.data.data import Data

from graph2mat.core.data import Formats, conversions
from graph2mat.core.data.processing import BasisMatrixDataBase, BasisMatrixData

__all__ = ["TorchBasisMatrixData"]


class TorchBasisMatrixData(BasisMatrixDataBase[torch.Tensor], Data):
    """Extension of ``BasisMatrixDataBase`` to be used within pytorch.

    All this class implements is the conversion of numpy arrays to torch tensors
    and back. The rest of the functionality is inherited from ``BasisMatrixDataBase``.

    Please refer to the documentation of ``BasisMatrixDataBase`` for more information.

    See Also
    --------
    graph2mat.BasisMatrixDataBase
        The class that implements the heavy lifting of the data processing.
    """

    _format = Formats.TORCH_BASISMATRIXDATA
    _data_format = Formats.TORCH_NODESEDGES
    _array_format = Formats.TORCH

    def __init__(self, *args, **kwargs):
        data = BasisMatrixDataBase._sanitize_data(self, **kwargs)
        Data.__init__(self, **data)

    def __getitem__(self, key: str) -> Any:
        return Data.__getitem__(self, key)

    @property
    def _data(self):
        return {**self._store}
