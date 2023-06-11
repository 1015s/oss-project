import tkinter as tk
import subprocess
from tkinter import ttk
import os
from tkinter import messagebox
from tkinter import simpledialog
#from filebrowser import * 

pathh=""

class BranchMenu:
    def __init__(self, parent):
        self.parent = parent
        self.toplevel = self.parent
        self.toplevel.title("Branch Menu")
        self.toplevel.geometry("300x200")

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
        branches = self.get_other_branches(pathh)
        root=tk.Tk()
        def select_branch(event):
            selected_branch = listbox.get(listbox.curselection())
            response = messagebox.askquestion("Question", "이 브랜치로 바꾸겠습니까?")
            if response == 'yes':
                print("User chose yes")
                self.branch_checkout(pathh,selected_branch)
                window.withdraw()
            elif response == 'no':
                print("User chose no")
                window.withdraw()            
            #print(selected_branch)
        # 새 창 생성
        window = tk.Toplevel(root)
        root.withdraw()
        # 목록 위젯 생성
        listbox = tk.Listbox(window)
        listbox.pack()
        # 브랜치 목록 추가
        for branch in branches:
            listbox.insert(tk.END, branch)
        # 브랜치 선택 이벤트 핸들러 연결
        listbox.bind('<<ListboxSelect>>', select_branch)

        

    def merging_branch(self):
        # 브랜치 병합 로직 작성
        print("브랜치 병합")
    
           
    def showing_branch(self,pathh):
        current_branch = self.current_branch(pathh)
        branches = self.branch_list(pathh)
        other_branches = [branch for branch in branches if branch != current_branch]
        branches = ['branch1', 'branch2', 'branch3']
        root=tk.Tk()
        def select_branch(event):
            selected_branch = listbox.get(listbox.curselection())
            print(selected_branch)

        # 새 창 생성
        window = tk.Toplevel(root)
        root.withdraw()
        # 목록 위젯 생성
        listbox = tk.Listbox(window)
        listbox.pack()
        
        # 브랜치 목록 추가
        for branch in branches:
            listbox.insert(tk.END, branch)

        # 브랜치 선택 이벤트 핸들러 연결
        listbox.bind('<<ListboxSelect>>', select_branch)

    #root = tk.Tk()

        '''
        listbox=tk.Listbox(window)
        branches = ['branch1', 'branch2', 'branch3'] 
        for branch in branches:
            listbox.insert(tk.END, branch)
        selected_branch = listbox.get(listbox.curselection())
        print(selected_branch)
        window = tk.Toplevel(listbox)
    # 목록 위젯 생성
    #listbox = tk.Listbox(window)
    #listbox.pack()
    # 브랜치 목록 추가
    #for branch in branches:
        #listbox.insert(tk.END, branch)
    # 브랜치 선택 이벤트 핸들러 연결
    #listbox.bind('<<ListboxSelect>>', select_branch)
    
    '''
    def check_git_managed(self, path):
        git_dir = os.path.join(path, ".git")
        if os.path.exists(git_dir) and os.path.isdir(git_dir):
            return True
        return False

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
            result = subprocess.check_output(cmd, cwd=folder_path, universal_newlines=True, encoding='utf-8')
            #result = subprocess.check_output(cmd, cwd=folder_path, universal_newlines=True)
            branches = [branch.strip() for branch in result.splitlines()]
            return branches
    
    # input : folder_path -> output : current branch 제외한 나머지 branch list 반환
    def get_other_branches(self, folder_path):
        current_branch = self.current_branch(folder_path)
        branches = self.branch_list(folder_path)
        modified_branch_list = [branch.replace(" ", "").replace("*", "") for branch in branches]
        other_branches = [branch for branch in modified_branch_list if branch != current_branch]
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