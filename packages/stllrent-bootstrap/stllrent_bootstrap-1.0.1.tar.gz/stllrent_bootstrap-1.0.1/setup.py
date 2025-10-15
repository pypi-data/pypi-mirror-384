#!/usr/bin/env python3

# [INSTALL BUILD TOOLS]:
# pip install build
# pip install twine

# [PUBLISH]:
# python -m build
# python -m twine upload dist/*

"""
Parts of this file were taken from the pyzmq project
(https://github.com/zeromq/pyzmq) which have been permitted for use under the
BSD license. Parts are from lxml (https://github.com/lxml/lxml)
"""
# setup.py
from setuptools import setup

# O setup agora é mínimo, pois o pyproject.toml gerencia a configuração.
setup()