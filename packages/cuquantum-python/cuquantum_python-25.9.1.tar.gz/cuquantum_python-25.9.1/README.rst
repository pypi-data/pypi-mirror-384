*****************************************************************************************************
cuQuantum Python: A High-Performance Library for Accelerating Quantum Computing Simulations in Python
*****************************************************************************************************

NVIDIA cuQuantum Python provides Python bindings and high-level object-oriented models for accessing the full 
functionalities of `NVIDIA cuQuantum SDK <https://developer.nvidia.com/cuquantum-sdk>`_ from Python.

Documentation
=============

For detailed guide, please refer to `cuQuantum Python documentation <https://docs.nvidia.com/cuda/cuquantum/latest/python/index.html>`_.

Installation
============

.. code-block:: bash

   pip install -v --no-cache-dir cuquantum-python

.. note::

   Starting cuQuantum 22.11, this package is a meta package pointing to ``cuquantum-python-cuXX``,
   where XX is the CUDA major version (currently CUDA 12 & 13 are supported).
   The meta package will attempt to infer and install the correct ``-cuXX`` wheel. 
   The auto-detection mechanism is not guaranteed to work in certain environments, and users are encouraged to install the new wheels that
   come *with* the ``-cuXX`` suffix.

   The argument ``--no-cache-dir`` is required for pip 23.1+. It forces pip to execute the
   auto-detection logic.


Citing cuQuantum
================

`H. Bayraktar et al., "cuQuantum SDK: A High-Performance Library for Accelerating Quantum Science," 2023 IEEE International Conference on Quantum Computing and Engineering (QCE), Bellevue, WA, USA, 2023, pp. 1050-1061, doi: 10.1109/QCE57702.2023.00119 <https://doi.org/10.1109/QCE57702.2023.00119>`_
