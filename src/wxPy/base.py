#!/usr/bin/env python

# Base layout engine
# Copyright (C) 2010 Todd Kennedy <todd.kennedy@gmail.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import wx        

class BaseWindow(object):
    """
    BaseWindow provides a rudementary layout engine for building wxpython guis.
    
    Included methods:
    buildToolbar(): expects a method to be defined in the child class named
        toolbarData which returns a tuple of tuples defining the toolbar
        
    buildMenuBar(): expects a method to be definied in the child class named
        menuData which returns a tuple of dictionaries defining the menu 
        structure in the application
    
    buildLayout(): expects a method to be defined in the child class named
        layoutData which returns a tuple of dictionaries defining the 
        application structure and widgets
        
    More details about the data structures required are found in the 
    docstrings for each method
    
    """

    TC_STYLE = wx.ALL|wx.ALIGN_CENTER_VERTICAL
    ST_STYLE = wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL
    ui_font = None
    _not_editable_color = wx.Colour(220, 220, 220)
    
    def __init__(self):
        pass
        
    def buildToolbar(self):
        """
        buildToolbar will generate a toolbar on the window with Text labels.  It expects 
        whatever is subclassing it to have a method called toolbarData which, when called
        returns a tuple of tuples matching the following spec:
        (ID, ICON, LABEL, HELP, METHOD)
        
        providing a tuple with a empty string for id will create a separator
        """
        toolbar = wx.ToolBar(self, -1, style=wx.TB_TEXT)
        self.SetToolBar(toolbar)
        for button in self.toolbarData():
            self._createTool(toolbar, *button)
        toolbar.Realize()
        
    def _createTool(self, toolbar, tb_id, fn_icon, label, help, handler):
        """
        _createTool should never be called directly, but rather from buildToolbar. It accepts the data
        about the tool to be created, creates it, places it in the toolbar and then binds the action
        to the method.  if the id is an empty string it'll create a separator
        """
        if not tb_id:
            toolbar.AddSeparator()
            return
        else:
            icon = wx.Bitmap(fn_icon, wx.BITMAP_TYPE_ANY)
            tool = toolbar.AddLabelTool(tb_id, label, icon, icon, wx.ITEM_NORMAL, label, help)
            self.Bind(wx.EVT_MENU, handler, tool)    
    
    def buildMenuBar(self):
        """
        buildMenuBar will build your applications menus and attach all relevant submenus and bind
        the events to the appropriate methods.  when called it'll expect whatever is subclassing
        BaseWindow to have a method defined named menuData that returns a tuple of menus.  the menus
        are tuples of dictionaries, each dictionary representing a unique item on the menu
        
        name: name of the menu or menu item
        method: method to be called upon selection
        id: guid for this menu option
        help: a help string
        font:
        editable:
        
        to create a submenu, do not add the method, id and help keys, but rather an items key
        which contains a tuple of dictionaries as defined above
        """
        menu_bar = wx.MenuBar()
        for menu in self.menuData():
            label = menu['name']
            items = menu['items']
            menu_bar.Append(self._createMenu(items), label)
        self.SetMenuBar(menu_bar)
    
    def GetNewFont(self, pointSize=None, family=None, style=None, weight=None, underline=None, face=None, encoding=None):
        """
        getFont allows the user to override specific attributes of the default interface font 
        without having to mess around with generating a new wx.Font object or talking to
        wx.SystemSettings, etc.
    
        getFont returns a wx.Font object
    
        (self, pointSize, family, style, weight, underline, face, encoding) 
        """
        f = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
    
        if pointSize:
            f.SetPointSize(pointSize)
        
        if family:
            f.SetFamily(family)
    
        if style:
            f.SetStyle(style)
        
        if weight:
            f.SetWeight(weight)
        
        if underline:
            f.SetUnderline(underline)
    
        if face:
            f.SetFace(face)
        
        if encoding:
            f.SetEncoding(encoding)
        
        return f
        
    def SetDefaultFont(self, font):
        if type(font) == type(wx.Font):
            self.ui_font = font
        else:
            print 'fuck off'

    def toggleWidget(self, widget, status):
        widget.Enable(status)
        if status:
            widget.SetBackgroundColour(wx.Colour(255, 255, 255))
        else:
            widget.SetBackgroundColour(self._not_editable_color)    
    
    def _createMenu(self, items):
        """ 
        _createMenu is a helper method for buildMenuBar and should never be called directly.
        it accepts a tuple of menu dictionaries and returns a menu.  if additional tuples are 
        found, it will generate submenus and attach them to the parent menu
        """
        menu = wx.Menu()
        for item in items:
            if item.has_key('items'):
                menu_id = wx.NewId()
                label = item['name']
                sub_menu = self._createMenu(item['items'])
                menu.AppendMenu(menu_id, label, sub_menu)
            else:
                self._createMenuItem(menu, item['id'], item['name'], item['help'], item['method'])
        return menu
        
    def _createMenuItem(self, menu, menu_id, name, help, method, kind=wx.ITEM_NORMAL):
        """
        _createMenuItem is a helper method for buildMenuBar and should never be called directly.
        it accepts all the arguments for terminal (non-submenu) menu item, creates the menu item,
        attaches it to the menu and then binds the menu item to the specified method
        """
        if menu_id == 'separator':
            menu.AppendSeparator()
            return
        menu_item = menu.Append(menu_id, name, help, kind)
        self.Bind(wx.EVT_MENU, method, menu_item)
        
        
    def setDefaultSizerStyle(self, proportion=0, flag=wx.ALL, border=3):
        self.default_sizer_args = {'proportion': proportion, 'flag': flag, 'border': border}
        
        
    def buildLayout(self, parent, layoutData=None):
        """
        buildLayout generates the ui from a list of dictionaries.  
        This method expects a method to be defined called layoutData 
        which returns a list.  this does not handle creating frames 
        or dialogs, just the ui for a pre-defined window.
        
        buildLayout returns a wx.BoxSizer(wx.VERTICAL) containing all 
        the items defined by your dictionary list.
        
        The layout engine is predicated on horizontal rows of sizers (or 
        single elements), stacked on top of each other to create the 
        frame.  If a sizer needs to vertically span one or more sizers,
        the spanned sizers all need to be wrapped in a master sizer that
        will be layed parallel to the spanning sizer.
        
        This method accepts an optional parent parameter. If the frame
        specifies a top-level panel as it's top level frame element,
        this should be passed in so that tab-order can be maintained
        within the widgets
        
        """
        self.master_sizer = wx.BoxSizer(wx.VERTICAL)
        
        if not layoutData:
            layoutData = self.layoutData()

        for row in layoutData:
            if row.has_key('title'):
                    title = row.pop('title')
                    self.master_sizer.Add(self._createSectionHeader(parent, title), 0, wx.ALL|wx.EXPAND, 3)
            # we've gotta pop them off now or they won't exist after the recursive call to _createWidgets
            sizer_add_args = self._getSizerAddArgs(row)
            self.master_sizer.Add(self._createWidgets(row, parent), **sizer_add_args)
        
        return self.master_sizer

    def _createWidgets(self, row, parent):
        """
        _createWidgets is bread and butter of the layout engine.  this takes each
        "row" of elements and generates sizer that can be added to the main sizer
        for the frame.  if there are no children element, the top level element 
        can be a single widget which is passed back to be added.
        """

        if row.has_key('widgets'):
            # this row can contain either widgets or sizers
            # there will always be a 'widgets' key here though
            # thanks to the 'if' statement
            
            # we'll take off the child elements and then create our sizer
            widgets = row.pop('widgets')
            if row.has_key('title'):
                title = self._createSectionHeader(parent, row.pop('title'))

            sizer = self._createSizer(row)
            
            try:
                sizer.Add(title, 0, wx.ALL|wx.EXPAND, 3)
            except:
                pass                
            
            # now lets see if there are more sizers or just elements
            # if there are more sizers, we're gonna call this function again
            for widget in widgets:
                # this will be true if we're working with a sizer
                if widget.has_key('widgets'):                    
                    sizer.Add(self._createWidgets(widget, parent))
                else:
                    sizer = self._addWidgetToSizer(widget, sizer, parent)
        else:
            print 'how the fuck did you get called?'
            
        return sizer


    def _addWidgetToSizer(self, widget, sizer, parent):
        """
        _addWidgetToSizer pops off the widget's arguement to the
        Add() method and adds them to a dictionary.  We still pass
        this to the _getSizerAddArgs() method so we can ensure
        there are reasonable defaults present for all items.
        
        then _addWidgetToSizer tries to generate the widget using
        _createWidget.  If a widget is returned, it then adds that
        element to the sizer passed in and returns the sizer
        to the calling method
        """
        args = {}
        if widget.has_key('flag'):
            args['flag'] = widget.pop('flag')
        
        if widget.has_key('proportion'):
            args['proportion'] = widget.pop('proportion')
        
        if widget.has_key('border'):
            args['border'] = widget.pop('border')
            
        element = self._createWidget(widget, parent)

        if element:
            sizer.Add(element, **self._getSizerAddArgs(args))
        
        return sizer

    def _getSizerAddArgs(self, sizer_element):
        """
        _getSizerAddArgs returns the proportion, style and border
        a given element should set when being added to a sizer.
        
        if no values are set or present, it will use the default values
        specified in the args dictionary
        """
        args = {}
    
        try:
            self.default_sizer_args
        except AttributeError:
            self.setDefaultSizerStyle()
            
        for key in self.default_sizer_args.keys():
            if sizer_element.has_key(key):
                args[key] = sizer_element[key]
            else:
                args[key] = self.default_sizer_args[key]

        return args
        
    def _createSizer(self, sizer):
        """
        _createSizer takes the sizer function passed from the dictionary, 
        sets it a temp variable and then removes the sizer function from 
        the dictionary, leaving only the arguments to the sizer functions 
        as elements. we then call the sizer function, passing the values
        of the dictionary as *args to the sizer method
        """
        method = sizer.pop('widget')
        
        if sizer.has_key('flag'):
            sizer.pop('flag')
        
        if sizer.has_key('proportion'):
            sizer.pop('proportion')
        
        if sizer.has_key('border'):
            sizer.pop('border')
            
        if sizer.has_key('title'):
            sizer.pop('title')
        
        return method(*sizer.values())
        
    def _createWidget(self, widget, parent):
        """
        the keys for each widget should be the arguments for the 
        given widget, in addition to the following:
        
        widget: this is the widget we'll be making.
        sizer_style: information to be passed onto the sizer for styling
        proportion: how greedy it should be when placed into the sizer
        border: how big the border should be (if the border elements are 
            specified in the sizer_sizer key)
        event: a dictionary containing a method that should be called 
            upon event_type.
        display: method or parameter to check. if this key is present,
            item is considered to be optional and will only be displayed 
            if the condition is true
        
        these keys are popped off (and used if necessary) and then the
        widget is called with the remaining keys as the **kw argument
        to the method
        """
        if widget.has_key('display'):
            display = widget.pop('display')
            if not display:
                return None
            
        wxMethod = widget.pop('widget')

        try:
            event = widget.pop('event')
        except:
            event = False
                    
        try:
            var = widget.pop('var')
        except:
            var = False

        try:
            font = widget.pop('font')
        except:
            font = False
            
        try:
            editable = widget.pop('editable')
        except:
            editable = True
            
        if not widget.has_key('id') and var:
            widget['id'] = wx.NewId()
            
        gui_element = wxMethod(parent, **widget)
    
        if self.ui_font and not font:
            gui_element.SetFont(self.ui_font)
        elif font:
            gui_element.SetFont(font)
            
        if not editable:
            self.toggleWidget(gui_element, False)
    
        if var:
            setattr(self, var, gui_element)
            setattr(self, '%s_id' % var, gui_element.GetId())
    
        if event:
            if type(event) == type(()):
                for evt in event:
                    self._bindEvent(evt, gui_element)
            else:
                self._bindEvent(event, gui_element)

        return gui_element

    def _bindEvent(self, event, element):
        self.Bind(event['event_type'], event['method'], element)
        
    def _createSectionHeader(self, parent, title, font=None, scale=-1):
        """
        _createSectionHeader returns a horizontal wx.BoxSizer
        which contains a header and a horizontal rule.  if no font
        is specified, the default is that it uses the system font,
        one point size lower.  the font can either be passed
        as a formal parameter or it can be found in the ui_font
        attribute of the class, if present
        """
        
        if font == None:
            if self.ui_font:
                f = self.ui_font
            else:
                f = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
                f.SetPointSize(f.GetPointSize() + scale)
        else:
            f = font
                
        section_head = wx.StaticText(parent, -1, title)
        section_head.SetFont(f)
        section_line = wx.StaticLine(parent, -1, 
            style=wx.LI_HORIZONTAL)
        
        tb = wx.BoxSizer(wx.HORIZONTAL)
        tb.Add(section_head, 0, wx.ALL|wx.ALIGN_BOTTOM, 3)
        tb.Add(section_line, proportion=1, flag=wx.ALIGN_BOTTOM|wx.BOTTOM, border=5)
        
        return tb