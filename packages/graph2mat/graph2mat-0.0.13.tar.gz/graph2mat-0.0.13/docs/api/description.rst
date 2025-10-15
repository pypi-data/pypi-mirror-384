Comprehensive description
=========================

In this section we will highlight the most important aspects of the
`graph2mat` API, trying to give a nice high level overview of what
the package has to offer and how it works.

Core functionality
------------------

.. currentmodule:: graph2mat

These are classes that can be imported like:

.. code-block:: python

    from graph2mat import X

    # or

    import graph2mat
    graph2mat.X

They represent the core of `graph2mat`'s functionality, which can be then
extended to suit particular needs.

Graph2Mat
*********

The center of the package is the `Graph2Mat` class.

.. autosummary::
    :toctree: api-generated/
    :template: autosummary/custom-class-template.rst

    Graph2Mat

It implements the skeleton to convert graphs to matrices.
The rest of the package revolves around this class, to:

- Help handling data.
- Help defining its architecture.
- Implement functions to be usedd within `Graph2Mat`.
- Provide helpers for training models.
- Ease its use for particular applications.

Basis
********

A 3D point cloud might have points with different basis functions, which results
in blocks of different size and shape in the matrix. Keeping information of the
basis is crucial to determine the architecture of the `Graph2Mat` model,
as well as to process data in the right way.

A unique point type with a certain basis is represented by a `PointBasis` instance,
while basis tables store all the unique point types that appear in the dataset and
therefore the model should be able to handle. Basis tables have helper methods to
aid with reshaping model outputs or disentangling batches of data, for example.

.. autosummary::
    :toctree: api-generated/
    :template: autosummary/custom-class-template.rst

    PointBasis
    BasisTableWithEdges
    AtomicTableWithEdges

Data containers
***************

These classes are used to store the data of your dataset.

`BasisConfiguration` and `OrbitalConfiguration` are used to store the raw information
of a structure, including its coordinates, atomic numbers and corresponing matrix.

`BasisMatrixDataBase` (and its subclasses) is a container that stores the configuration in the shape of a graph,
ready to be used by models. It contains, for example, information about the edges. This
class is ready to be batched. However, the `BasisMatrixDataBase` class is just a base class
and you are never going to use it directly. Instead, you will use a subclass of it that handles
a given type of arrays (e.g. `numpy` arrays, `torch` tensors...). The core library provides
one for `numpy` arrays, `BasisMatrixData`. For the variant that deals with `torch` tensors
for example, you will need to use the subclass provided in `graph2mat.bindings.torch`.

.. autosummary::
    :toctree: api-generated/
    :template: autosummary/custom-class-template.rst

    BasisMatrixDataBase
    BasisMatrixData
    BasisConfiguration
    OrbitalConfiguration

Formats
*******

Handling sparse matrices for associated 3D point clouds with basis functions is sometimes
not straightforward. For each different task (e.g. training a ML model, computing a property...)
there might be some data format that is more convenient. To the user (and the developer), converting
from any format to any other target format can be a pain. In `graph2mat`, we try to centralize
this task by:

