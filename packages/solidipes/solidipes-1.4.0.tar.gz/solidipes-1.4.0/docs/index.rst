.. Solidipes documentation master file, created by
   sphinx-quickstart on Wed Nov  9 22:59:45 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Solidipes' documentation!
====================================

.. image:: https://gitlab.com/solidipes/solidipes/-/raw/main/logos/solidipes.png
   :width: 180px
   :align: center

Solidipes is a Python package designed to support scientists throughout the entire lifecycle of their research data: **acquisition, curation, publication, and sharing**.
It is named after *Armillaria solidipes*, the species of the largest living organism on Earth, a fungus forming an underground network spanning 9 km\ :sup:`2`.
Solidipes can be deployed as a web platform, providing an intuitive interface for visualizing research data. This interface guides scientists in adhering to best practices for dataset publication, assisting them in writing essential documentation and setting appropriate metadata. Ultimately, the curated datasets can be seamlessly uploaded to Zenodo for dissemination.
By using Solidipes, your community can overcome existing barriers to data sharing, ensuring that research outputs adhere to the **FAIR principles** (Findable, Accessible, Interoperable, and Reusable).

Solidipes was created within the scope of the `DCSM project <https://dcsm.readthedocs.io/>`_ (Dissemination of Computational Solid Mechanics), funded by `ETH Board <https://ethrat.ch/en/eth-domain/open-research-data/>`_ through an Open Research Data (ORD) "Explore" grant. Its development is a collaborative effort between the `LSMS <https://www.epfl.ch/labs/lsms/>`_\ [#affiliation_EPFL]_, `ENAC-IT4Research <https://www.epfl.ch/schools/enac/about/data-at-enac/enac-it4research/>`_\ [#affiliation_EPFL]_, the `LASTRO <https://www.epfl.ch/labs/lastro/>`_\ [#affiliation_EPFL]_, and the `EPFL Library <https://www.epfl.ch/campus/library/>`_\ [#affiliation_EPFL]_.

.. rubric:: Affiliations

.. [#affiliation_EPFL] `École Polytechnique Fédérale de Lausanne (EPFL) <https://www.epfl.ch/>`_, Switzerland

If you want to use Solidipes, please refer to the :ref:`User Guide<user-guide>` section.
Additionally, we offer an institutional deployment of Solidipes, `dcms.epfl.ch <https://dcsm.epfl.ch/dcsm-intranet/>`_, providing a centralized repository where datasets undergoing curation or intended for sharing can be efficiently stored. This platform is currently being utilized to significantly enhance the data curation process for the **Diamond open-access** `Journal of Theoretical, Computational and Applied Mechanics (JTCAM) <https://jtcam.episciences.org/>`_.


If you are interested in contributing to the development of Solidipes, please see the :ref:`Developer Guide<developer-guide>` section.


.. raw:: html

	 <video width="100%" controls>
	 <source src="https://gitlab.renkulab.io/guillaume.anciaux/solidipes-documentation-videos/-/raw/master/data/final_videos/solidipes-intro.mp4?ref_type=heads&inline=false" type="video/mp4"> Your browser does not support the video tag.</video>

|


.. toctree::
   :maxdepth: 2
   :caption: Contents

   src/user/index.rst
   src/developer/index.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
