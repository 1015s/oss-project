import tkinter as tk
import subprocess
from tkinter import ttk

stirng =""
class StageList: #stage에 올라간 파일 list를 보여주는 gui
    def clear_entry(self):
        if self.entry.get() == "커밋 메세지 입력":
            self.entry.delete(0, tk.END)
            
            
    def show_entry(self):
        if not self.entry.get():
            self.entry.insert(0, "커밋 메세지 입력")
        else:
            user_input = self.entry.get()
            return user_input
    def __init__(self, parent):
        self.parent = parent
        self.toplevel = parent
        self.listbox = tk.Listbox(self.toplevel)
        self.listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.entry = tk.Entry(self.toplevel)
        self.entry.insert(0, "커밋 메세지 입력")
        #self.entry.bind("<FocusIn>", self.clear_entry)
        #self.entry.bind("<FocusOut>", self.show_entry)
        self.entry.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.BOTH)
        print("메시지확인:"+StageList.show_entry(self))
        
           
        self.button = tk.Button(self.toplevel, text="commit",command=StageList.final_commit(StageList.show_entry(self),stirng))
        self.button.pack(side=tk.RIGHT, padx=5, pady=5)     
        
        
    def listpane(self,element):
        print("listpane에 들어옴")
        global stirng
        stirng=element
        print("stirng입니다:"+stirng)
        cmd = ["git", "diff", "--cached", "--name-only"]
        result = subprocess.run(cmd, cwd=element, capture_output=True, text=True)
        staged_files = result.stdout.strip().splitlines()
        for item in staged_files:
            self.listbox.insert(tk.END, item)
            
            
            


    def final_commit(commit_message,file_path):
        final_message=commit_message
        try:
            # git commit 실행
            cmd = ["git", "commit", "-m", final_message, "--", file_path]
            subprocess.run(cmd, check=True)
            print("Git commit successful.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Git commit failed: {e}")
            return False
root = tk.Tk()
stage_list = StageList(root)
#stage_list.show_entry()
#root.mainloop()       
        
        
'''
 class FilePage: #파일브라우저(가정)
    
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.button = ttk.Button(self.frame, text="commit", command=self.showStageList)
        self.button.pack(padx=10, pady=10)

    def showStageList(self): #stagelist 생성
        stageList = StageList(self.frame)


if __name__ == '__main__':
    root = tk.Tk()
    new = FilePage(root)
    root.mainloop()
    '''