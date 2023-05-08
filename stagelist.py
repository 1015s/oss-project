import tkinter as tk
from tkinter import ttk


class StageList: #stage에 올라간 파일 list를 보여주는 gui
    def __init__(self, parent):
        self.parent = parent
        self.toplevel = tk.Toplevel(parent)
        
        self.listbox = tk.Listbox(self.toplevel)
        self.listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.listbox.insert(tk.END, "apple")
        self.listbox.insert(tk.END, "banana")


        self.entry = tk.Entry(self.toplevel)
        self.entry.insert(0, "커밋 메세지 입력")
        self.entry.bind("<FocusIn>", self.clear_entry)
        self.entry.bind("<FocusOut>", self.show_entry)
        self.entry.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.BOTH)

        self.button = tk.Button(self.toplevel, text="commit")
        self.button.pack(side=tk.LEFT, padx=5, pady=5)

    def clear_entry(self, event):
        if self.entry.get() == "커밋 메세지 입력":
            self.entry.delete(0, tk.END)
    
    def show_entry(self, event):
        if not self.entry.get():
            self.entry.insert(0, "커밋 메세지 입력")

        


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