# coding=utf-8
"""
pyCity_Calc: Python package addon for pyCity

The MIT License

Copyright (C) 2015-2019 Jan Schiefelbein

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

from setuptools import setup


setup(name='pycity_calc',
      version='0.1.0',
      description='Python package to model energy systems on '
                  'city district scale',
      url='https://github.com/RWTH-EBC/pyCity_calc',
      author='Jan Schiefelbein',
      author_email='jschiefelbein@eonerc.rwth-aachen.de',
      license='MIT License',
      packages=['pycity_calc'],
      setup_requires=['numpy', 'matplotlib', 'networkx', 'shapely',
                      'richardsonpy', 'uesgraphs', 'pycity_base',
                      'xlrd', 'pytest', 'pypower', 'utm', 'pyDOE'],
      install_requires=['numpy', 'matplotlib', 'networkx', 'shapely',
                      'richardsonpy', 'uesgraphs','pycity_base',
                      'xlrd', 'pytest', 'pypower', 'utm', 'pyDOE'])
