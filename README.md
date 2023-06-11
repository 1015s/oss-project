# FileBrowser with Git

GUI file browser and git usage tool written in python using tkinter.<br>
_It was created by expanding https://github.com/j4321/tkFileBrowser.git_


<br>

## Purpose
```
Filebrowser has extended Git to work together. 
Git has been made easy to use through the GUI.
```

<br>

## Requirements
- Windows11
- python 3.x

And you need python packages.<br>
They can be installed at once through requirements.txt.
- Babel
- Pillow
- psutil
- pywin32
- tk

<br>

## Installation

1. Git clone this repository
> git clone https://github.com/1015s/oss-project.git
2. Creating a Virtual Environment
> python -m venv venv
3. Running a Virtual Environment
> source venv/Scripts/activate
4. Installing the required
> pip install -r requirements.txt
5. Run main
> python \__main__.py

<br>

## How to use

Click the start button on the Welcome page

<br>

### Git repository creation

1. Select the file you want to create as a git repository
2. Right-click
3. To select a create git repository

<br>

### Version Controlling

<br>

**Version Controlling except commit**
1. Select the file you want
2. Right click
3. Select the desired action 
4. Click OK when the confirmation window appears

<br>

**Committing staged changes**
1. Select the top-level folder associated with the git repository
2. Click on the mouse wheel
3. You will be able to see a list of files in the Staged state. <br>Click the file you want
4. Enter a commit message
5. Click the commit button


<br>

### Show status

1. Select the file you want
2. Right click
3. You can see the status of the file at the top of the menu

<br>

### Branch management

1. Open the top-level folder associated with the git repository
2. Click "Branch" button
3. You will be able to see new window named "Branch Menu"

<br>

**Create Branch**
1. Click "Create Branch" button in Branch Menu window
2. Enter new branch name
3. Click the OK button  

<br>

**Delete Branch**
1. Click "Delete Branch" button in Branch Menu window
2. You will be able to see a list of branches except for the current branch. <br>Click the branch you want to delete
3. When the confirmation message window appears, click the Y button  

<br>

**Rename Branch**
1. Click "Rename Branch" button in Branch Menu window
2. You will be able to see a list of branches. <br>Click the branch you want to rename
3. When the confirmation message window appears, click the Y button
4. Enter new name
5. Click the OK button 

<br>

**Checkout Branch**
1. Click "Checkout Branch" button in Branch Menu window
2. You will be able to see a list of branches except for the current branch. <br>Click the branch you want to checkout
3. When the confirmation message window appears, click the Y button  

<br>

**Merge Branch**
1. Click "Merge Branch" button in Branch Menu window
2. You will be able to see a list of branches except for the current branch. <br>Click the branch you want to merge with current branch
3. When the confirmation message window appears, click the Y button  

<br>

**Checking current Branch**
1. Click "Current Branch" button in Branch Menu window
2. You will be able to see current branch in message window  



<br>

### Git clone from GitHub

<br>

**Git clone from Private Github repository**
1. Open the top-level folder NOT associated with the git repository
2. Click "Clone" button
3. You will be able to see confirmation message window which asks if it's private or not.<br>Click Y button
4. Enter github repository's url to clone
5. Enter github repository's access token  

<br>

**Git clone from Public Github repository**
1. Open the top-level folder NOT associated with the git repository
2. Click "Clone" button
3. You will be able to see confirmation message window which asks if it's private or not.<br>Click N button  
4. Enter github repository's url to clone


<br>




## License

Under GPL-3.0 license
