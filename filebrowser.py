# -*- coding: utf-8 -*-
"""
tkfilebrowser - Alternative to filedialog for Tkinter
Copyright 2017-2018 Juliette Monsel <j_4321@protonmail.com>

tkfilebrowser is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

tkfilebrowser is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


Main class
"""

import os
import subprocess
import datetime
from tkinter import messagebox
from tkinter import simpledialog

import psutil
from re import search
from subprocess import check_output
from os import walk, mkdir, stat, access, W_OK, listdir
from os import name as OSNAME
from os.path import sep as SEP
from os.path import exists, join, getmtime, realpath, split, expanduser, \
    abspath, isabs, splitext, dirname, getsize, isdir, isfile, islink
try:
    from os import scandir
    SCANDIR = True
except ImportError:
    SCANDIR = False
import traceback
import constants as cst
from constants import unquote, tk, ttk, key_sort_files, \
    get_modification_date, display_modification_date, display_size
from autoscrollbar import AutoScrollbar
from path_button import PathButton
import path_button
from tooltip import TooltipTreeWrapper
from recent_files import RecentFiles
from stagelist import *
from branch_menu import *
from tkinter import filedialog
import tkinter as tk
if OSNAME == 'nt':
    from win32com.shell import shell, shellcon

_ = cst._

class Stats:
    """Fake stats class to create dummy stats for broken links."""
    def __init__(self, **kwargs):
        self._prop = kwargs

    def __getattr__(self, attr):
        if attr not in self._prop:
            raise AttributeError("Stats has no attribute %s." % attr)
        else:
            return self._prop[attr]

#stagelist에 대한 인스턴스 생성
#sroot = tk.Tk()  # 부모 윈도우 생성
#stage_list = StageList(sroot)  # StageList의 인스턴스 생성
#sroot.mainloop()  # Tkinter 이벤트 루프 시작

