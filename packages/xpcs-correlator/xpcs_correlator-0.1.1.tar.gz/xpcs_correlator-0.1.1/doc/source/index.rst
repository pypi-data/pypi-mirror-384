.. XPCS Correlator documentation master file, created by
   sphinx-quickstart on Tue Aug 27 11:14:10 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to XPCS Correlator's documentation!
===========================================

XPCS Correlator is a Python package for calculating the correlation functions of X-ray \
Photon Correlation Spectroscopy (XPCS) data to support activities of ESRF beamlines. \
It is designed  to be used  with the dense data format but in future it will support other \
sparse formats as well. Currently, it is mainly optimized for CPU distributed processing of \
the data using the Dask library.

.. toctree::
   :maxdepth: 1
   :caption: Contents:
   
   installation
   XPCS basics <xpcs_introduction>
   Calculation Basics <calculation_basics>
   Tutorial <tutorial>
   API <api/modules>

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. autosummary::
   :toctree: _autosummary

