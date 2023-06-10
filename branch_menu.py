import tkinter as tk
import subprocess
from tkinter import ttk
import os
from tkinter import messagebox
from tkinter import simpledialog
from filebrowser import * 

pathh=""

class BranchMenu:
    def __init__(self, parent):
        self.parent = parent
        self.toplevel = self.parent
        self.toplevel.title("Branch Menu")
        self.toplevel.geometry("300x200")
        '''
        self.parent = parent
        self.toplevel = tk.Toplevel(parent)
        self.toplevel.title("Branch Menu")
        self.toplevel.geometry("300x200")
        '''
        # 브랜치 생성 버튼
        self.create_button = ttk.Button(self.toplevel, text="브랜치 생성", command=self.creating_branch)
        self.create_button.pack(padx=10, pady=5)

        # 브랜치 삭제 버튼
        self.delete_button = ttk.Button(self.toplevel, text="브랜치 삭제", command=self.deleting_branch)
        self.delete_button.pack(padx=10, pady=5)

        # 브랜치 변경 버튼
        self.rename_button = ttk.Button(self.toplevel, text="브랜치 변경", command=self.renaming_branch)
        self.rename_button.pack(padx=10, pady=5)

        # 브랜치 체크아웃 버튼
        self.checkout_button = ttk.Button(self.toplevel, text="브랜치 체크아웃", command=self.checkouting_branch)
        self.checkout_button.pack(padx=10, pady=5)

        # 브랜치 병합 버튼
        self.merge_button = ttk.Button(self.toplevel, text="브랜치 병합", command=self.merging_branch)
        self.merge_button.pack(padx=10, pady=5)
        
        
        
        
        
    def connect_other_py(self,element):
        global pathh
        print("connect_other_py: "+element)
        pathh=element
        
        
    def creating_branch(self):
        branch_name = simpledialog.askstring("Create", "Enter new branch name")
        if branch_name:
            try:
                cmd = ["git", "branch", branch_name]
                subprocess.run(cmd, cwd=pathh)
                messagebox.showinfo("Branch Status", f"Branch '{branch_name}' created successfully.")
                return True
            except Exception as e:
                messagebox.showinfo("Branch Status", f"An error occurred: {e}")
                return False
        else:
            messagebox.showwarning("알림", "plz write new branch name")
            
    def deleting_branch(self):
        # 브랜치 삭제 로직 작성
        print("브랜치 삭제")

    def renaming_branch(self):
        # 브랜치 변경 로직 작성
        print("브랜치 이름변경")
        
    def checkouting_branch(self):
        # 브랜치 체크아웃 로직 작성
        print("브랜치 체크아웃")

    def merging_branch(self):
        # 브랜치 병합 로직 작성
        print("브랜치 병합")