class FileBrowser(tk.Toplevel):
    """Filebrowser dialog class."""
    #스켈레톤
    def check_git_managed():
        pass
    #에러메시지창
    def error_message_window():
        error_window=tk.Tk()
        error_window.withdraw()
        messagebox.showerror("!ERROR!", "부적절한 폴더/파일입니다!")
        error_window.destroy()
        
    def __init__(self, parent, initialdir="", initialfile="", mode="openfile",
                 multiple_selection=False, defaultext="", title="Filebrowser",
                 filetypes=[], okbuttontext=None, cancelbuttontext=_("Cancel"),commitbuttontext=("Commit은 폴더에 대고 마우스휠클릭\nBranch와 Clone버튼은 폴더를 열고 누르세요"),
                 foldercreation=True, **kw):
        """
        Create a filebrowser dialog.

        Arguments:

        parent : Tk or Toplevel instance
            parent window

        title : str
            the title of the filebrowser window

        initialdir : str
            directory whose content is initially displayed

        initialfile : str
            initially selected item (just the name, not the full path)

        mode : str
            kind of dialog: "openfile", "opendir" or "save"

        multiple_selection : bool
            whether to allow multiple items selection (open modes only)

        defaultext : str (e.g. '.png')
            extension added to filename if none is given (default is none)

        filetypes : list :obj:`[("name", "*.ext1|*.ext2|.."), ...]`
          only the files of given filetype will be displayed,
          e.g. to allow the user to switch between displaying only PNG or JPG
          pictures or dispalying all files:
          :obj:`filtypes=[("Pictures", "\*.png|\*.PNG|\*.jpg|\*.JPG'), ("All files", "\*")]`

        okbuttontext : str
            text displayed on the validate button, default is "Open".

        cancelbuttontext : str
            text displayed on the button that cancels the selection, default is "Cancel".

        foldercreation : bool
            enable the user to create new folders if True (default)
        """
        # compatibility with tkinter.filedialog arguments: the parent window is called 'master'
        if 'master' in kw and parent is None:
            parent = kw.pop('master')
        if 'defaultextension' in kw and not defaultext:
            defaultext = kw.pop('defaultextension')
        tk.Toplevel.__init__(self, parent, **kw)

        # python version compatibility
        if SCANDIR:
            self.display_folder = self._display_folder_scandir
        else:
            self.display_folder = self._display_folder_walk

        # keep track of folders to be able to move backward/foreward in history
        if initialdir:
            self.history = [initialdir]
        else:
            self.history = [expanduser("~")]
        self._hist_index = -1

        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.quit)
        self.title(title)

        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        self.mode = mode
        self.result = ""
        self.foldercreation = foldercreation

        # hidden files/folders visibility
        self.hide = False
        # hidden items
        self.hidden = ()

        # ---  style
        
        style = ttk.Style(self)
        bg = style.lookup("TFrame", "background")
        style.layout("right.tkfilebrowser.Treeview.Item",
                     [('Treeitem.padding',
                       {'children':
                           [('Treeitem.image', {'side': 'left', 'sticky': ''}),
                            ('Treeitem.focus',
                             {'children':
                                 [('Treeitem.text',
                                   {'side': 'left', 'sticky': ''})],
                              'side': 'left',
                              'sticky': ''})],
                        'sticky': 'nswe'})])
        style.layout("left.tkfilebrowser.Treeview.Item",
                     [('Treeitem.padding',
                       {'children':
                           [('Treeitem.image', {'side': 'left', 'sticky': ''}),
                            ('Treeitem.focus',
                             {'children':
                                 [('Treeitem.text', {'side': 'left', 'sticky': ''})],
                              'side': 'left',
                              'sticky': ''})],
                        'sticky': 'nswe'})])
        style.configure("right.tkfilebrowser.Treeview", font="TkDefaultFont")
        style.configure("right.tkfilebrowser.Treeview.Item", padding=2)
        style.configure("right.tkfilebrowser.Treeview.Heading",
                        font="TkDefaultFont")
        style.configure("left.tkfilebrowser.Treeview.Heading",
                        font="TkDefaultFont")
        style.configure("left.tkfilebrowser.Treeview.Item", padding=2)
        style.configure("listbox.tkfilebrowser.TFrame", background="white", relief="sunken")
        field_bg = style.lookup("TEntry", "fieldbackground", default='white')
        tree_field_bg = style.lookup("ttk.Treeview", "fieldbackground",
                                     default='white')
        fg = style.lookup('TLabel', 'foreground', default='black')
        active_bg = style.lookup('TButton', 'background', ('active',))
        sel_bg = style.lookup('Treeview', 'background', ('selected',))
        sel_fg = style.lookup('Treeview', 'foreground', ('selected',))
        self.option_add('*TCombobox*Listbox.selectBackground', sel_bg)
        self.option_add('*TCombobox*Listbox.selectForeground', sel_fg)
        style.map('types.tkfilebrowser.TCombobox', foreground=[], fieldbackground=[])
        style.configure('types.tkfilebrowser.TCombobox', lightcolor=bg,
                        fieldbackground=bg)
        style.configure('types.tkfilebrowser.TCombobox.Item', background='red')
        style.configure("left.tkfilebrowser.Treeview", background=active_bg,
                        font="TkDefaultFont",
                        fieldbackground=active_bg)
        self.configure(background=bg)
        # path button style
        style.configure("path.tkfilebrowser.TButton", padding=2)
        selected_bg = style.lookup("TButton", "background", ("pressed",))
        map_bg = style.map("TButton", "background")
        map_bg.append(("selected", selected_bg))
        style.map("path.tkfilebrowser.TButton",
                  background=map_bg,
                  font=[("selected", "TkDefaultFont 9 bold")])
        # tooltip style
        style.configure('tooltip.tkfilebrowser.TLabel', background='black',
                        foreground='white')

        # ---  images
        self.im_file = cst.PhotoImage(file=cst.IM_FILE, master=self)
        self.im_folder = cst.PhotoImage(file=cst.IM_FOLDER, master=self)
        self.im_desktop = cst.PhotoImage(file=cst.IM_DESKTOP, master=self)
        self.im_file_link = cst.PhotoImage(file=cst.IM_FILE_LINK, master=self)
        self.im_link_broken = cst.PhotoImage(file=cst.IM_LINK_BROKEN, master=self)
        self.im_folder_link = cst.PhotoImage(file=cst.IM_FOLDER_LINK, master=self)
        self.im_new = cst.PhotoImage(file=cst.IM_NEW, master=self)
        self.im_drive = cst.PhotoImage(file=cst.IM_DRIVE, master=self)
        self.im_home = cst.PhotoImage(file=cst.IM_HOME, master=self)
        self.im_recent = cst.PhotoImage(file=cst.IM_RECENT, master=self)
        self.im_recent_24 = cst.PhotoImage(file=cst.IM_RECENT_24, master=self)

        # ---  filetypes
        self.filetype = tk.StringVar(self)
        self.filetypes = {}
        if filetypes:
            for name, exts in filetypes:
                if name not in self.filetypes:
                    self.filetypes[name] = []
                self.filetypes[name] = r'%s$' % exts.strip().replace('.', '\.').replace('*', '.*')
            values = list(self.filetypes.keys())
            w = max([len(f) for f in values] + [5])
            b_filetype = ttk.Combobox(self, textvariable=self.filetype,
                                      state='readonly',
                                      style='types.tkfilebrowser.TCombobox',
                                      values=values,
                                      width=w)
            b_filetype.grid(row=3, sticky="e", padx=10, pady=(4, 0))
            self.filetype.set(filetypes[0][0])
            try:
                self.filetype.trace_add('write', lambda *args: self._change_filetype())
            except AttributeError:
                self.filetype.trace('w', lambda *args: self._change_filetype())
        else:
            self.filetypes[""] = r".*$"

        # ---  recent files
        self._recent_files = RecentFiles(cst.RECENT_FILES, 30)

        # ---  path completion
        self.complete = self.register(self._completion)
        self.listbox_var = tk.StringVar(self)
        self.listbox_frame = ttk.Frame(self, style="listbox.tkfilebrowser.TFrame", borderwidth=1)
        self.listbox = tk.Listbox(self.listbox_frame,
                                  listvariable=self.listbox_var,
                                  highlightthickness=0,
                                  borderwidth=0,
                                  background=field_bg,
                                  foreground=fg,
                                  selectforeground=sel_fg,
                                  selectbackground=sel_bg)
        self.listbox.pack(expand=True, fill="x")

        

        # ---  path bar
        self.path_var = tk.StringVar(self)
        frame_bar = ttk.Frame(self)
        frame_bar.columnconfigure(0, weight=1)
        frame_bar.grid(row=1, sticky="ew", pady=10, padx=10)
        frame_recent = ttk.Frame(frame_bar)
        frame_recent.grid(row=0, column=0, sticky="w")
        ttk.Label(frame_recent, image=self.im_recent_24).pack(side="left")
        ttk.Label(frame_recent, text=_("Recently used"),
                  font="TkDefaultFont 9 bold").pack(side="left", padx=4)
        self.path_bar = ttk.Frame(frame_bar)
        self.path_bar.grid(row=0, column=0, sticky="ew")
        self.path_bar_buttons = []
        #self.b_new_folder = ttk.Button(frame_bar, image=self.im_new,command=self.create_folder)
        self.b_commit_history = ttk.Button(frame_bar, text="Commit History", command=self.open_commit_history)
        #self.b_commit_history.grid(row=0, column=1, sticky="e")
        if self.foldercreation:
            #self.b_new_folder.grid(row=0, column=1, sticky="e")
            self.b_commit_history.grid(row=0, column=1, sticky="e")
        if mode == "save":
            ttk.Label(self.path_bar, text=_("Folder: ")).grid(row=0, column=0)
            self.defaultext = defaultext

            frame_name = ttk.Frame(self)
            frame_name.grid(row=0, pady=(10, 0), padx=10, sticky="ew")
            ttk.Label(frame_name, text=_("Name: ")).pack(side="left")
            self.entry = ttk.Entry(frame_name, validate="key",
                                   validatecommand=(self.complete, "%d", "%S",
                                                    "%i", "%s"))
            self.entry.pack(side="left", fill="x", expand=True)

            if initialfile:
                self.entry.insert(0, initialfile)
        else:
            self.multiple_selection = multiple_selection
            self.entry = ttk.Entry(frame_bar, validate="key",
                                   validatecommand=(self.complete, "%d", "%S",
                                                    "%i", "%s"))
            self.entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=0,
                            pady=(10, 0))
            self.entry.grid_remove()

        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.grid(row=2, sticky="eswn", padx=10)

        # ---  left pane
        left_pane = ttk.Frame(paned)
        left_pane.columnconfigure(0, weight=1)
        left_pane.rowconfigure(0, weight=1)

        paned.add(left_pane, weight=0)
        self.left_tree = ttk.Treeview(left_pane, selectmode="browse",
                                      style="left.tkfilebrowser.Treeview")
        wrapper = TooltipTreeWrapper(self.left_tree)
        self.left_tree.column("#0", width=150)
        self.left_tree.heading("#0", text=_("Shortcuts"), anchor="w")
        self.left_tree.grid(row=0, column=0, sticky="sewn")

        scroll_left = AutoScrollbar(left_pane, command=self.left_tree.yview)
        scroll_left.grid(row=0, column=1, sticky="ns")
        self.left_tree.configure(yscrollcommand=scroll_left.set)

        # list devices and bookmarked locations
        # -------- recent
        self.left_tree.insert("", "end", iid="recent", text=_("Recent"),
                              image=self.im_recent)
        wrapper.add_tooltip("recent", _("Recently used"))

        # -------- devices
        devices = psutil.disk_partitions(all=True if OSNAME == "nt" else False)

        for d in devices:
            m = d.mountpoint
            if m == "/":
                txt = "/"
            else:
                if OSNAME == 'nt':
                    txt = m
                else:
                    txt = split(m)[-1]
            self.left_tree.insert("", "end", iid=m, text=txt,
                                  image=self.im_drive)
            wrapper.add_tooltip(m, m)

        # -------- home
        home = expanduser("~")
        self.left_tree.insert("", "end", iid=home, image=self.im_home,
                              text=split(home)[-1])
        wrapper.add_tooltip(home, home)

        # -------- desktop
        if OSNAME == 'nt':
            desktop = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, None, 0)
        else:
            try:
                desktop = check_output(['xdg-user-dir', 'DESKTOP']).decode().strip()
            except Exception:
                # FileNotFoundError in python3 if xdg-users-dir is not installed,
                # but OSError in python2
                desktop = join(home, 'Desktop')
            if exists(desktop):
                self.left_tree.insert("", "end", iid=desktop, image=self.im_desktop,
                                      text=split(desktop)[-1])
                wrapper.add_tooltip(desktop, desktop)

        # -------- bookmarks
        if OSNAME == 'nt':
            bm = []
            for folder in [shellcon.CSIDL_PERSONAL, shellcon.CSIDL_MYPICTURES,
                           shellcon.CSIDL_MYMUSIC, shellcon.CSIDL_MYVIDEO]:
                try:
                    bm.append([shell.SHGetFolderPath(0, folder, None, 0)])
                except Exception:
                    pass
        else:
            path_bm = join(home, ".config", "gtk-3.0", "bookmarks")
            path_bm2 = join(home, ".gtk-bookmarks")  # old location
            if exists(path_bm):
                with open(path_bm) as f:
                    bms = f.read().splitlines()
            elif exists(path_bm2):
                with open(path_bm) as f:
                    bms = f.read().splitlines()
            else:
                bms = []
            bms = [ch.split() for ch in bms]
            bm = []
            for ch in bms:
                ch[0] = unquote(ch[0]).replace("file://", "")
                bm.append(ch)
        for l in bm:
            if len(l) == 1:
                txt = split(l[0])[-1]
            else:
                txt = l[1]
            self.left_tree.insert("", "end", iid=l[0],
                                  text=txt,
                                  image=self.im_folder)
            wrapper.add_tooltip(l[0], l[0])

        # ---  right pane
        right_pane = ttk.Frame(paned)
        right_pane.columnconfigure(0, weight=1)
        right_pane.rowconfigure(0, weight=1)
        paned.add(right_pane, weight=1)

        if mode != "save" and multiple_selection:
            selectmode = "extended"
        else:
            selectmode = "browse"

        self.right_tree = ttk.Treeview(right_pane, selectmode=selectmode,
                                       style="right.tkfilebrowser.Treeview",
                                       columns=("location", "size", "date"),
                                       displaycolumns=("size", "date"))
        # headings
        self.right_tree.heading("#0", text=_("Name"), anchor="w",
                                command=lambda: self._sort_files_by_name(True))
        self.right_tree.heading("location", text=_("Location"), anchor="w",
                                command=lambda: self._sort_by_location(False))
        self.right_tree.heading("size", text=_("Size"), anchor="w",
                                command=lambda: self._sort_by_size(False))
        self.right_tree.heading("date", text=_("Modified"), anchor="w",
                                command=lambda: self._sort_by_date(False))
        # columns
        self.right_tree.column("#0", width=250)
        self.right_tree.column("location", width=100)
        self.right_tree.column("size", stretch=False, width=85)
        self.right_tree.column("date", width=120)
        # tags
        self.right_tree.tag_configure("0", background=tree_field_bg)
        self.right_tree.tag_configure("1", background=active_bg)
        self.right_tree.tag_configure("folder", image=self.im_folder)
        self.right_tree.tag_configure("file", image=self.im_file)
        self.right_tree.tag_configure("folder_link", image=self.im_folder_link)
        self.right_tree.tag_configure("file_link", image=self.im_file_link)
        self.right_tree.tag_configure("link_broken", image=self.im_link_broken)
        if mode == "opendir":
            self.right_tree.tag_configure("file", foreground="gray")
            self.right_tree.tag_configure("file_link", foreground="gray")

        self.right_tree.grid(row=0, column=0, sticky="eswn")
        # scrollbar
        self._scroll_h = AutoScrollbar(right_pane, orient='horizontal',
                                       command=self.right_tree.xview)
        self._scroll_h.grid(row=1, column=0, sticky='ew')
        scroll_right = AutoScrollbar(right_pane, command=self.right_tree.yview)
        scroll_right.grid(row=0, column=1, sticky="ns")
        self.right_tree.configure(yscrollcommand=scroll_right.set,
                                  xscrollcommand=self._scroll_h.set)

        # ---  buttons
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=4, sticky="ew", pady=10, padx=10)
        if okbuttontext is None:
            if mode == "save":
                okbuttontext = _("Save")
            else:
                okbuttontext = _("Open")
        ttk.Button(frame_buttons, text=okbuttontext,
                   command=self.validate).pack(side="right")
        ttk.Button(frame_buttons, text=cancelbuttontext,
                   command=self.quit).pack(side="right", padx=4)
        ttk.Label(frame_buttons,text=commitbuttontext).pack(side="left",padx=2)
        ttk.Button(frame_buttons, text="Branch",
                   command=self.branch_button_click).pack(side="right", padx=5)
        ttk.Button(frame_buttons, text="Clone",
                   command=self.clone_button_click).pack(side="right", padx=9)
        # --- 메뉴 생성
        self.foldermenu = tk.Menu(self, tearoff=0)
        self.filemenu_untracked = tk.Menu(self, tearoff=0)
        self.filemenu_commited = tk.Menu(self, tearoff=0)
        self.filemenu_modified = tk.Menu(self, tearoff=0)
        self.filemenu_staged = tk.Menu(self, tearoff=0)
      
      

        # ---  key browsing entry
        self.key_browse_var = tk.StringVar(self)
        self.key_browse_entry = ttk.Entry(self, textvariable=self.key_browse_var,
                                          width=10)
        cst.add_trace(self.key_browse_var, "write", self._key_browse)
        # list of folders/files beginning by the letters inserted in self.key_browse_entry
        self.paths_beginning_by = []
        self.paths_beginning_by_index = 0  # current index in the list

        # ---  initialization
        if not initialdir:
            initialdir = expanduser("~")

        self.display_folder(initialdir)
        initialpath = join(initialdir, initialfile)
        if initialpath in self.right_tree.get_children(""):
            self.right_tree.see(initialpath)
            self.right_tree.selection_add(initialpath)

        # ---  bindings
        # filetype combobox
        self.bind_class('TCombobox', '<<ComboboxSelected>>',
                        lambda e: e.widget.selection_clear(),
                        add=True)
        # left tree
        self.left_tree.bind("<<TreeviewSelect>>", self._shortcut_select)
        # right tree
        self.right_tree.bind("<Double-1>", self._select)
        self.right_tree.bind("<Return>", self._select)
        self.right_tree.bind("<Right>", self._go_left)
        self.right_tree.bind("<Button-3>", self._select_rightmouse) #우클릭 bind
        #yuna 마우스휠클릭 bind, 여기에서 commit을 위한 마우스 이벤트 바꿀수 있음
        self.right_tree.bind("<Button-2>",self._select_special_mouse)

        if multiple_selection:
            self.right_tree.bind("<Control-a>", self._right_tree_select_all)

        if mode == "opendir":
            self.right_tree.bind("<<TreeviewSelect>>",
                                 self._file_selection_opendir)
        elif mode == "openfile":
            self.right_tree.bind("<<TreeviewSelect>>",
                                 self._file_selection_openfile)
        else:
            self.right_tree.bind("<<TreeviewSelect>>",
                                 self._file_selection_save)
        self.right_tree.bind("<KeyPress>", self._key_browse_show)
        # listbox
        self.listbox.bind("<FocusOut>",
                          lambda e: self.listbox_frame.place_forget())
        

        # path entry
        self.entry.bind("<Escape>",
                        lambda e: self.listbox_frame.place_forget())
        self.entry.bind("<Down>", self._down)
        self.entry.bind("<Return>", self.validate)
        self.entry.bind("<Right>", self._tab)
        self.entry.bind("<Tab>", self._tab)
        self.entry.bind("<Control-a>", self._select_all)
        
        # key browse entry
        self.key_browse_entry.bind("<FocusOut>", self._key_browse_hide)
        self.key_browse_entry.bind("<Escape>", self._key_browse_hide)
        self.key_browse_entry.bind("<Return>", self._key_browse_validate)

        # main bindings
        self.bind("<Control-h>", self.toggle_hidden)
        self.bind("<Alt-Left>", self._hist_backward)
        self.bind("<Alt-Right>", self._hist_forward)
        self.bind("<Alt-Up>", self._go_to_parent)
        self.bind("<Alt-Down>", self._go_to_child)
        self.bind("<Button-1>", self._unpost, add=True)
        self.bind("<FocusIn>", self._hide_listbox)

        if mode != "save":
            self.bind("<Control-l>", self.toggle_path_entry)
        if self.foldercreation:
            self.right_tree.bind("<Control-Shift-N>", self.create_folder)

        self.update_idletasks()
        self.lift()
        if mode == 'save':
            self.entry.selection_range(0, 'end')
            self.entry.focus_set() 
          
    def branch_button_click(self):
        global glo_path
        glo_path=path_button.global_path
        print("branch_button_click 함수 진입")
        print("glo_path: "+glo_path)
        
        if glo_path: #경로가 있다면
            if self.check_git_managed(glo_path)==True: # 오류발생 and self.is_git_top_level(element)==True:#gitrepo가 맞는경우
                #branch_menu.py를 실행시키기위한 인스턴스 만들기
                
                root=tk.Tk()
                branch_menu=BranchMenu(root)
                branch_menu.connect_other_py(glo_path)
                root.mainloop()  # Tkinter 이벤트 루프 시작
                
            else: #gitrepo가 아닌경우
                FileBrowser.error_message_window()
        else:#경로가 없는경우
            FileBrowser.error_message_window()
    #yuna 마우스휠클릭시 그 파일의 경로를 알아내고 stagelist.py실행하게 하는 함수
    def _select_special_mouse(self,event):
        x,y=event.x,event.y
        element=self.right_tree.identify('item',x=x,y=y)
        if element: #경로가 있다면
            if self.check_git_managed(element)==True: # 오류발생 and self.is_git_top_level(element)==True:#gitrepo가 맞는경우
                #stagelist.py를 실행시키기위한 인스턴스 만들기
                sroot=tk.Tk()
                stage_list=StageList(sroot)
                #StageList.__init__(self,sroot)
                stage_list.listpane(element)
                sroot.mainloop()  # Tkinter 이벤트 루프 시작
            else: #gitrepo가 아닌경우
                FileBrowser.error_message_window()
        else:#경로가 없는경우
            FileBrowser.error_message_window()
                 
    def _right_tree_select_all(self, event):
        if self.mode == 'opendir':
            tags = ['folder', 'folder_link']
        else:
            tags = ['file', 'file_link']
        items = self.right_tree.tag_has(tags[0]) + self.right_tree.tag_has(tags[1])
        self.right_tree.selection_clear()
        self.right_tree.selection_set(items)

    def _select_all(self, event):
        """Select all entry content."""
        event.widget.selection_range(0, "end")
        return "break"  # suppress class binding

    # ---  key browsing
    def _key_browse_hide(self, event):
        """Hide key browsing entry."""
        if self.key_browse_entry.winfo_ismapped():
            self.key_browse_entry.place_forget()
            self.key_browse_entry.delete(0, "end")

    def _key_browse_show(self, event):
        """Show key browsing entry."""
        if event.char.isalnum() or event.char in [".", "_", "(", "-", "*", "$"]:
            self.key_browse_entry.place(in_=self.right_tree, relx=0, rely=1,
                                        y=4, x=1, anchor="nw")
            self.key_browse_entry.focus_set()
            self.key_browse_entry.insert(0, event.char)

    def _key_browse_validate(self, event):
        """Hide key browsing entry and validate selection."""
        self._key_browse_hide(event)
        self.right_tree.focus_set()
        self.validate()

    def _key_browse(self, *args):
        """Use keyboard to browse tree."""
        self.key_browse_entry.unbind("<Up>")
        self.key_browse_entry.unbind("<Down>")
        deb = self.key_browse_entry.get().lower()
        if deb:
            if self.mode == 'opendir':
                children = list(self.right_tree.tag_has("folder"))
                children.extend(self.right_tree.tag_has("folder_link"))
                children.sort()
            else:
                children = self.right_tree.get_children("")
            self.paths_beginning_by = [i for i in children if split(i)[-1][:len(deb)].lower() == deb]
            sel = self.right_tree.selection()
            if sel:
                self.right_tree.selection_remove(*sel)
            if self.paths_beginning_by:
                self.paths_beginning_by_index = 0
                self._browse_list(0)
                self.key_browse_entry.bind("<Up>",
                                           lambda e: self._browse_list(-1))
                self.key_browse_entry.bind("<Down>",
                                           lambda e: self._browse_list(1))

    def _browse_list(self, delta):
        """
        Navigate between folders/files with Up/Down keys.

        Navigation between folders/files beginning by the letters in
        self.key_browse_entry.
        """
        self.paths_beginning_by_index += delta
        self.paths_beginning_by_index %= len(self.paths_beginning_by)
        sel = self.right_tree.selection()
        if sel:
            self.right_tree.selection_remove(*sel)
        path = abspath(join(self.history[self._hist_index],
                            self.paths_beginning_by[self.paths_beginning_by_index]))
        self.right_tree.see(path)
        self.right_tree.selection_add(path)

    # ---  column sorting
    def _sort_files_by_name(self, reverse):
        """Sort files and folders by (reversed) alphabetical order."""
        files = list(self.right_tree.tag_has("file"))
        files.extend(list(self.right_tree.tag_has("file_link")))
        folders = list(self.right_tree.tag_has("folder"))
        folders.extend(list(self.right_tree.tag_has("folder_link")))
        files.sort(reverse=reverse)
        folders.sort(reverse=reverse)

        for index, item in enumerate(folders):
            self.move_item(item, index)
        l = len(folders)

        for index, item in enumerate(files):
            self.move_item(item, index + l)
        self.right_tree.heading("#0",
                                command=lambda: self._sort_files_by_name(not reverse))

    def _sort_by_location(self, reverse):
        """Sort files by location."""
        l = [(self.right_tree.set(k, "location"), k) for k in self.right_tree.get_children('')]
        l.sort(reverse=reverse)
        for index, (val, k) in enumerate(l):
            self.move_item(k, index)
        self.right_tree.heading("location",
                                command=lambda: self._sort_by_location(not reverse))

    def _sort_by_size(self, reverse):
        """Sort files by size."""
        files = list(self.right_tree.tag_has("file"))
        files.extend(list(self.right_tree.tag_has("file_link")))
        nb_folders = len(self.right_tree.tag_has("folder"))
        nb_folders += len(list(self.right_tree.tag_has("folder_link")))
        files.sort(reverse=reverse, key=getsize)

        for index, item in enumerate(files):
            self.move_item(item, index + nb_folders)

        self.right_tree.heading("size",
                                command=lambda: self._sort_by_size(not reverse))

    def _sort_by_date(self, reverse):
        """Sort files and folders by modification date."""
        files = list(self.right_tree.tag_has("file"))
        files.extend(list(self.right_tree.tag_has("file_link")))
        folders = list(self.right_tree.tag_has("folder"))
        folders.extend(list(self.right_tree.tag_has("folder_link")))
        l = len(folders)
        folders.sort(reverse=reverse, key=getmtime)
        files.sort(reverse=reverse, key=getmtime)

        for index, item in enumerate(folders):
            self.move_item(item, index)
        for index, item in enumerate(files):
            self.move_item(item, index + l)

        self.right_tree.heading("date",
                                command=lambda: self._sort_by_date(not reverse))

    # ---  file selection
    def _file_selection_save(self, event):
        """Save mode only: put selected file name in name_entry."""
        sel = self.right_tree.selection()
        if sel:
            sel = sel[0]
            tags = self.right_tree.item(sel, "tags")
            if ("file" in tags) or ("file_link" in tags):
                self.entry.delete(0, "end")
                if self.path_bar.winfo_ismapped():
                    self.entry.insert(0, self.right_tree.item(sel, "text"))
                else:
                    # recently used files
                    self.entry.insert(0, sel)
                self.entry.selection_clear()
                self.entry.icursor("end")

    def _file_selection_openfile(self, event):
        """Put selected file name in path_entry if visible."""
        sel = self.right_tree.selection()
        if sel and self.entry.winfo_ismapped():
            self.entry.delete(0, 'end')
            self.entry.insert("end", self.right_tree.item(sel[0], "text"))
            self.entry.selection_clear()
            self.entry.icursor("end")

    def _file_selection_opendir(self, event):
        """
        Prevent selection of files in opendir mode and put selected folder
        name in path_entry if visible.
        """
        sel = self.right_tree.selection()
        if sel:
            for s in sel:
                tags = self.right_tree.item(s, "tags")
                if ("file" in tags) or ("file_link" in tags):
                    self.right_tree.selection_remove(s)
            sel = self.right_tree.selection()
            if len(sel) == 1 and self.entry.winfo_ismapped():
                self.entry.delete(0, 'end')
                self.entry.insert("end", self.right_tree.item(sel[0], "text"))
                self.entry.selection_clear()
                self.entry.icursor("end")

    def _shortcut_select(self, event):
        """Selection of a shortcut (left pane)."""
        sel = self.left_tree.selection()
        if sel:
            sel = sel[0]
            if sel != "recent":
                self.display_folder(sel)
            else:
                self._display_recents()

    def _display_recents(self):
        """Display recently used files/folders."""
        self.path_bar.grid_remove()
        self.right_tree.configure(displaycolumns=("location", "size", "date"))
        w = self.right_tree.winfo_width() - 305
        if w < 0:
            w = 250
        self.right_tree.column("#0", width=w)
        self.right_tree.column("location", stretch=False, width=100)
        self.right_tree.column("size", stretch=False, width=85)
        self.right_tree.column("date", width=120)
        #if self.foldercreation:
        #    self.b_new_folder.grid_remove()
        extension = self.filetypes[self.filetype.get()]
        files = self._recent_files.get()
        self.right_tree.delete(*self.right_tree.get_children(""))
        i = 0
        if self.mode == "opendir":
            paths = []
            for p in files:
                if isfile(p):
                    p = dirname(p)
                d, f = split(p)
                tags = [str(i % 2)]
                vals = ()
                if f:
                    if f[0] == ".":
                        tags.append("hidden")
                else:
                    f = "/"
                if isdir(p):
                    if islink(p):
                        tags.append("folder_link")
                    else:
                        tags.append("folder")
                    vals = (p, "", get_modification_date(p))
                if vals and p not in paths:
                    i += 1
                    paths.append(p)
                    self.right_tree.insert("", "end", p, text=f, tags=tags,
                                           values=vals)
        else:
            for p in files:
                d, f = split(p)
                tags = [str(i % 2)]
                vals = ()
                if f:
                    if f[0] == ".":
                        tags.append("hidden")
                else:
                    f = "/"
                if islink(p):
                    if isfile(p):
                        if extension == r".*$" or search(extension, f):
                            tags.append("file_link")
                            stats = stat(p)
                            vals = (p, display_size(stats.st_size),
                                    display_modification_date(stats.st_mtime))
                    elif isdir(p):
                        tags.append("folder_link")
                        vals = (p, "", get_modification_date(p))
                elif isfile(p):
                    if extension == r".*$" or search(extension, f):
                        tags.append("file")
                        stats = stat(p)
                        vals = (p, display_size(stats.st_size),
                                display_modification_date(stats.st_mtime))
                elif isdir(p):
                    tags.append("folder")
                    vals = (p, "", get_modification_date(p))
                if vals:
                    i += 1
                    self.right_tree.insert("", "end", p, text=f, tags=tags,
                                           values=vals)

    def _select(self, event):
        """display folder content on double click / Enter, validate if file."""
        
        sel = self.right_tree.selection()
        if sel:
            sel = sel[0]
            tags = self.right_tree.item(sel, "tags")
            if ("folder" in tags) or ("folder_link" in tags):
                self.display_folder(sel)
            elif self.mode != "opendir":
                self.validate(event)
        elif self.mode == "opendir":
            pass
            #self.validate(event)

      


    def _unpost(self, event):
        """Hide self.key_browse_entry."""
        if event.widget != self.key_browse_entry:
            self._key_browse_hide(event)

    def _hide_listbox(self, event):
        """Hide the path proposition listbox."""
        if event.widget not in [self.listbox, self.entry, self.listbox_frame]:
            self.listbox_frame.place_forget()

    def _change_filetype(self):
        """Update view on filetype change."""
        if self.path_bar.winfo_ismapped():
            self.display_folder(self.history[self._hist_index])
        else:
            self._display_recents()
        if self.mode == 'save':
            filename = self.entry.get()
            new_ext = self.filetypes[self.filetype.get()]
            if filename and not search(new_ext, filename):
                old_ext = search(r'\..+$', filename).group()
                exts = [e[2:].replace('\.', '.') for e in new_ext[:-1].split('|')]
                exts = [e for e in exts if search(r'\.[^\*]+$', e)]
                if exts:
                    filename = filename.replace(old_ext, exts[0])
                self.entry.delete(0, 'end')
                self.entry.insert(0, filename)

    # ---  path completion in entries: key bindings
    def _down(self, event):
        """Focus listbox on Down arrow press in entry."""
        self.listbox.focus_set()
        self.listbox.selection_set(0)

    def _tab(self, event):
        """Go to the end of selected text and remove selection on tab press."""
        self.entry = event.widget
        self.entry.selection_clear()
        self.entry.icursor("end")
        return "break"

    def _select_enter(self, event, d):
        """Change entry content on Return key press in listbox."""
        self.entry.delete(0, "end")
        self.entry.insert(0, join(d, self.listbox.selection_get()))
        self.entry.selection_clear()
        self.entry.focus_set()
        self.entry.icursor("end")

    def _select_mouse(self, event, d):
        """Change entry content on click in listbox."""
        self.entry.delete(0, "end")
        self.entry.insert(0, join(d, self.listbox.get("@%i,%i" % (event.x, event.y))))
        self.entry.selection_clear()
        self.entry.focus_set()
        self.entry.icursor("end")

    def _completion(self, action, modif, pos, prev_txt):
        """Complete the text in the path entry with existing folder/file names."""
        if self.entry.selection_present():
            sel = self.entry.selection_get()
            txt = prev_txt.replace(sel, '')
        else:
            txt = prev_txt
        if action == "0":
            self.listbox_frame.place_forget()
            txt = txt[:int(pos)] + txt[int(pos) + 1:]
        elif isabs(txt) or self.path_bar.winfo_ismapped():
            txt = txt[:int(pos)] + modif + txt[int(pos):]
            d, f = split(txt)
            if f and not (f[0] == "." and self.hide):
                if not isabs(txt):
                    d2 = join(self.history[self._hist_index], d)
                else:
                    d2 = d

                try:
                    root, dirs, files = walk(d2).send(None)
                    dirs.sort(key=lambda n: n.lower())
                    l2 = []
                    if self.mode != "opendir":
                        files.sort(key=lambda n: n.lower())
                        extension = self.filetypes[self.filetype.get()]
                        if extension == r".*$":
                            l2.extend([i.replace(" ", "\ ") for i in files if i[:len(f)] == f])
                        else:
                            for i in files:
                                if search(extension, i) and i[:len(f)] == f:
                                    l2.append(i.replace(" ", "\ "))
                    l2.extend([i.replace(" ", "\ ") + "/" for i in dirs if i[:len(f)] == f])

                except StopIteration:
                    # invalid content
                    l2 = []

                if len(l2) == 1:
                    self.listbox_frame.place_forget()
                    i = self.entry.index("insert")
                    self.entry.delete(0, "end")
                    self.entry.insert(0, join(d, l2[0]))
                    self.entry.selection_range(i + 1, "end")
                    self.entry.icursor(i + 1)

                elif len(l2) > 1:
                    self.listbox.bind("<Return>", lambda e, arg=d: self._select_enter(e, arg))
                    self.listbox.bind("<Button-1>", lambda e, arg=d: self._select_mouse(e, arg))
                    self.listbox_var.set(" ".join(l2))
                    self.listbox_frame.lift()
                    self.listbox.configure(height=len(l2))
                    self.listbox_frame.place(in_=self.entry, relx=0, rely=1,
                                             anchor="nw", relwidth=1)
                else:
                    self.listbox_frame.place_forget()
        return True

    def _go_left(self, event):
        """Move focus to left pane."""
        sel = self.left_tree.selection()
        if not sel:
            sel = expanduser("~")
        else:
            sel = sel[0]
        self.left_tree.focus_set()
        self.left_tree.focus(sel)

    # ---  go to parent/children folder with Alt+Up/Down
    def _go_to_parent(self, event):
        """Go to parent directory."""
        parent = dirname(self.path_var.get())
        self.display_folder(parent, update_bar=False)

    def _go_to_child(self, event):
        """Go to child directory."""
        lb = [b.get_value() for b in self.path_bar_buttons]
        i = lb.index(self.path_var.get())
        if i < len(lb) - 1:
            self.display_folder(lb[i + 1], update_bar=False)

    # ---  navigate in history with Alt+Left/ Right keys
    def _hist_backward(self, event):
        """Navigate backward in folder selection history."""
        if self._hist_index > -len(self.history):
            self._hist_index -= 1
            self.display_folder(self.history[self._hist_index], reset=False)

    def _hist_forward(self, event):
        """Navigate forward in folder selection history."""
        try:
            self.left_tree.selection_remove(*self.left_tree.selection())
        except TypeError:
            # error raised in python 2 by empty selection
            pass
        if self._hist_index < -1:
            self._hist_index += 1
            self.display_folder(self.history[self._hist_index], reset=False)

    def _update_path_bar(self, path):
        """Update the buttons in path bar."""
        for b in self.path_bar_buttons:
            b.destroy()
        self.path_bar_buttons = []
        if path == "/":
            folders = []
        else:
            folders = path.split(SEP)
            while '' in folders:
                folders.remove('')
        if OSNAME == 'nt':
            p = folders.pop(0) + '\\'
            b = PathButton(self.path_bar, self.path_var, p, text=p,
                           command=lambda path=p: self.display_folder(path, update_bar=False))
        else:
            p = "/"
            b = PathButton(self.path_bar, self.path_var, p, image=self.im_drive,
                           command=lambda path=p: self.display_folder(path, update_bar=False))
        self.path_bar_buttons.append(b)
        b.grid(row=0, column=1, sticky="ns")
        for i, folder in enumerate(folders):
            p = join(p, folder)
            b = PathButton(self.path_bar, self.path_var, p, text=folder,
                           command=lambda f=p: self.display_folder(f, update_bar=False),
                           style="path.tkfilebrowser.TButton")
            self.path_bar_buttons.append(b)
            b.grid(row=0, column=i + 2, sticky="ns")

    def _display_folder_listdir(self, folder, reset=True, update_bar=True):
        """
        Display the content of folder in self.right_tree.
        Arguments:
            * reset (boolean): forget all the part of the history right of self._hist_index
            * update_bar (boolean): update the buttons in path bar
        """
        # remove trailing / if any
        folder = abspath(folder)
        # reorganize display if previous was 'recent'
        if not self.path_bar.winfo_ismapped():
            self.path_bar.grid()
            self.right_tree.configure(displaycolumns=("size", "date"))
            w = self.right_tree.winfo_width() - 205
            if w < 0:
                w = 250
            self.right_tree.column("#0", width=w)
            self.right_tree.column("size", stretch=False, width=85)
            self.right_tree.column("date", width=120)
            #if self.foldercreation:
            #    self.b_new_folder.grid()
        # reset history
        if reset:
            if not self._hist_index == -1:
                self.history = self.history[:self._hist_index + 1]
                self._hist_index = -1
            self.history.append(folder)
        # update path bar
        if update_bar:
            self._update_path_bar(folder)
        self.path_var.set(folder)
        # disable new folder creation if no write access
        if self.foldercreation:
            if access(folder, W_OK):
                #self.b_new_folder.state(('!disabled',))
                pass
            else:
                #self.b_new_folder.state(('disabled',))
                pass
        # clear self.right_tree
        self.right_tree.delete(*self.right_tree.get_children(""))
        self.right_tree.delete(*self.hidden)
        self.hidden = ()
        root = folder
        extension = self.filetypes[self.filetype.get()]
        content = listdir(folder)
        i = 0
        for f in content:
            p = join(root, f)
            if f[0] == ".":
                tags = ("hidden",)
                if not self.hide:
                    tags = (str(i % 2),)
                    i += 1
            else:
                tags = (str(i % 2),)
                i += 1
            if isfile(p):
                if extension == r".*$" or search(extension, f):
                    if islink(p):
                        tags = tags + ("file_link",)
                    else:
                        tags = tags + ("file",)
                    try:
                        stats = stat(p)
                    except OSError:
                        self.right_tree.insert("", "end", p, text=f, tags=tags,
                                               values=("", "??", "??"))
                    else:
                        self.right_tree.insert("", "end", p, text=f, tags=tags,
                                               values=("",
                                                       display_size(stats.st_size),
                                                       display_modification_date(stats.st_mtime)))
            elif isdir(p):
                if islink(p):
                    tags = tags + ("folder_link",)
                else:
                    tags = tags + ("folder",)

                self.right_tree.insert("", "end", p, text=f, tags=tags,
                                       values=("", "", get_modification_date(p)))
            else:  # broken link
                tags = tags + ("link_broken",)
                self.right_tree.insert("", "end", p, text=f, tags=tags,
                                       values=("", "??", "??"))

        items = self.right_tree.get_children("")
        if items:
            self.right_tree.focus_set()
            self.right_tree.focus(items[0])
        if self.hide:
            self.hidden = self.right_tree.tag_has("hidden")
            self.right_tree.detach(*self.right_tree.tag_has("hidden"))
        self._sort_files_by_name(False)

    def _display_folder_walk(self, folder, reset=True, update_bar=True):
        """
        Display the content of folder in self.right_tree.
        Arguments:
            * reset (boolean): forget all the part of the history right of self._hist_index
            * update_bar (boolean): update the buttons in path bar
        """
        # remove trailing / if any
        folder = abspath(folder)
        # reorganize display if previous was 'recent'
        if not self.path_bar.winfo_ismapped():
            self.path_bar.grid()
            self.right_tree.configure(displaycolumns=("size", "date"))
            w = self.right_tree.winfo_width() - 205
            if w < 0:
                w = 250
            self.right_tree.column("#0", width=w)
            self.right_tree.column("size", stretch=False, width=85)
            self.right_tree.column("date", width=120)
            #if self.foldercreation:
            #    self.b_new_folder.grid()
        # reset history
        if reset:
            if not self._hist_index == -1:
                self.history = self.history[:self._hist_index + 1]
                self._hist_index = -1
            self.history.append(folder)
        # update path bar
        if update_bar:
            self._update_path_bar(folder)
        self.path_var.set(folder)
        # disable new folder creation if no write access
        if self.foldercreation:
            if access(folder, W_OK):
                #self.b_new_folder.state(('!disabled',))
                pass
            else:
                #self.b_new_folder.state(('disabled',))
                pass
        # clear self.right_tree
        self.right_tree.delete(*self.right_tree.get_children(""))
        self.right_tree.delete(*self.hidden)
        self.hidden = ()
        try:
            root, dirs, files = walk(folder).send(None)
            # display folders first
            dirs.sort(key=lambda n: n.lower())
            i = 0
            for d in dirs:
                p = join(root, d)
                if islink(p):
                    tags = ("folder_link",)
                else:
                    tags = ("folder",)
                if d[0] == ".":
                    tags = tags + ("hidden",)
                    if not self.hide:
                        tags = tags + (str(i % 2),)
                        i += 1
                else:
                    tags = tags + (str(i % 2),)
                    i += 1
                self.right_tree.insert("", "end", p, text=d, tags=tags,
                                       values=("", "", get_modification_date(p)))
            # display files
            files.sort(key=lambda n: n.lower())
            extension = self.filetypes[self.filetype.get()]
            for f in files:
                if extension == r".*$" or search(extension, f):
                    p = join(root, f)
                    if islink(p):
                        tags = ("file_link",)
                    else:
                        tags = ("file",)
                    try:
                        stats = stat(p)
                    except FileNotFoundError:
                        stats = Stats(st_size="??", st_mtime="??")
                        tags = ("link_broken",)
                    if f[0] == ".":
                        tags = tags + ("hidden",)
                        if not self.hide:
                            tags = tags + (str(i % 2),)
                            i += 1
                    else:
                        tags = tags + (str(i % 2),)
                        i += 1

                    self.right_tree.insert("", "end", p, text=f, tags=tags,
                                           values=("",
                                                   display_size(stats.st_size),
                                                   display_modification_date(stats.st_mtime)))
            items = self.right_tree.get_children("")
            if items:
                self.right_tree.focus_set()
                self.right_tree.focus(items[0])
            if self.hide:
                self.hidden = self.right_tree.tag_has("hidden")
                self.right_tree.detach(*self.right_tree.tag_has("hidden"))
        except StopIteration:
            self._display_folder_listdir(folder, reset, update_bar)
        except PermissionError as e:
            cst.showerror('PermissionError', str(e), master=self)

    def _display_folder_scandir(self, folder, reset=True, update_bar=True):
        """
        Display the content of folder in self.right_tree.

        Arguments:
            * reset (boolean): forget all the part of the history right of self._hist_index
            * update_bar (boolean): update the buttons in path bar
        """
        # remove trailing / if any
        folder = abspath(folder)
        # reorganize display if previous was 'recent'
        if not self.path_bar.winfo_ismapped():
            self.path_bar.grid()
            self.right_tree.configure(displaycolumns=("size", "date"))
            w = self.right_tree.winfo_width() - 205
            if w < 0:
                w = 250
            self.right_tree.column("#0", width=w)
            self.right_tree.column("size", stretch=False, width=85)
            self.right_tree.column("date", width=120)
            #if self.foldercreation:
            #    self.b_new_folder.grid()
        # reset history
        if reset:
            if not self._hist_index == -1:
                self.history = self.history[:self._hist_index + 1]
                self._hist_index = -1
            self.history.append(folder)
        # update path bar
        if update_bar:
            self._update_path_bar(folder)
        self.path_var.set(folder)
        # disable new folder creation if no write access
        if self.foldercreation:
            if access(folder, W_OK):
                #self.b_new_folder.state(('!disabled',))
                pass
            else:
                #self.b_new_folder.state(('disabled',))
                pass
        # clear self.right_tree
        self.right_tree.delete(*self.right_tree.get_children(""))
        self.right_tree.delete(*self.hidden)
        self.hidden = ()
        extension = self.filetypes[self.filetype.get()]
        try:
            content = sorted(scandir(folder), key=key_sort_files)
            i = 0
            tags_array = [["folder", "folder_link"],
                          ["file", "file_link"]]
            for f in content:
                b_file = f.is_file()
                name = f.name
                try:
                    stats = f.stat()
                    tags = (tags_array[b_file][f.is_symlink()],)
                except FileNotFoundError:
                    stats = Stats(st_size="??", st_mtime="??")
                    tags = ("link_broken",)
                if name[0] == '.':
                    tags = tags + ("hidden",)
                    if not self.hide:
                        tags = tags + (str(i % 2),)
                        i += 1
                else:
                    tags = tags + (str(i % 2),)
                    i += 1
                if b_file:
                    if extension == r".*$" or search(extension, name):
                        self.right_tree.insert("", "end", f.path, text=name, tags=tags,
                                               values=("",
                                                       display_size(stats.st_size),
                                                       display_modification_date(stats.st_mtime)))
                else:
                    self.right_tree.insert("", "end", f.path, text=name, tags=tags,
                                           values=("", "",
                                                   display_modification_date(stats.st_mtime)))
            items = self.right_tree.get_children("")
            if items:
                self.right_tree.focus_set()
                self.right_tree.focus(items[0])
            if self.hide:
                self.hidden = self.right_tree.tag_has("hidden")
                self.right_tree.detach(*self.right_tree.tag_has("hidden"))
        except FileNotFoundError:
            self._display_folder_scandir(expanduser('~'), reset=True, update_bar=True)
        except PermissionError as e:
            cst.showerror('PermissionError', str(e), master=self)

    def create_folder(self, event=None):
        """Create new folder in current location."""
        def ok(event):
            name = e.get()
            e.destroy()
            if name:
                folder = join(path, name)
                try:
                    mkdir(folder)
                except Exception:
                    # show exception to the user (typically PermissionError or FileExistsError)
                    cst.showerror(_("Error"), traceback.format_exc())
                self.display_folder(path)

        def cancel(event):
            e.destroy()
            self.right_tree.delete("tmp")

        path = self.path_var.get()

        if self.path_bar.winfo_ismapped() and access(path, W_OK):
            self.right_tree.insert("", 0, "tmp", tags=("folder", "1"))
            self.right_tree.see("tmp")
            e = ttk.Entry(self)
            x, y, w, h = self.right_tree.bbox("tmp", column="#0")
            e.place(in_=self.right_tree, x=x + 24, y=y,
                    width=w - x - 4)
            e.bind("<Return>", ok)
            e.bind("<Escape>", cancel)
            e.bind("<FocusOut>", cancel)
            e.focus_set()

    def move_item(self, item, index):
        """Move item to index and update dark/light line alternance."""
        self.right_tree.move(item, "", index)
        tags = [t for t in self.right_tree.item(item, 'tags')
                if t not in ['1', '0']]
        tags.append(str(index % 2))
        self.right_tree.item(item, tags=tags)

    def toggle_path_entry(self, event):
        """Toggle visibility of path entry."""
        if self.entry.winfo_ismapped():
            self.entry.grid_remove()
            self.entry.delete(0, "end")
        else:
            self.entry.grid()
            self.entry.focus_set()

    def toggle_hidden(self, event=None):
        """Toggle the visibility of hidden files/folders."""
        if self.hide:
            self.hide = False
            for item in reversed(self.hidden):
                self.right_tree.move(item, "", 0)
            self.hidden = ()
        else:
            self.hide = True
            self.hidden = self.right_tree.tag_has("hidden")
            self.right_tree.detach(*self.right_tree.tag_has("hidden"))
        # restore color alternance
        for i, item in enumerate(self.right_tree.get_children("")):
            tags = [t for t in self.right_tree.item(item, 'tags')
                    if t not in ['1', '0']]
            tags.append(str(i % 2))
            self.right_tree.item(item, tags=tags)

    def get_result(self):
        """Return selection."""
        return self.result

    def quit(self):
        """Destroy dialog."""
        self.destroy()
        if self.result:
            if isinstance(self.result, tuple):
                for path in self.result:
                    self._recent_files.add(path)
            else:
                self._recent_files.add(self.result)

    def _validate_save(self):
        """Validate selection in save mode."""
        name = self.entry.get()
        if name:
            ext = splitext(name)[-1]
            if not ext and not name[-1] == "/":
                # append default extension if none given
                name += self.defaultext
            if isabs(name):
                # name is an absolute path
                if exists(dirname(name)):
                    rep = True
                    if isfile(name):
                        rep = cst.askyesnocancel(_("Confirmation"),
                                                 _("The file {file} already exists, do you want to replace it?").format(file=name),
                                                 icon="warning")
                    elif isdir(name):
                        # it's a directory
                        rep = False
                        self.display_folder(name)
                    path = name
                else:
                    # the path is invalid
                    rep = False
            elif self.path_bar.winfo_ismapped():
                # we are not in the "recent files"
                path = join(self.history[self._hist_index], name)
                rep = True
                if exists(path):
                    if isfile(path):
                        rep = cst.askyesnocancel(_("Confirmation"),
                                                 _("The file {file} already exists, do you want to replace it?").format(file=name),
                                                 icon="warning")
                    else:
                        # it's a directory
                        rep = False
                        self.display_folder(path)
                elif not exists(dirname(path)):
                    # the path is invalid
                    rep = False
            else:
                # recently used file
                sel = self.right_tree.selection()
                if len(sel) == 1:
                    path = sel[0]
                    tags = self.right_tree.item(sel, "tags")
                    if ("folder" in tags) or ("folder_link" in tags):
                        rep = False
                        self.display_folder(path)
                    elif isfile(path):
                        rep = cst.askyesnocancel(_("Confirmation"),
                                                 _("The file {file} already exists, do you want to replace it?").format(file=name),
                                                 icon="warning")
                    else:
                        rep = True
                else:
                    rep = False

            if rep:
                self.result = realpath(path)
                self.quit()
            elif rep is None:
                self.quit()
            else:
                self.entry.delete(0, "end")
                self.entry.focus_set()

    def _validate_from_entry(self):
        """
        Validate selection from path entry in open mode.

        Return False if the entry is empty, True otherwise.
        """
        name = self.entry.get()
        if name:  # get file/folder from entry
            if not isabs(name) and self.path_bar.winfo_ismapped():
                # we are not in the "recent files"
                name = join(self.history[self._hist_index], name)
            if not exists(name):
                self.entry.delete(0, "end")
            elif self.mode == "openfile":
                if isfile(name):
                    if self.multiple_selection:
                        self.result = (realpath(name),)
                    else:
                        self.result = realpath(name)
                    self.quit()
                else:
                    self.display_folder(name)
                    self.entry.grid_remove()
                    self.entry.delete(0, "end")
            else:
                if self.multiple_selection:
                    self.result = (realpath(name),)
                else:
                    self.result = realpath(name)
                self.quit()
            return True
        else:
            return False

    def _validate_multiple_sel(self):
        """Validate selection in open mode with multiple selection."""
        sel = self.right_tree.selection()
        if self.mode == "opendir":
            if sel:
                self.result = tuple(realpath(s) for s in sel)
            else:
                self.result = (realpath(self.history[self._hist_index]),)
            self.quit()
        else:  # mode == openfiles
            if len(sel) == 1:
                sel = sel[0]
                tags = self.right_tree.item(sel, "tags")
                if ("folder" in tags) or ("folder_link" in tags):
                    self.display_folder(sel)
                else:
                    self.result = (realpath(sel),)
                    self.quit()
            elif len(sel) > 1:
                files = tuple(s for s in sel if "file" in self.right_tree.item(s, "tags"))
                files = files + tuple(realpath(s) for s in sel if "file_link" in self.right_tree.item(s, "tags"))
                if files:
                    self.result = files
                    self.quit()
                else:
                    self.right_tree.selection_remove(*sel)

    def _validate_single_sel(self):
        """Validate selection in open mode without multiple selection."""
        sel = self.right_tree.selection()
        if self.mode == "openfile":
            if len(sel) == 1:
                sel = sel[0]
                tags = self.right_tree.item(sel, "tags")
                if ("folder" in tags) or ("folder_link" in tags):
                    self.display_folder(sel)
                else:
                    self.result = realpath(sel)
                    self.quit()
        else:  # mode is "opendir"
            if len(sel) == 1:
                self.result = realpath(sel[0])
            else:
                self.result = realpath(self.history[self._hist_index])
            self.quit()

    def validate(self, event=None):
        """Validate selection and store it in self.results if valid."""
        if self.mode == "save":
            self._validate_save()
        else:
            validation = self._validate_from_entry()
            if not validation:
                # the entry is empty
                if self.multiple_selection:
                    self._validate_multiple_sel()
                else:
                    self._validate_single_sel()

                    


