#!/usr/bin/env python
# This file is part of Medieer.
# 
#     Medieer is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     Medieer is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages
    
appname = 'Medieer'
appauthor = 'Todd Kennedy'
authoremail = '<todd.kennedy@gmail.com>'
__version__ = '0.65'

setup(name=appname,
      version=__version__,
      author=appauthor,
      author_email=authoremail,
      url='http://medieer.selfassembled.org',
      license='GPLv3',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests', '.git']),
      install_requires=['sqlobject', 'lxml', 'beautifulsoup', 'appdirs', 'argparse'],
      scripts=['Medieer.py'],
      )