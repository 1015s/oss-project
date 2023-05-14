import tkinter as tk
import subprocess
from tkinter import ttk
import os
from tkinter import messagebox
fol_str =""
file_str=""
com_message=""
file_name=""
class StageList: #stage에 올라간 파일 list를 보여주는 gui
    def clear_entry(self):
        global com_message
        if self.entry.get() == "커밋 메세지 입력":
            self.entry.delete(0, tk.END)
            
    def show_entry(self):
        global com_message
        if not self.entry.get():
            self.entry.insert(0, "커밋 메세지 입력")
        else:
            user_input = self.entry.get()
            com_message=user_input
        return com_message
    def __init__(self, parent):
        self.parent = parent
        self.toplevel = parent
        self.listbox = tk.Listbox(self.toplevel)
        self.listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.listbox.bind("<<ListboxSelect>>", lambda event: self.select_file(event))
        self.entry = tk.Entry(self.toplevel)
        self.entry.insert(0, "커밋 메세지 입력")
        self.entry.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.BOTH)
        
        
           
        self.button = tk.Button(self.toplevel, text="commit",command=self.final_commit)
        self.button.pack(side=tk.RIGHT, padx=5, pady=5)     
        
        
    def listpane(self,element):
        global fol_str
        fol_str=element
        cmd = ["git", "diff", "--cached", "--name-only"]
        result = subprocess.run(cmd, cwd=element, capture_output=True, text=True)
        staged_files = result.stdout.strip().splitlines()
        for item in staged_files:
            self.listbox.insert(tk.END, item)

    def select_file(self,event):
        global file_str
        global file_name
        global fol_str
        folder_path=fol_str
        #global com_message
        selected_indices = self.listbox.curselection()
        selected_items = [self.listbox.get(i) for i in selected_indices]  
        
        # 파일이 위치한 폴더 경로
        if selected_items:
            file_name = selected_items[0]
            file_str = os.path.join(folder_path, file_name)
            
            

    def final_commit(self):
        global com_message, file_str,fol_str,file_name
        com_message = self.show_entry()  # 커밋 메시지 가져오기
        file_path = file_str  # 선택된 파일 경로 가져오기
        final_message=com_message
        if not com_message:
            messagebox.showwarning("알림", "커밋 메시지를 입력해주세요.")
            return

        if not file_str:
            messagebox.showwarning("경고", "파일을 선택해주세요.")
            return
        try:
            # git commit 실행
            cmd = ["git", "commit", "-m", final_message, "--", file_path]
            subprocess.run(cmd, check=True)
            print("Git commit successful.")
            self.toplevel.destroy()
            return True
        except subprocess.CalledProcessError as e:
            print(f"Git commit failed: {e}")
            return False
        