#### Git ####
    
    ### folder ###
    # git repo인지 check
    def check_git_managed(self, path):
        git_dir = os.path.join(path, ".git")
        if os.path.exists(git_dir) and os.path.isdir(git_dir):
            return True
        return False

    # git init
    def git_init(self, path):
        if self.check_git_managed(path):
            return False
        
        try:
            subprocess.run(["git", "init", path])
            messagebox.showinfo("Git initialized", "Git repository initialized successfully.")
            return True
        except:
            messagebox.showerror("Git initialization failed", "Failed to initialize git repository.")
            return False

    
    ### file ###
    # file의 git status check
    def check_file_status(self, file_path):
        # 해당 파일이 속한 폴더 찾기
        folder_path = os.path.abspath(os.path.join(file_path, os.pardir))

        # 해당 폴더가 git repository에 연결되어 있는지 확인
        if not self.check_git_managed(folder_path):
            messagebox.showinfo("Folder Status", f"{folder_path} is not a git repository")
            return

        # git status 실행
        cmd = ["git", "status", "-s", "--", file_path]
        result = subprocess.check_output(cmd, cwd=folder_path)

        # git status 결과 확인하여 파일 상태 변경
        status = result.decode()
        if status != "":
            status = result.decode()[:2]            

        return status, folder_path

    # git add
    # untracked, modified 일 때 실행
    def git_add(self, file_path, folder_path):
        
        try:
            cmd = ["git", "add", "--", file_path]
            subprocess.run(cmd, cwd=folder_path)
            messagebox.showinfo("File Status", f"{file_path} is now being staged")
            return True
        except:
            messagebox.showinfo("File Status", f"{file_path} cannot do git add")
            return False

    # git restore
    # modified 일 때 실행
    def git_restore(self, file_path, folder_path):
        try:
            cmd = ["git", "restore", "--", file_path]
            subprocess.run(cmd, cwd=folder_path)
            messagebox.showinfo("File Status", f"{file_path} is now unmodified")
            return True
        except:
            messagebox.showinfo("File Status", f"{file_path} cannot do git restore")
            return False


    # git restore --staged
    # staged 일 때 실행
    def git_restore_staged(self, file_path, folder_path):
        
        try:
            cmd = ["git", "reset", "HEAD", "--", file_path]
            subprocess.run(cmd, cwd=folder_path)
            messagebox.showinfo("File Status", f"{file_path} is now modified or untracked")
            return True
        except:
            messagebox.showinfo("File Status", f"{file_path} cannot do git restore --staged")
            return False

    # git rm -- cached
    # committed or unmodified 파일
    def git_rm_cached(self, file_path, folder_path):

        try:
            cmd = ["git", "rm", "--cached", "--", file_path]
            subprocess.run(cmd, cwd=folder_path)
            messagebox.showinfo("File Status", f"{file_path} is now untracked")
            return True
        except:
            messagebox.showinfo("File Status", f"{file_path} cannot do git rm --cached")
            return False
    
    # git rm
    # committed or unmodified 파일
    def git_rm(self, file_path, folder_path):
        
        try:
            cmd = ["git", "rm", "--", file_path]
            subprocess.run(cmd, cwd=folder_path)
            messagebox.showinfo("File Status", f"{file_path} is now removed")
            return True
        except:
            messagebox.showinfo("File Status", f"{file_path} cannot do git rm")
            return False
        
    # Renaming : git mv oldname newname
    # committed or unmodified 파일
    def git_mv(self, old_path, folder_path, new_path):
        
        new_path = os.path.join(folder_path, new_path)

        try:
            subprocess.run(["git", "mv", old_path, new_path], cwd=folder_path)
            messagebox.showinfo("File Status", f"{old_path} renamed to {new_path}")
        except:
            messagebox.showinfo("File Status", f"Failed to rename {old_path} to {new_path}")

    ##### commit    
    
    # 선택된 folder가 git과 연결된 최상위 폴더인지 확인
    # input : folder path
    def is_git_top_level(self, folder_path):
        # 해당 폴더의 Git 최상위 경로 확인
        cmd = ["git", "rev-parse", "--show-toplevel"]
        result = subprocess.run(cmd, cwd=folder_path, capture_output=True, text=True)
        git_top_level = result.stdout.strip()

        # 폴더 경로가 Git 최상위 경로와 일치하는지 확인
        return os.path.abspath(folder_path) == os.path.abspath(git_top_level)
    
    # staging list 출력
    def staged_list(self, folder_path):
        # 해당 폴더가 git에 연결된 최상위 디렉토리 이면 commit 버튼 누를 수 있음 -> staged list 절대 경로 반환
        if not self.is_git_top_level(folder_path):
            messagebox.showinfo("Folder Status", f"{folder_path} is not a top level git repository")
            return
        
        # Staging Area에 있는 파일 목록 가져오기
        cmd = ["git", "diff", "--cached", "--name-only"]
        result = subprocess.run(cmd, cwd=folder_path, capture_output=True, text=True)
        staged_files = result.stdout.strip().splitlines()

        # 파일의 절대 경로 반환
        staged_file_paths = [os.path.join(folder_path, file) for file in staged_files]
        return staged_file_paths
        
    # git commit
    def git_commit(self, file_path, commit_message):
        try:
            # git commit 실행
            cmd = ["git", "commit", "-m", commit_message, "--", file_path]
            subprocess.run(cmd, check=True)
            messagebox.showinfo("File Status", "Git commit successful.")
            return True
        except subprocess.CalledProcessError as e:
            messagebox.showinfo("File Status", f"Git commit failed: {e}")
            return False
    
    ### Branch Management
    
    # input : folder_path -> output : 현재 branch 이름 (git에 의해 관리되지 않으면 None 반환)
    def current_branch(self, folder_path):
        if not self.check_git_managed(folder_path):
            return None
        else:
            cmd = ["git", "branch", "--show-current"]
            result = subprocess.run(cmd, cwd=folder_path, capture_output=True, text=True)
            branch_name = result.stdout.strip()
            return branch_name
    
    # input : 새로운 branch 이름, folder path -> 새로운 branch 생성
    def branch_create(self, folder_path, branch_name):
        try:
            cmd = ["git", "branch", branch_name]
            subprocess.run(cmd, cwd=folder_path)
            messagebox.showinfo("Branch Status", f"Branch '{branch_name}' created successfully.")
            return True
        except Exception as e:
            messagebox.showinfo("Branch Status", f"An error occurred: {e}")
            return False
    
    # input : folder_path -> output : 현재 git repo에 있는 branch 이름 list 반환(git에 의해 관리되지 않으면 빈 list 반환)
    def branch_list(self, folder_path):
        if not self.check_git_managed(folder_path):
            return []
        else:
            cmd = ["git", "branch"]
            result = subprocess.check_output(cmd, cwd=folder_path, universal_newlines=True)
            branches = [branch.strip() for branch in result.splitlines()]
            return branches
    
    # input : folder_path -> output : current branch 제외한 나머지 branch list 반환
    def get_other_branches(self, folder_path):
        current_branch = self.current_branch(folder_path)
        branches = self.branch_list(folder_path)
        
        other_branches = [branch for branch in branches if branch != current_branch]
        return other_branches
    
    # input : folder_path, 삭제하고 싶은 branch 이름 -> output : 해당 branch가 있으면 삭제, 없으면 오류 메시지
    def branch_delete(self, folder_path, branch_name):
        try:
            cmd = ["git", "branch", "-D", branch_name]
            subprocess.run(cmd, cwd=folder_path)
            messagebox.showinfo("Branch Status", f"The branch '{branch_name}' has been deleted.")
            return True
        except subprocess.CalledProcessError as e:
            messagebox.showinfo("Branch Status", f"The branch '{branch_name}' does not exist.")
            return False

    
    # input : folder_path, 기존 branch 이름, 새로운 branch 이름 -> output : 기존 branch 이름이 존재하면 rename, 없으면 오류 메시지
    def branch_rename(self, folder_path, old_branch_name, new_branch_name):
        try:
            cmd = ["git", "branch", "-m", old_branch_name, new_branch_name]
            subprocess.run(cmd, cwd=folder_path)
            messagebox.showinfo("Branch Status", f"The branch '{old_branch_name}' has been renamed to '{new_branch_name}'.")
            return True
        except subprocess.CalledProcessError as e:
            messagebox.showinfo("Branch Status", f"Failed to rename the branch '{old_branch_name}'.")
            return False
    
    # input : folder_path, 바꾸고 싶은 branch 이름 -> output : 있으면 checkout, 없으면 오류 메시지
    def branch_checkout(self, folder_path, branch_name):
        try:
            cmd = ["git", "checkout", branch_name]
            subprocess.run(cmd, cwd=folder_path)
            messagebox.showinfo("Branch Status", f"Switched to the branch '{branch_name}'.")
            return True
        except subprocess.CalledProcessError as e:
            messagebox.showinfo("Branch Status", f"Failed to switch to the branch '{branch_name}'.")
            return False
    
    
    ### Branch Merge
    
    # input : folder_path, git merge 하고 싶은 branch 이름 
    # output : success 이면 True, error 이면 git merge abort 하고, False와 unmerged paths 담은 messagebox 띄움
    def merge_branch(self, folder_path, branch_name):
        # 해당 폴더가 git repository에 연결되어 있는지 확인
        if not self.check_git_managed(folder_path):
            return False

        try:
            # git merge 수행
            cmd_merge = ["git", "merge", branch_name]
            subprocess.run(cmd_merge, cwd=folder_path)

            # merge 중에 발생한 충돌 또는 에러 확인
            if subprocess.call(["git", "merge", "--no-commit", "--no-ff", branch_name], cwd=folder_path) != 0:
                cmd_status = ["git", "status", "-s", "--unmerged"]
                result = subprocess.check_output(cmd_status, cwd=folder_path, universal_newlines=True)
                unmerged_paths = [line.split()[1] for line in result.splitlines()]

                if unmerged_paths:
                    subprocess.run(["git", "merge", "--abort"], cwd=folder_path)
                    messagebox.showinfo("Git Status", f"Merge aborted due to conflicts or errors.\n\nUnmerged paths: {unmerged_paths}")
                    return False
                else:
                    messagebox.showinfo("Git Status", "Merge completed successfully.")
                    return True

        except subprocess.CalledProcessError as e:
            messagebox.showinfo("Git Status", f"Merge failed with error: {e}")
            return False    
    
    ### Git Commit History
    
    # input - folder_path, output - 현재 branchdml commit history - hash, 작성자 이름, 메시지 dic 타입의 list로 만들어서 반환
    def git_commit_history(self, folder_path):
        # 해당 폴더가 git repository에 연결되어 있는지 확인
        
        if not self.check_git_managed(folder_path):
            messagebox.showinfo("Folder Status", f"{folder_path} is not a git repository")
            return None
        

        # 현재 브랜치 이름 가져오기
        current_branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=folder_path, text=True).strip()
        #print(current_branch)
        #print(folder_path)
        

        # 현재 브랜치의 workflow 커밋 히스토리 가져오기
        cmd = ["git", "log", "--oneline", "--graph", "--branches", "--decorate", "--pretty=format:%h, %an, %s", current_branch]
        result = subprocess.check_output(cmd, cwd=folder_path, text=True, encoding='utf-8')
        

        # 개행 문자로 분리하여 각 커밋의 작성자 이름과 메시지를 추출하여 리스트로 반환
        commit_history = []
        for line in result.strip().split('\n'):
            try:
                if line.startswith('* '):
                    line = line[2:]  # "*" 제거
                commit_hash, rest = line.split(',', 1)
                commit_hash = commit_hash.strip().split(' ')[-1]  # 커밋 해시에서 불필요한 문자 제거
                author_name, message = rest.lstrip().split(',', 1)
                message = message.strip()
                
                commit_history.append({
                    'hash': commit_hash,
                    'author': author_name,
                    'message': message
                })
                
            except (UnicodeDecodeError, ValueError):
                continue
        return commit_history
            
    
    # input - foler_path, commit_object_hash -> output : dict 타입으로 commit_hash, author_name, commit_date(ISO 8601 형식), commit_message 반환
    def commit_object_detail(self, folder_path, commit_hash):
        cmd = ["git", "show", "--no-patch", "--format=%an|%ad|%s", commit_hash]
        result = subprocess.run(cmd, cwd=folder_path, capture_output=True, text=True, encoding='utf-8')

        if result.returncode != 0:
            # Commit not found
            return None

        commit_info = result.stdout.strip()
        author_name, commit_date, commit_message = commit_info.split('|')
        commit_date = datetime.datetime.strptime(commit_date, '%a %b %d %H:%M:%S %Y %z').strftime('%Y-%m-%d %H:%M:%S')

        return {
            'commit_hash': commit_hash,
            'author_name': author_name,
            'commit_date': commit_date,
            'commit_message': commit_message
        }

    
    ### Git clone from GitHub
    
    # public repo : input - clone 할 git repo address, 로컬 path -> output : git clone 수행 -> 결과 값에 따른 messagebox 띄움
    def git_clone_public(self, repository_url, destination_path):
        try:
            cmd = ["git", "clone", repository_url, destination_path]
            subprocess.run(cmd)
            messagebox.showinfo("Git Clone Status", "Git clone completed successfully.")
            return True

        except subprocess.CalledProcessError as e:
            messagebox.showinfo("Git Clone Status", f"Clone failed with error: {e}")
            return False
    
    # private repo : input - clone 할 git repo address, 로컬 path, personal access token -> output : git clone 수행 -> 결과 값에 따른 messagebox
    def git_clone_private(self,repository_url, destination_path, access_token):
        repo_url=repository_url.replace("https://","")
        try:
            cmd = ["git", "clone", "https://"+access_token+"@"+repo_url]
            subprocess.run(cmd, cwd=destination_path)
            '''
            env = {
                "GIT_ASKPASS": "echo",  # 인증 정보 요청 시 터미널 대화식 프롬프트를 사용하지 않도록 설정
                "GIT_TOKEN": access_token  # 액세스 토큰 설정
            }
            '''
            #subprocess.run(cmd, env=env,check=True)
            messagebox.showinfo("Git Clone Status", "Git clone completed successfully.")
            return True

        except subprocess.CalledProcessError as e:
            messagebox.showinfo("Git Clone Status", f"Clone failed with error: {e}")
            return False

    def clone_button_click(self):
        global glo_path
        glo_path=path_button.global_path
        destination_path=glo_path
        print("branch_button_click 함수 진입")
        print("glo_path: "+glo_path)
        if glo_path: #경로가 있다면
            if self.check_git_managed(glo_path)==True:
                FileBrowser.error_message_window() #이미 git repo면 안되얌
            else: #gitrepo가 아닌경우
                response = messagebox.askquestion("Question", "Is remote repository Private?")
                if response == 'yes':
                    print("User chose A")
                    self.choose_private(destination_path)
                elif response == 'no':
                    print("User chose B")
                    self.choose_public(destination_path)
        else:#경로가 없는경우
            FileBrowser.error_message_window()
        '''
        root = tk.Tk()

        label = tk.Label(root, text="Choose Public or Private")
        label.pack(side="top")
        button_a = tk.Button(root, text="Public", command=self.choose_public(destination_path))
        button_a.pack(side="left")
        button_b = tk.Button(root, text="Private", command=self.choose_private(destination_path))
        button_b.pack(side="right")
        root.mainloop()
        '''
    def choose_public(self,destination_path):
        print("public")
        url = simpledialog.askstring("url", "Enter github url")
        if url:
            self.git_clone_public(url,destination_path)
        else:
            messagebox.showwarning("알림", "주소 입력안함")
    def choose_private(self,destination_path):
        print("private")
        url = simpledialog.askstring("url", "Enter github url")
        if url:
            access_token=simpledialog.askstring("access token", "Enter access token")
            if access_token:
                self.git_clone_private(url,destination_path,access_token)
            else:
                messagebox.showwarning("알림", "토큰입력안함")
        else:
            messagebox.showwarning("알림", "주소입력안함")
          
    #우클릭시

    def _select_rightmouse(self, event):    
        x, y = event.x, event.y
        element = self.right_tree.identify('item',x=x, y=y) # 마우스 우클릭한 위치에 해당하는 요소 반환 - 파일 경로
        

        if element:
            sel = self.right_tree.selection()
            sel = sel[0] if sel else None
            if sel == element:
                tags = self.right_tree.item(sel, "tags")

                if ("folder" in tags) or ("folder_link" in tags): # folder일 경우
                    if(self.check_git_managed(element)):

                        self.foldermenu.delete(0, tk.END) 
                        self.foldermenu.add_command(label="<Already Git repository>")
                        self.foldermenu.tk_popup(event.x_root, event.y_root, 0)
                    else:
                        self.foldermenu.delete(0, tk.END) 
                        self.foldermenu.add_command(label="Create git repo", command=lambda: self.show_popup_create(element))
                        self.foldermenu.tk_popup(event.x_root, event.y_root, 0)
                elif self.mode == "openfile": # file일 경우
                    status, folder_path = self.check_file_status(element)
                    
                    if status is not None: #해당 파일의 상위 폴더가 git repo라면
                        if status == "??": #untracked
                            self.filemenu_untracked.delete(0, tk.END)
                            self.filemenu_untracked.add_command(label='<untracked>')
                            self.filemenu_untracked.add_separator()  # 구분선 추가
                            self.filemenu_untracked.add_command(label="go to stage", command=lambda: self.show_popup_untracked(element))
                            self.filemenu_untracked.tk_popup(event.x_root, event.y_root, 0)
                        elif status == "": #committed
                            self.filemenu_commited.delete(0, tk.END)
                            self.filemenu_commited.add_command(label='<committed>')
                            self.filemenu_commited.add_separator()
                            self.filemenu_commited.add_command(label="untrack", command=lambda: self.show_popup_commited(element, "untrack"))
                            self.filemenu_commited.add_command(label="delete", command=lambda: self.show_popup_commited(element, "delete"))
                            self.filemenu_commited.add_command(label="rename", command=lambda: self.show_popup_commited(element, "rename"))
                            self.filemenu_commited.tk_popup(event.x_root, event.y_root, 0)
                        elif status == "AM" or status == "MM": #staged and modified
                            self.filemenu_staged.delete(0, tk.END)
                            self.filemenu_staged.add_command(label='<staged> and <modified>')
                            self.filemenu_staged.add_separator()
                            self.filemenu_staged.add_command(label="go to stage", command=lambda: self.show_popup_staged_modified(element, "go to stage"))
                            self.filemenu_staged.add_command(label="undo", command=lambda: self.show_popup_staged_modified(element, "undo"))
                            self.filemenu_staged.add_command(label="unstage", command=lambda: self.show_popup_staged_modified(element , "unstage"))
                            self.filemenu_staged.tk_popup(event.x_root, event.y_root, 0)
                        elif status == " M": #modified
                            self.filemenu_modified.delete(0, tk.END)
                            self.filemenu_modified.add_command(label='<modified>')
                            self.filemenu_modified.add_separator()
                            self.filemenu_modified.add_command(label="go to stage", command=lambda: self.show_popup_modified(element, "go to stage"))
                            self.filemenu_modified.add_command(label="undo", command=lambda: self.show_popup_modified(element, "undo"))
                            self.filemenu_modified.tk_popup(event.x_root, event.y_root, 0)
                        elif status == "A" or "M": #staged
                            self.filemenu_staged.delete(0, tk.END)
                            self.filemenu_staged.add_command(label='<staged>')
                            self.filemenu_staged.add_separator()
                            self.filemenu_staged.add_command(label="unstage", command=lambda: self.show_popup_staged(element))
                            self.filemenu_staged.tk_popup(event.x_root, event.y_root, 0)
                        
        
