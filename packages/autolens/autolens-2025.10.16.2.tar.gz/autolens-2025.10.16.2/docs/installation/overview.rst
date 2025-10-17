.. _overview:

Overview
========

**PyAutoLens** requires Python 3.9 - 3.12 and support the Linux, MacOS and Windows operating systems.

**PyAutoLens** can be installed via the Python distribution `Anaconda <https://www.anaconda.com/>`_ or using
`Pypi <https://pypi.org/>`_ to ``pip install`` **PyAutoLens** into your Python distribution.

We recommend Anaconda as it manages the installation of many major libraries (e.g. numpy, scipy,
matplotlib, etc.) making installation more straight forward. Windows users must use Anaconda.

The installation guide for both approaches can be found at:

- `Anaconda installation guide <https://pyautolens.readthedocs.io/en/latest/installation/conda.html>`_

- `PyPI installation guide <https://pyautolens.readthedocs.io/en/latest/installation/pip.html>`_

Users who wish to build **PyAutoLens** from source (e.g. via a ``git clone``) should follow
our `building from source installation guide <https://pyautolens.readthedocs.io/en/latest/installation/source.html>`_.

Known Issues
------------

There is a known issue installing **PyAutoLens** via both ``conda`` and ``pip`` associated with the libraries ``llvmlite``
and ``numba``. If your installation raises an error mentioning either library, follow the instructions in
our `troubleshooting section <https://pyautolens.readthedocs.io/en/latest/installation/troubleshooting.html>`_.

Dependencies
------------

**PyAutoLens** has the following dependencies:

**PyAutoConf** https://github.com/rhayes777/PyAutoConf

**PyAutoFit** https://github.com/rhayes777/PyAutoFit

**PyAutoArray** https://github.com/Jammy2211/PyAutoArray

**PyAutoGalaxy** https://github.com/Jammy2211/PyAutoGalaxy

**dynesty** https://github.com/joshspeagle/dynesty

**emcee** https://github.com/dfm/emcee

**PySwarms** https://github.com/ljvmiranda921/pyswarms

**colossus**: https://bdiemer.bitbucket.io/colossus/

**astropy** https://www.astropy.org/

**corner.py** https://github.com/dfm/corner.py

**matplotlib** https://matplotlib.org/

**numba** https://github.com/numba/numba

**numpy** https://numpy.org/

**scipy** https://www.scipy.org/

**scikit-image**: https://github.com/scikit-image/scikit-image

**scikit-learn**: https://github.com/scikit-learn/scikit-learn

And the following optional dependencies:

**pynufft**: https://github.com/jyhmiinlin/pynufft