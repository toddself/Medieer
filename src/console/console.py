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

from pubsub import pub

from core.models import Settings, Media
from core.tools import get_files

REVERT_MSG = """\
Are you sure you want to revert?
Your files will be moved back to the original locations and renamed. 
Nothing else will be done. [y/N]
"""

def console_display(msg):
    print msg

# not so subtly stolen from phatch and stani's talk at pycon 2011
def ask(question, answers):
    answer = None
    while not(answer in awswers):
        answer = raw_input(question).strip().lower()
    return answer

def ask_yes_no(question, default='yes'):
    return ask(question, ['yes','no'])  == default


class Console():
    """"""
    
    def __init__(self, options, log):
        pub.subscribe(self.conflict_resolver, 'RESOLVE_CONFLICT')
        self.log = log
        self.options = options
        if self.options.show_defaults:
            self.show_defaults()
        elif self.options.change_setting:
            self.change_setting(self.options.change_setting)
        elif self.options.rewind:
            self.rewind()
        elif self.options.regenerate_xml:
            self.regenerate_xml(self.ensure_list(self.options.infile))
        elif self.options.infile:
            self.process_files(self.ensure_list(self.options.infile))
        else:
            self.process_files('*')

        def show_defaults(self):
            settings = list(Settings.select())
            vw = max([len(setting.value) for setting in settings])
            kw = max([len(setting.key) for setting in settings])
            sc_head = 'Setting'.ljust(kw)
            vc_head = 'Value'.ljust(vw)
            output = '\n%s\t%s' % (sc_head, vc_head)
            output +=  '\n%s\n' % ('-' * len(output))
            for s in settings:
                output += '%s\t%s\n' % (s.key.ljust(kw), s.value.ljust(vw))
            print output
            sys.exit(0)        
        
        def change_setting(self, settings):
            for s in settings:
                try:
                    key, value = s.split('=')
                except ValueError:
                    msg = '%s is not in the form of key=value.' % s[0]
                    self.log.critical(msg)
                    sys.exit(msg)
                else:
                    try:
                        so = list(Settings.select(Settings.q.key==key))[0]
                    except IndexError:
                        msg = "%s is not a valid key" % key
                        self.log.critical(msg)
                        sys.exit(msg)
                    else:
                        so.value = value
                        msg = 'Changed key %s to  %s' % (so.key, so.value)
                        self.log.info(msg)
                        print msg
            sys.exit(0)
        
        def rewind(self):
            if ask_yes_no(REVERT_MSG):
                self.log.info('Rewinding!')
                pub.sendMessage('REWIND')
                sys.exit(0)
            else:
                print "Nothing changed."
                sys.exit()
        
        def regenerate_xml(self, f_list):
            for fn in f_list:
                pub.sendMessage('GENERATE_XML', filename=fn)
            pub.sendMessage('OUTPUT_XML')
            sys.exit()
        
        def process_files(self, f_list):
            for fn in f_list:
                pub.sendMessage('PROCESS_FILE', filename=fn)
            sys.exit()
        
        def ensure_list(self, arr):
            if not isinstance(arr, list):
                return [arr]
            else:
                return arr
        
        def conflict_resolver(self, conflict_list):
            pass
                
def main(options, log):
    # We want all the end-user messages to be pulled into the console display
    # function.  This will allow the end user to see them
    pub.subscribe(console_display, 'STD_OUT')
    ft = FileTools()
    con = Console(options)
                
if __name__ == '__main__':
    main()