###show_popup_###

    def show_popup_create(self, path): #label="Create git repo"
        result = messagebox.askyesno("Confirmation", "정말 진행하시겠습니까?")
        if result:
            self.git_init(path)

    def show_popup_untracked(self, path): 
        result = messagebox.askyesno("Confirmation", "정말 진행하시겠습니까?")
        if result:
            folder_path = os.path.dirname(path)
            self.git_add(path, folder_path)

    def show_popup_commited(self, path, label): 
        
        result = messagebox.askyesno("Confirmation", "정말 진행하시겠습니까?")
        if result:
            folder_path = os.path.dirname(path)
            if label == "untrack":
                self.git_rm_cached(path, folder_path)
            elif label == "delete":
                self.git_rm(path, folder_path)
            elif label == "rename":
                new_name = simpledialog.askstring("Rename", "Enter new name")
                self.git_mv(path, folder_path, new_name)
            

    def show_popup_modified(self, path, label): 
        
        result = messagebox.askyesno("Confirmation", "정말 진행하시겠습니까?")
        if result:
            folder_path = os.path.dirname(path)
            if label == "go to stage":
                self.git_add(path, folder_path)
            elif label == "undo":
                self.git_restore(path, folder_path)
            
            

    def show_popup_staged(self, path):
        
        result = messagebox.askyesno("Confirmation", "정말 진행하시겠습니까?")
        if result:
            folder_path = os.path.dirname(path)
            self.git_restore_staged(path, folder_path)


    def show_popup_staged_modified(self, path, label):
        
        result = messagebox.askyesno("Confirmation", "정말 진행하시겠습니까?")
        if result:
            folder_path = os.path.dirname(path)
            if label == "go to stage":
                self.git_add(path, folder_path)
            elif label == "undo":
                self.git_restore(path, folder_path)
            elif label == "unstage":
                self.git_restore_staged(path, folder_path)


    ###commit history 창 생성###

    def open_commit_history(self):
        # Commit History 가져오기
        path_strings = [button['text'] for button in self.path_bar_buttons]
        path_list = []
        for path in path_strings:
            # 첫번째 항목의 마지막 글자를 삭제
            if path == path_strings[0]:
                path = path[:-1]
            path_list.append(path)
        path = "\\".join(path_list)
        commit_history = self.git_commit_history(path)
        if commit_history is None:
            return

        def show_status(commit, mylist):
            status_window = tk.Toplevel(self)
            status_window.geometry("400x100")
            status_text = f"commit_hash: {mylist['commit_hash']}\n"
            status_text += f"author_name: {mylist['author_name']}\n"
            status_text += f"commit_date: {mylist['commit_date']}\n"
            status_text += f"commit_message: {mylist['commit_message']}"
            status_label = tk.Label(status_window, text=status_text)
            status_label.pack()

        def node_clicked(event, commit):
            mylist = self.commit_object_detail(path, commit['hash'])
            print(mylist)
            show_status(commit, mylist)

        new_window = tk.Toplevel(self)  # 새로운 창 생성
        new_window.geometry("400x500")

        canvas = tk.Canvas(new_window)
        scrollbar_y = tk.Scrollbar(new_window, command=canvas.yview)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(yscrollcommand=scrollbar_y.set)

        scrollbar_x = tk.Scrollbar(new_window, command=canvas.xview, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.configure(xscrollcommand=scrollbar_x.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 노드 그리기
        node_radius = 10
        text_offset = 20  # 텍스트의 오른쪽으로의 오프셋
        node_positions = [(50, 50 + i * 50) for i in range(len(commit_history))]
        nodes = []
        for position, commit in zip(node_positions, commit_history):
            node = canvas.create_oval(position[0] - node_radius, position[1] - node_radius, position[0] + node_radius,
                                    position[1] + node_radius, fill="red", tags="node")
            nodes.append(node)
            canvas.create_text(position[0] + node_radius + text_offset, position[1], anchor=tk.W,
                            text=f"{commit['author']}: {commit['message']}")
            canvas.tag_bind(node, "<Button-1>", lambda event, commit=commit: node_clicked(event, commit))

        # 선 그리기
        for i in range(len(nodes) - 1):
            x1, y1 = canvas.coords(nodes[i])[0] + node_radius, canvas.coords(nodes[i])[1] + node_radius
            x2, y2 = canvas.coords(nodes[i + 1])[0] + node_radius, canvas.coords(nodes[i + 1])[1] + node_radius
            canvas.create_line(x1, y1, x2, y2, tags=("line", f"line{i}"))

        def update_scrollregion(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", update_scrollregion)
        canvas.config(scrollregion=canvas.bbox("all"))
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # 노드에 대한 선 숨기기
        for i in range(len(nodes) - 1):
            canvas.tag_lower(f"line{i}", "node")

        new_window.mainloop()


    def clear_entry(self, event):
        pass
    
    def show_entry(self, event):
        pass

    