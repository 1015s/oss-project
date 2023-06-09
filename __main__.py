# -*- coding: utf-8 -*-
'''
tkfilebrowser - Alternative to filedialog for Tkinter
Copyright 2017 Juliette Monsel <j_4321@protonmail.com>

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


Example
'''


from functions import askopendirname, askopenfilenames, asksaveasfilename

try:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import filedialog
except ImportError:
    import tk
    #import ttk
    from tkinter import filedialog as filedialog



root = tk.Tk()
root.title("oss-project GUI git repository")
style = ttk.Style(root)
style.theme_use("clam")
root.geometry("300x200")
root.resizable(False, False)


def c_open_file_old():
    rep = filedialog.askopenfilenames(parent=root, initialdir='/', initialfile='tmp',
                                      filetypes=[("PNG", "*.png"),
                                                 ("JPEG", "*.jpg"),
                                                 ("All files", "*")])
    print(rep)


def c_open_dir_old():
    rep = filedialog.askdirectory(parent=root, initialdir='/tmp')
    print(rep)


def c_save_old():
    rep = filedialog.asksaveasfilename(parent=root, defaultextension=".png",
                                       initialdir='/tmp', initialfile='image.png',
                                       filetypes=[("PNG", "*.png"),
                                                  ("JPEG", "*.jpg"),
                                                  ("Text files", "*.txt"),
                                                  ("All files", "*")])
    print(rep)


def c_open_file():
    rep = askopenfilenames(parent=root, initialdir='/', initialfile='tmp',
                           filetypes=[
                                      ("All files", "*")])
    print(rep)


def c_open_dir():
    rep = askopendirname(parent=root, initialdir='/', initialfile='tmp')
    print(rep)


def c_save():
    rep = asksaveasfilename(parent=root, defaultext=".png", initialdir='/tmp', initialfile='image.png',
                            filetypes=[("Pictures", "*.png|*.jpg|*.JPG"),
                                       ("Text files", "*.txt"),
                                       ("All files", "*")])
    print(rep)

oss_label = tk.Label(root, text="oss-project", font=("Helvetica", 8))
oss_label.place(relx=0.25, rely=0.05, anchor="ne")

repo_label = tk.Label(root, text="GUI git repository", font=("Helvetica", 20,"bold"))
repo_label.place(relx=0.5, rely=0.35, anchor="center")

open_button = ttk.Button(root, text="start", command=c_open_file)
open_button.place(relx=0.5, rely=0.65, anchor="center")
close_button = ttk.Button(root, text="end", command=root.destroy)
close_button.place(relx=0.5, rely=0.85, anchor="center")
root.mainloop()
