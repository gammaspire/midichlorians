import sys

import tkinter as tk
import os

from tkinter import messagebox
import glob

from generate_app import MainPage

homedir = os.getenv('HOME')

#create main window container, into which the first page will be placed.
class App(tk.Tk):
    
    def __init__(self, path_to_repos, initial_browsedir, soundfont, window_geometry, path_to_ffmpeg):          #INITIALIZE; will always run when App class is called.
        tk.Tk.__init__(self)     #initialize tkinter; *args are parameter arguments, **kwargs can be dictionary arguments
        
        self.title('MIDI-chlorians: Sonification of Nearby Galaxies')
        self.geometry(window_geometry)
        self.resizable(True,True)
        self.rowspan=10
        
        #will be filled with heaps of frames and frames of heaps. 
        container = tk.Frame(self)
        container.pack(side='top', fill='both', expand=True)     #fills entire container space
        container.grid_rowconfigure(0,weight=1)
        container.grid_columnconfigure(0,weight=1)

        ## Initialize Frames
        self.frames = {}     #empty dictionary
        frame = MainPage(container, self, path_to_repos, initial_browsedir, soundfont, path_to_ffmpeg)   #define frame  
        self.frames[MainPage] = frame     #assign new dictionary entry {MainPage: frame}
        frame.grid(row=0,column=0,sticky='nsew')   #define where to place frame within the container...CENTER!
        for i in range(self.rowspan):
            frame.columnconfigure(i, weight=1)
            frame.rowconfigure(i, weight=1)
        
        self.show_frame(MainPage)  #a method to be defined below (see MainPage class)
        self.create_menubar()      #FOR MAC USERS: WILL APPEAR ON THE *MAC MENUBAR*, NOT THE TK WINDOW.
    
    def create_menubar(self):
        
        self.menu = tk.Menu(self)

        self.filemenu = tk.Menu(self.menu, tearoff=0)
        self.filemenu.add_command(label='Load FITS file', command=self.popup_loadfits)
        self.filemenu.add_command(label='Sonification Features', command=self.popup_sonifeat)
        self.filemenu.add_command(label='Defining a Region', command=self.popup_rectline)
        self.filemenu.add_command(label='Save .wav', command=self.popup_wav)
        self.filemenu.add_command(label='Save .mp4', command=self.popup_mp4)
        self.filemenu.add_separator()
        self.filemenu.add_command(label='Exit Program', command=self.quit)
        self.menu.add_cascade(label='Help',menu=self.filemenu)
        
        self.config(menu=self.menu)
    
    #once I record a proper video, I might also link the youtube address to each textboxes. and rather than type all text content here, I'll just create a few .txt files in the folder.
    def popup_loadfits(self):
        self.textbox1 = open(path_to_repos+'readme_files/loadfits.txt','r').reaed()
        messagebox.showinfo('How to Load a FITS File',self.textbox1)
    
    def popup_sonifeat(self):
        self.textbox2 = open(path_to_repos+'readme_files/sonifeat.txt','r').read()
        messagebox.showinfo('Sonification Features',self.textbox2)
    
    def popup_rectline(self):
        self.textbox3 = open(path_to_repos+'readme_files/rectline.txt').read()
        messagebox.showinfo('Constraining Sonification Area',self.textbox3)
    
    def popup_wav(self):
        self.textbox4 = open(path_to_repos+'readme_files/howtowav.txt').read()
        messagebox.showinfo('Save Sound as WAV File',self.textbox4)
    
    def popup_mp4(self):
        self.textbox5 = open(path_to_repos+'readme_files/howtomp4.txt').read()
        messagebox.showinfo('Save Sound (with Animation!) as MP4 File',self.textbox5)
    
    def show_frame(self, cont):     #'cont' represents the controller, enables switching between frames/windows...I think.
        frame = self.frames[cont]
        frame.tkraise()   #will raise window/frame to the 'front;' if there is more than one frame, quite handy.
        
if __name__ == "__main__":
        
    if '-h' in sys.argv or '--help' in sys.argv:
        print("Usage: %s [-params (name of parameter.txt file, no single or double quotation marks)]")
        sys.exit(1)
        
    if '-params' in sys.argv:
        p = sys.argv.index('-params')
        param_file = str(sys.argv[p+1])
    
    #create dictionary with keyword and values from param textfile...
    param_dict = {}
    with open(param_file) as f:
        for line in f:
            try:
                key = line.split()[0]
                val = line.split()[1]
                param_dict[key] = val
            except:
                continue

    #now...extract parameters and assign to relevantly-named variables
    path_to_ffmpeg = param_dict['path_to_ffmpeg']
    path_to_repos = param_dict['path_to_repos']
    initial_browsedir = param_dict['initial_browsedir']
    soundfont = param_dict['soundfont']
    window_geometry = param_dict['window_geometry']
        
    app = App(path_to_repos, initial_browsedir, soundfont, window_geometry, path_to_ffmpeg)
    app.mainloop()