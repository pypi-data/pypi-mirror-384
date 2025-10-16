"""
Module to edit, load, and save the `NXtomo application <https://tomotools.gitlab-pages.esrf.fr/nxtomo/>`_.
"""

from nxtomo.version import version as __version__  # noqa F401

from .application.nxtomo import NXtomo  # noqa F401