- Having a class, `Formats`, that contains all the formats that we support.
- Having a class that manages the conversions between these formats: `ConversionManager``.

An instance of `ConversionManager` is available at ``graph2mat.conversions``, which all
the conversions implemented by graph2mat. See them here: :ref:`g2m.conversions`.

.. autosummary::
    :toctree: api-generated/
    :template: autosummary/custom-class-template.rst

    Formats
    ConversionManager

Other useful top level modules
*******************************

These are some other modules which contain helper functions that might be useful to you.
FOr example, the `metrics` module contains functions that you can use as loss functions
to train your models.

.. autosummary::
    :toctree: api-generated/
    :template: autosummary/custom-module-template.rst

    metrics
    sparse

Bindings
---------

Bindings are essential to use `graph2mat` in combination with other libraries. The core
of `graph2mat` is agnostic to the library you use, and you should choose the bindings
that you need for your specific use case.

Torch
*****

.. currentmodule:: graph2mat.bindings.torch

These are classes that can be imported like:

.. code-block:: python

    from graph2mat.bindings.torch import X

    # or

    import graph2mat.bindings.torch

    graph2mat.bindings.torch.X

Torch bindings implement **extensions of the core data functionality to make it usable in** `torch`.

The `TorchBasisMatrixData` is just a version of `BasisMatrixData` that uses `torch` tensors
instead of `numpy` arrays.

The `TorchBasisMatrixDataset` is a wrapper around `torch.utils.data.Dataset`
that creates `TorchBasisMatrixData` instances for each example in your dataset. It can therefore
be used with `torch_geometric`'s `DataLoader` to create batches of `TorchBasisMatrixData` instances.

.. autosummary::
    :toctree: api-generated/
    :template: autosummary/custom-class-template.rst

    TorchBasisMatrixData
    TorchBasisMatrixDataset

The bindings also implement a version of `Graph2Mat` that deals with `torch` tensors
and is ready to be used for training models with `torch`.

.. autosummary::
    :toctree: api-generated/
    :template: autosummary/custom-class-template.rst

    TorchGraph2Mat

E3nn
*****

.. currentmodule:: graph2mat.bindings.e3nn

These are classes that can be imported like:

.. code-block:: python

    from graph2mat.bindings.e3nn import X

    # or

    import graph2mat.bindings.e3nn

    graph2mat.bindings.e3nn.X

Here's a table of the e3nn bindings that are available. There's `E3nnGraph2Mat`, which
is just an extension of the ``Graph2Mat`` model that handles `e3nn`'s irreps. And then
there are implementations of blocks that you might use within your model.

+----------------------------+----------------------+
| Class                      | Type of block        |
+============================+======================+
| `E3nnGraph2Mat`            | Model                |
+----------------------------+----------------------+
| `E3nnInteraction`          | Preprocessing        |
+----------------------------+----------------------+
| `E3nnEdgeMessageBlock`     | Preprocessing (edges)|
+----------------------------+----------------------+
| `E3nnSimpleNodeBlock`      | Node block readout   |
+----------------------------+----------------------+
| `E3nnSeparateTSQNodeBlock` | Node block readout   |
+----------------------------+----------------------+
| `E3nnSimpleEdgeBlock`      | Edge block readout   |
+----------------------------+----------------------+

Tools
-----

The ``graph2mat.tools`` module contains code that it is not per se graph2mat
functionality, but can be very useful within its day to day use.

Lightning
*********

.. currentmodule:: graph2mat.tools.lightning

These are tools for pytorch lightning. They can be imported like:

.. code-block:: python

    from graph2mat.tools.lightning import X

    # or

    import graph2mat.tools.lightning

    graph2mat.tools.lightning.X

.. note::

    Apart from the tools listed below, which can be used from python, we also provide a full
    pytorch lightning Command Line Interface (CLI) for those who want to train models from the
    command line. See the :doc:`CLI tutorials <../tutorials/cli/index>` for more information.

`Pytorch Lightning <https://lightning.ai/docs/pytorch/stable/>`_ is a very nice library to
facilitate the training of models with ``torch``. Their main training flow is based around
the ``Trainer`` class. We recommend going through their documentation to understand how
things are meant to be used. In short, the trainer needs a model, a data module and
can use callbacks. We provide these three pieces specifically tailored for the ``graph2mat``
framework so that you can start using ``lightning`` right away with little to no friction.

**Models**

.. autosummary::
    :toctree: api-generated/
    :template: autosummary/custom-class-template.rst

    LitBasisMatrixModel
    models.mace.LitMACEMatrixModel

**Data modules**

.. autosummary::
    :toctree: api-generated/
    :template: autosummary/custom-class-template.rst

    MatrixDataModule

**Callbacks**

.. autosummary::
    :toctree: api-generated/
    :template: autosummary/custom-class-template.rst

    MatrixWriter
    SamplewiseMetricsLogger
    PlotMatrixError
