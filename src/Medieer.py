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
#     along with Medieer.  If not, see <http://www.gnu.org/licenses/>.

# TODO VERSION 1.0: IMPLEMENT GUI
# TODO VERSION 1.0: IMPLEMENT VERSION MIGRATION
# TODO VERSION 1++: IMPLEMENT IMDB LOOKUP
# TODO VERSION 1++: IMPLEMENT TVDB LOOKUP
# TODO VERSION 1++: ALLOW FOR MULTIPLE CATEGORIZATION. SYMLINKS?
# TODO VERSION 1.0 REFACTOR Medieer OBJECT FOR BETTER CODE ORGANIZATION


__all__ = ['main', ]

import sys
import argparse
import logging
from os.path import join, isdir

from sqlobject import connectionForURI, sqlhub
from appdirs import AppDirs

APPNAME = 'Medieer'
APPAUTHOR = 'Selfassembled'
__version__ = '0.65'

class ConsoleParse(argparse.Action):
    """Sets no_gui to be true when any other console commands are used"""
    
    def __call__(self, parser, namespace, values, option_string=None):
        if values:
            setattr(namespace, self.dest, values)
        else:
            setattr(namespace, self.dest, True)
            
        if not hasattr(namespace, 'no_gui'):
            setattr(namespace, 'no_gui', True)

def parse_args(args):
    parser = argparse.ArgumentParser(description='Manage media metadata.')
    console_group = parser.add_argument_group('console', 'Console switches')
    console_group.add_argument('-s', '--show-defaults', action=ConsoleParse, 
                        nargs=0,
                        dest='show_defaults', 
                        default=False, 
                        help='Show all settings and exit. -n implied.')                        
    console_group.add_argument('-n', '--no-gui', action=ConsoleParse,
                        nargs=0,
                        dest='no_gui', 
                        default=False, 
                        help="Don't launch GUI.")
    console_group.add_argument('-t', '--trust', action=ConsoleParse,
                        nargs=0,
                        dest='trust', 
                        default=False, 
                        help="If title returns more than one result,"+ 
                        "choose first from list.")      
    console_group.add_argument('-r', '--rewind', action=ConsoleParse, 
                        nargs=0,
                        dest='rewind',
                        default=False, 
                        help="Rename files to source names. -n implied")
    console_group.add_argument('-c', '--change-setting', action=ConsoleParse,
                        nargs=1,
                        dest='change_setting', 
                        default='', 
                        help='Change a setting.'+
                        'Example: --change-setting source_path=/etc/videos'+
                        '-n implied.')
    console_group.add_argument('-x', '--regenerate-xml', action='store_true',
                        dest='regenerate_xml', 
                        default=False, 
                        help='Generate XML from database.'+
                        'Do not process new files. -n implied')
    parser.add_argument('-d', '--debug', nargs=1, 
                        dest='debug',
                        default='INFO'
                        help='Set logging level [DEBUG|INFO]. Default: INFO')
    return parser.parse_args(args)

def init_log(level, appdirs):
    levels = {'debug': logging.DEBUG, 'info': logging.INFO}
    log_filename = join(appdirs.user_log_dir, "%s.log" % appdirs.appname)               
    msg_fmt = '[%(asctime)s] %(name)-12s %(levelname)-8s %(message)s'
    date_fmt = '%m/%d %H:%M'
    level = levels.get(level, logging.NOTSET)
    
    try:
        logging.basicConfig(level = level,
                            format = msg_fmt,
                            datefmt = date_fmt,
                            filename=LOG_FILENAME,
                            filemode='w')
    except IOError:
        logging.basicConfig(level = level,
                            format = msg_fmt,
                            datefmt = date_fmt,
                            stream=sys.stderr)

def open_db(appdirs):
    db_driver = 'sqlite'
    db_fn = join(appdirs.user_data_dir, appdirs.appname+'.sqlite')
    connection_string = "%s://%s" % (db_driver, db_fn)
    connection = connectionForURI(connection_string)
    sqlhub.processConnection = connection                            

def launch_console(options):
    from console import console
    console.main(options, log=logging.getLogger('console'))

def launch_gui(options):
    from core.tools import launch_pw
    launch_pw()
    from pyWx import gui
    gui.main(options, log=logging.getLogger('gui')

def main(argv):
    options = parse_args(argv)
    appdirs = AppDirs(APPNAME, APPAUTHOR)
    init_log(options.debug[0].lower(), appdirs)

    # We need to initialize the data directories if this is a first-run
    if not isdir(appdirs.user_data_dir):
        from core import first_run
        first_run.main(log=logging.getLogger('first_run'), appdirs)

    # Now that the database exists, we can safely open the connection
    open_db(appdirs)
    if options.no_gui:
        launch_console(options)
    else:
        launch_gui(options)    
    
if __name__ == '__main__':
    main(sys.argv[:1])