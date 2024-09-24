'''
Class layout adapted from 
https://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter/7557028#7557028
'''

import sys

import ffmpeg
from midi2audio import FluidSynth
from midiutil import MIDIFile
from audiolazy import str2midi
from pygame import mixer                    #this library is what causes the loading delay methinks

import tkinter as tk
import numpy as np
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation

from matplotlib import figure              #see self.fig, self.ax.

import matplotlib                          #I need this for matplotlib.use. sowwee.
matplotlib.use('TkAgg')                    #strange error messages will appear otherwise.

from scipy.stats import scoreatpercentile
from scipy import spatial
from astropy.visualization import simple_norm
from astropy.io import fits
from reproject import reproject_interp
from tkinter import font as tkFont
from tkinter import messagebox
from tkinter import filedialog
import glob

from io import BytesIO
from mido import MidiFile

homedir = os.getenv('HOME')

#create main window container, into which the first page will be placed.
class App(tk.Tk):
    
    def __init__(self, path_to_repos, initial_browsedir, soundfont, window_geometry):          #INITIALIZE; will always run when App class is called.
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
        frame = MainPage(container, self, path_to_repos, initial_browsedir, soundfont)   #define frame  
        self.frames[MainPage] = frame     #assign new dictionary entry {MainPage: frame}
        frame.grid(row=0,column=0,sticky='nsew')   #define where to place frame within the container...CENTER!
        for i in range(self.rowspan):
            frame.columnconfigure(i, weight=1)
            frame.rowconfigure(i, weight=1)
        
        self.show_frame(MainPage)  #a method to be defined below (see MainPage class)
    
    def show_frame(self, cont):     #'cont' represents the controller, enables switching between frames/windows...I think.
        frame = self.frames[cont]
        frame.tkraise()   #will raise window/frame to the 'front;' if there is more than one frame, quite handy.
        
        
#inherits all from tk.Frame; will be on first window
class MainPage(tk.Frame):    
    
    def __init__(self, parent, controller, path_to_repos, initial_browsedir, soundfont):
        
        #generalized parameters given in params.txt file
        self.path_to_repos = path_to_repos
        self.initial_browsedir = initial_browsedir
        self.soundfont = soundfont
        
        #these variables will apply to the self.drawSq function, if the user desires to use it.
        self.bound_check=None
        self.x1=None
        self.x2=None
        self.y1=None
        self.y2=None
        self.angle=0
        
        #initiate a counter to ensure that files do not overwrite one another for an individual galaxy
        #note: NEEDED FOR THE SAVE WIDGET
        self.namecounter=0
        self.namecounter_ani=0
        self.namecounter_ani_both=0
                
        #dictionary for different key signatures
        
        self.note_dict = {
           'C Major': 'C2-D2-E2-F2-G2-A2-B2-C3-D3-E3-F3-G3-A3-B3-C4-D4-E4-F4-G4-A4-B4-C5-D5-E5-F5-G5-A5-B5',
           'G Major': 'G1-A1-B1-C2-D2-E2-F#2-G2-A2-B2-C3-D3-E3-F#3-G3-A3-B3-C4-D4-E4-F#4-G4-A4-B4-C5-D5-E5-F#5',
           'D Major': 'D2-E2-F#2-G2-A2-B2-C#3-D3-E3-F#3-G3-A3-B3-C#4-D4-E4-F#4-G4-A4-B4-C#5-D5-E5-F#5-G5-A5-B5-C#6',
           'A Major': 'A1-B1-C#2-D2-E2-F#2-G#2-A2-B2-C#3-D3-E3-F#3-G#3-A3-B3-C#4-D4-E4-F#4-G#4-A4-B4-C#5-D5-E5-F#5-G#5',
           'E Major': 'E2-F#2-G#2-A2-B2-C#3-D#3-E3-F#3-G#3-A3-B3-C#4-D#4-E4-F#4-G#4-A4-B4-C#5-D#5-E5-F#5-G#5-A5-B5-C#6-D#6',
           'B Major': 'B1-C#2-D#2-E2-F#2-G#2-A#2-B3-C#3-D#3-E3-F#3-G#3-A#3-B4-C#4-D#4-E4-F#4-G#4-A#4-B5-C#5-D#5-E5-F#5-G#5-A#5',
           'F# Major': 'F#2-G#2-A#2-B2-C#3-D#3-E#3-F#3-G#3-A#3-B3-C#4-D#4-E#4-F#4-G#4-A#4-B4-C#5-D#5-E#5-F#5-G#5-A#5-B5-C#6-D#6-E#6', 
           'Gb Major': 'Gb1-Ab1-Bb1-Cb2-Db2-Eb2-F2-Gb2-Ab2-Bb2-Cb3-Db3-Eb3-F3-Gb3-Ab3-Bb3-Cb4-Db4-Eb4-F4-Gb4-Ab4-Bb4-Cb5-Db5-Eb5-F5',
           'Db Major': 'Db2-Eb2-F2-Gb2-Ab2-Bb2-C3-Db3-Eb3-F3-Gb3-Ab3-Bb3-C4-Db4-Eb4-F4-Gb4-Ab4-Bb4-C5-Db5-Eb5-F5-Gb5-Ab5-Bb5-C6',
           'Ab Major': 'Ab1-Bb1-C2-Db2-Eb2-F2-G2-Ab2-Bb2-C3-Db3-Eb3-F3-G3-Ab3-Bb3-C4-Db4-Eb4-F4-G4-Ab4-Bb4-C5-Db5-Eb5-F5-G5', 
           'Eb Major': 'Eb2-F2-G2-Ab2-Bb2-C3-D3-Eb3-F3-G3-Ab3-Bb3-C4-D4-Eb4-F4-G4-Ab4-Bb4-C5-D5-Eb5-F5-G5-Ab5-Bb5-C6-D6',
           'Bb Major': 'Bb1-C2-D2-Eb2-F2-G2-A2-Bb2-C3-D3-Eb3-F3-G3-A3-Bb3-C4-D4-Eb4-F4-G4-A4-Bb4-C5-D5-Eb5-F5-G5-A5',
           'F Major': 'F2-G2-A2-Bb2-C3-D3-E3-F3-G3-A3-Bb3-C4-D4-E4-F4-G4-A4-Bb4-C5-D5-E5-F5-G5-A5-Bb5-C6-D6-E6', 
        }
        
        #isolate the key signature names --> need for the dropdown menu
        self.keyvar_options=list(self.note_dict.keys())

        self.keyvar = tk.StringVar()
        self.keyvar.set(self.keyvar_options[2])
        
        #defines the number of rows/columns to resize when resizing the entire window.
        self.rowspan=10
        
        #define a font
        self.helv20 = tkFont.Font(family='Helvetica', size=20, weight='bold')
        
        #first frame...
        tk.Frame.__init__(self,parent)
        
        #NOTE: columnconfigure and rowconfigure below enable the minimization and maximization of window to also affect widget size
        
        #create frame for save widgets...y'know, to generate the .wav and .mp4 
        self.frame_save=tk.LabelFrame(self,text='Save Files',padx=5,pady=5)
        self.frame_save.grid(row=4,column=1,columnspan=5)
        for i in range(self.rowspan):
            self.frame_save.columnconfigure(i,weight=1)
            self.frame_save.rowconfigure(i,weight=1)
        
        #create display frame, which will hold the canvas and a few button widgets underneath.
        self.frame_display=tk.LabelFrame(self,text='Display',font='Vendana 15',padx=5,pady=5)
        self.frame_display.grid(row=0,column=0,rowspan=9)
        for i in range(self.rowspan):
            self.frame_display.columnconfigure(i, weight=1)
            self.frame_display.rowconfigure(i, weight=1)
        
        #create buttons frame, which currently only holds the 'save' button, 'browse' button, and entry box.
        self.frame_buttons=tk.LabelFrame(self,text='File Browser',padx=5,pady=5)
        self.frame_buttons.grid(row=0,column=1,columnspan=2)
        for i in range(self.rowspan):
            self.frame_buttons.columnconfigure(i, weight=1)
            self.frame_buttons.rowconfigure(i, weight=1)
            
        #create soni frame, which holds the event button for converting data into sound (midifile).
        #there are also heaps of text boxes with which the user can manipulate the sound conversion parameters
        self.frame_soni=tk.LabelFrame(self,text='Parameters (Click "Sonify" to play)',padx=5,pady=5)
        self.frame_soni.grid(row=7,column=2,rowspan=2,sticky='se')
        for i in range(self.rowspan):
            self.frame_soni.columnconfigure(i, weight=1)
            self.frame_soni.rowconfigure(i, weight=1)
        
        #create editcanvas frame --> manipulates vmin, vmax, cmap of the display image
        self.frame_editcanvas = tk.LabelFrame(self,text='Change Display',padx=5,pady=5)
        self.frame_editcanvas.grid(row=7,column=1,sticky='s')
        for i in range(self.rowspan):
            self.frame_editcanvas.columnconfigure(i, weight=1)
            self.frame_editcanvas.columnconfigure(i, weight=1)
            
        #create box frame --> check boxes for lines vs. squares when interacting with the figure canvas
        self.frame_box = tk.LabelFrame(self,text='Change Rectangle Angle',padx=5,pady=5)
        self.frame_box.grid(row=8,column=1,sticky='s')
        for i in range(self.rowspan):
            self.frame_box.columnconfigure(i, weight=1)
            self.frame_box.rowconfigure(i, weight=1)
        
        self.galaxy_to_display()
        '''
        INSERT INITIATION FUNCTIONS TO RUN BELOW.
        '''
        self.initiate_vals()
        self.add_info_button()
        self.populate_soni_widget()
        self.populate_box_widget()
        self.populate_save_widget()
        self.init_display_size()
        self.populate_editcanvas_widget()
    
    def populate_box_widget(self):
        self.angle_box = tk.Entry(self.frame_box, width=15, borderwidth=2, bg='black', fg='lime green',
                                  font='Arial 20')
        self.angle_box.insert(0,'Rotation angle (deg)')
        self.angle_box.grid(row=0,column=0,columnspan=5)
        self.add_angle_buttons()
    
    def initiate_vals(self):
        self.var = tk.IntVar()
        self.val = tk.Label(self.frame_display,text='Mean Pixel Value: ',font='Arial 18')
        self.val.grid(row=8,column=2,padx=1,pady=(3,1),sticky='e')
        self.line_check = tk.Checkbutton(self.frame_display,text='Switch to Lines',
                                         onvalue=1,offvalue=0,command=self.change_canvas_event,
                                         variable=self.var,font='Arial 18')
        self.line_check.grid(row=9,column=2,padx=1,pady=(3,1),sticky='e')
    
    def galaxy_to_display(self):
        self.path_to_im = tk.Entry(self.frame_buttons, width=35, borderwidth=2, bg='black', fg='lime green', 
                                   font='Arial 20')
        self.path_to_im.insert(0,'Type path/to/image.fits or click "Browse"')
        self.path_to_im.grid(row=0,column=0,columnspan=2)
        self.add_browse_button()
        self.add_enter_button()
    
    def populate_editcanvas_widget(self,min_v=0, max_v=1, min_px=0, max_px=1):
        
        self.v1slider = tk.Scale(self.frame_editcanvas, from_=min_px, to=max_px, orient=tk.HORIZONTAL,
                                command=self.change_vvalues)
        self.v2slider = tk.Scale(self.frame_editcanvas, from_=min_px, to=max_px, orient=tk.HORIZONTAL,
                                command=self.change_vvalues)
        
        v1lab = tk.Label(self.frame_editcanvas,text='vmin').grid(row=0,column=0)
        v2lab = tk.Label(self.frame_editcanvas,text='vmax').grid(row=1,column=0)
        
        self.v1slider.grid(row=0,column=1)
        self.v2slider.grid(row=1,column=1)
        
        self.cmap_options = ['viridis', 'rainbow', 'plasma', 'spring', 
                             'Wistia', 'cool', 'gist_heat', 'winter', 
                             'Purples', 'Greens', 'Oranges', 'gray']
        
        #set up cmap dropdown menu
        self.cmapvar = tk.StringVar()
        self.cmapvar.set(self.cmap_options[0])
        
        self.cmap_menu = tk.OptionMenu(self.frame_editcanvas, self.cmapvar, *self.cmap_options, command=self.change_cmap)
        self.cmap_menu.config(font='Arial 15',padx=5,pady=5) 
        
        cmaplab = tk.Label(self.frame_editcanvas,text='cmap').grid(row=2,column=0)
        
        self.cmap_menu.grid(row=2,column=1)
        
        self.cmaprev = tk.IntVar()
        self.reverse_cmap = tk.Checkbutton(self.frame_editcanvas,text='Invert Colorbar', onvalue=1, offvalue=0, 
                                           variable = self.cmaprev, font='Arial 15', command=self.reverse_cmap)
        self.reverse_cmap.grid(row=3,column=0,columnspan=2)
        
    
    def change_vvalues(self, value):
        min_val = float(self.v1slider.get())
        max_val = float(self.v2slider.get())
        self.im.norm.autoscale([min_val, max_val])  #change vmin, vmax of self.im
        #self.im.set_clim(vmin=min_val, vmax=max_val)   #another way of doing exactly what I typed above.
        self.canvas.draw()   
    
    #command to change color scheme of the image
    def change_cmap(self, value): 
        self.im.set_cmap(self.cmapvar.get())
        self.canvas.draw()
    
    #command to reverse the color schemes. for this version of matplotlib, reversal is as simple as appending _r 
    def reverse_cmap(self):
        if self.cmaprev.get()==1:
            colorb = self.cmapvar.get() + '_r'
        if self.cmaprev.get()==0:
            colorb = self.cmapvar.get()
        self.im.set_cmap(colorb)
        self.canvas.draw()
        
    def populate_save_widget(self):
        self.add_save_button()
        self.add_saveani_button()
        self.add_w1w3merge_box()
    
    def populate_soni_widget(self):
        
        self.add_midi_button()
        
        #create all entry textboxes (with labels and initial values), midi button!
   
        #this checkbox inverts the note assignment such that high values have low notes and low values have high notes.
        self.var_rev = tk.IntVar()
        self.rev_checkbox = tk.Checkbutton(self.frame_soni, text='Note Inversion', onvalue=1, offvalue=0, variable=self.var_rev, font='Arial 17')
        self.rev_checkbox.grid(row=0,column=0,columnspan=2)
        
        ylab = tk.Label(self.frame_soni,text='yscale').grid(row=1,column=0)
        self.y_scale_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green', 
                                      font='Arial 15')
        self.y_scale_entry.insert(0,'0.5')
        self.y_scale_entry.grid(row=1,column=1,columnspan=1)
        
        vmin_lab = tk.Label(self.frame_soni,text='Min Velocity').grid(row=2,column=0)
        self.vel_min_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green', 
                                      font='Arial 15')
        self.vel_min_entry.insert(0,'10')
        self.vel_min_entry.grid(row=2,column=1,columnspan=1)
        
        vmax_lab = tk.Label(self.frame_soni,text='Max Velocity').grid(row=3,column=0)
        self.vel_max_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green', 
                                      font='Arial 15')
        self.vel_max_entry.insert(0,'100')
        self.vel_max_entry.grid(row=3,column=1,columnspan=1)
        
        bpm_lab = tk.Label(self.frame_soni,text='BPM').grid(row=4,column=0)
        self.bpm_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green', 
                                  font='Arial 15')
        self.bpm_entry.insert(0,'35')
        self.bpm_entry.grid(row=4,column=1,columnspan=1)
        
        xminmax_lab = tk.Label(self.frame_soni,text='xmin, xmax').grid(row=5,column=0)
        self.xminmax_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green',
                                      font='Arial 15')
        self.xminmax_entry.insert(0,'x1, x2')
        self.xminmax_entry.grid(row=5,column=1,columnspan=1)
        
        key_lab = tk.Label(self.frame_soni,text='Key Signature').grid(row=6,column=0)
        self.key_menu = tk.OptionMenu(self.frame_soni, self.keyvar, *self.keyvar_options)
        self.key_menu.config(bg='black',fg='black',font='Arial 15')
        self.key_menu.grid(row=6,column=1,columnspan=1)
        
        program_lab = tk.Label(self.frame_soni,text='Instrument (0-127)').grid(row=7,column=0)
        self.program_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green', 
                                      font='Arial 15')
        self.program_entry.insert(0,'0')
        self.program_entry.grid(row=7,column=1,columnspan=1)
        
        duration_lab = tk.Label(self.frame_soni,text='Duration (sec)').grid(row=8,column=0)
        self.duration_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green', 
                                       font='Arial 15')
        self.duration_entry.insert(0,'0.4')
        self.duration_entry.grid(row=8,column=1,columnspan=1)
    
    def init_display_size(self):
        #aim --> match display frame size with that once the canvas is added
        #the idea is for consistent aestheticsTM
        self.fig = figure.Figure(figsize=(5,5))
        self.fig.subplots_adjust(left=0.06, right=0.94, top=0.94, bottom=0.06)

        self.ax = self.fig.add_subplot()
        self.im = self.ax.imshow(np.zeros(100).reshape(10,10))
        self.ax.set_title('Click "Browse" to the right to begin!',fontsize=15)
        self.text = self.ax.text(x=2.2,y=4.8,s='Your Galaxy \n Goes Here',color='red',fontsize=25)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_display) 
        
        #activate the draw square/rectangle/quadrilateral/four-sided polygon event
        self.connect_event=self.canvas.mpl_connect('button_press_event',self.drawSqRec)
        
        #add canvas 'frame'
        self.label = self.canvas.get_tk_widget()
        self.label.grid(row=0,column=0,columnspan=3,rowspan=6,sticky='nsew')
    
    def add_info_button(self):
        self.info_button = tk.Button(self.frame_display, text='Galaxy FITS Info', padx=15, pady=10, font='Ariel 20', command=self.popup_info)
        self.info_button.grid(row=8,column=0,sticky='w',rowspan=2)
    
    def add_save_button(self):
        self.save_button = tk.Button(self.frame_save, text='Save as WAV', padx=15, pady=10, font='Ariel 20',
                                     command=self.save_sound)
        self.save_button.grid(row=0,column=0)
    
    def add_saveani_button(self):
        self.saveani_button = tk.Button(self.frame_save, text='Save as MP4', padx=15, pady=10, font='Ariel 20', command=self.create_midi_animation)
        self.saveani_button.grid(row=0,column=1)
    
    def add_w1w3merge_box(self):
        self.var_w1w3 = tk.IntVar()
        self.w1w3merge_box = tk.Checkbutton(self.frame_save, text='Create Overlay MP3 (W1 & W3 only)', 
                                            font='Ariel 20', onvalue=1, offvalue=0, variable=self.var_w1w3)
        self.w1w3merge_box.grid(row=1,column=0,sticky='nsew',columnspan=2)
    
    
    def add_browse_button(self):
        self.button_explore = tk.Button(self.frame_buttons ,text="Browse", padx=20, pady=10, font=self.helv20, command=self.browseFiles)
        self.button_explore.grid(row=1,column=0)
        
    def add_enter_button(self):
        self.path_button = tk.Button(self.frame_buttons, text='Enter/Refresh Canvas', padx=20, pady=10, font=self.helv20,command=self.initiate_canvas)
        self.path_button.grid(row=1,column=1)
    
    def add_midi_button(self):
        self.midi_button = tk.Button(self.frame_soni, text='Sonify', padx=20, pady=10, font=self.helv20, 
                                     command=self.midi_setup_bar)
        self.midi_button.grid(row=9,column=0,columnspan=2)
    
    def add_angle_buttons(self):
        self.angle_button = tk.Button(self.frame_box, text='Rotate',padx=5,pady=10,font=self.helv20,
                                      command=self.create_rectangle)
        self.angle_button.grid(row=2,column=1,columnspan=3)
        self.incarrow = tk.Button(self.frame_box, text='+1',padx=1,pady=10,font='Ariel 14',
                                  command=self.increment)
        self.incarrow.grid(row=2,column=4,columnspan=1)                          
        self.decarrow = tk.Button(self.frame_box, text='-1',padx=1,pady=10,font='Ariel 14',
                                  command=self.decrement)
        self.decarrow.grid(row=2,column=0,columnspan=1)
    
    def increment(self):
        #a few lines in other functions switch self.angle from 90 (or 270) to 89.9
        #to prevent this 89.9 number from being inserted into the angle_box and then incremented/decremented, 
        #I'll just pull the self.angle float again.
        self.angle = float(self.angle_box.get())
        self.angle += 1   #increment
        self.angle_box.delete(0,tk.END)   #delete current textbox entry
        self.angle_box.insert(0,str(self.angle))   #update entry with incremented angle
        
        #automatically rotate the rectangle when + is clicked
        self.create_rectangle()
    
    def decrement(self):
        #a few lines in other functions switch self.angle from 90 (or 270) to 89.9 (for instance)
        #to prevent this number from being inserted into the angle_box and then incremented/decremented, 
        #I'll just pull the self.angle float again.
        self.angle = float(self.angle_box.get())
        self.angle -= 1   #decrement
        self.angle_box.delete(0,tk.END)   #delete current textbox entry
        self.angle_box.insert(0,str(self.angle))   #update entry with decremented angle
        
        #automatically rotate when - is clicked
        self.create_rectangle()
    
    def save_sound(self):
        
        #if self.memfile has been defined already, then save as .wav
        #notes: -file will automatically go to 'saved_wavfiles' directory
        #       -.wav will only save the most recent self.midi_file, meaning the user must click "Sonify" to 
                 #sonify their rectangle/parameter tweaks so that they might be reflected in the .wav
        
        if hasattr(self, 'midi_file'):
            
            midi_savename = self.path_to_repos+'saved_wavfiles/'+str(self.galaxy_name)+'-'+str(self.band)+'.mid'   #using our current file conventions to define self.galaxy_name (see relevant line for further details); will save file to saved_wavfile directory
            
            #write file
            with open(midi_savename,"wb") as f:
                self.midi_file.writeFile(f)
            
            wav_savename = self.path_to_repos+'saved_wavfiles/'+str(self.galaxy_name)+'-'+str(self.band)+'.wav'   
            
            #initiate FluidSynth class!
            #gain governs the volume of wavefile. I needed to tweak the source code of midi2audio to 
            #have the gain argument --> I'll give instructions somewhere for how to do so...
            #check my github wiki. :-)
            fs = FluidSynth(sound_font=self.soundfont, gain=3)   
            
            if os.path.isfile(wav_savename):    
                self.namecounter+=1
                wav_savename = self.path_to_repos+'saved_wavfiles/'+str(self.galaxy_name)+'-'+str(self.band)+'-'+str(self.namecounter)+'.wav'                
            else:
                self.namecounter=0
            
            fs.midi_to_audio(midi_savename, wav_savename) 
            
            self.download_success()   #play the jingle
            
            self.time = self.get_wav_length(wav_savename)   #length of soundfile
            
            self.wav_savename = wav_savename   #need for creating .mp4
            
        #if user has not yet clicked "Sonify", then clicking button will activate a popup message
        else:
            self.textbox = 'Do not try to save an empty .wav file! Create a rectangle on the image canvas then click "Sonify" to generate MIDI notes.'
            self.popup()
    
    def initiate_canvas(self):
        
        #I need to add a try...except statement here, in case a user accidentally clicks "Enter/Refresh" without loading a galaxy first. If they do so, then try to successfully load a galaxy, the GUI will break.
        
        try:
            #delete any and all miscellany (galaxy image, squares, lines) from the canvas (created using 
            #self.init_display_size())
            self.label.delete('all')
            self.ax.remove()
        except:
            pass
        
        self.dat, self.dat_header = fits.getdata(str(self.path_to_im.get()), header=True)
        
        #many cutouts, especially those in the r-band, have pesky foreground stars and other artifacts, which will invariably dominate the display of the image stretch. one option is that I can grab the corresponding mask image for the galaxy and create a 'mask bool' of 0s and 1s, then multiply this by the image in order to dictate v1, v2, and the normalization *strictly* on the central galaxy pixel values. 
        
        try:
            full_filepath = str(self.path_to_im.get()).split('/')
            full_filename = full_filepath[-1]
            split_filename = full_filename.replace('.','-').split('-')   #replace .fits with -fits, then split all
            galaxyname = split_filename[0]
            galaxyband = split_filename[3]
        except:
            print('Selected filename is not split with "-" characters with galaxyband; defaulting to generic wavelength.')
            galaxyname = split_filename[0]   #should still be the full filename
            galaxyband = ' '
        
        try:
            if (galaxyband=='g') | (galaxyband=='r') | (galaxyband=='z'):
                mask_path = glob.glob(self.initial_browsedir+galaxyname+'*'+'r-mask.fits')[0]
            if (galaxyband=='W3') | (galaxyband=='W1'):
                mask_path = glob.glob(self.initial_browsedir+galaxyname+'*'+'wise-mask.fits')[0]
                
            mask_image = fits.getdata(mask_path)
            self.mask_bool = ~(mask_image>0)
        
        except:
            self.mask_bool = np.zeros((len(self.dat),len(self.dat)))+1  #create a full array of 1s, won't affect image
            print('Mask image not found; proceeded with default v1, v2, and normalization values.')
        
        v1 = scoreatpercentile(self.dat*self.mask_bool,0.5)
        v2 = scoreatpercentile(self.dat*self.mask_bool,99.9)
        norm_im = simple_norm(self.dat*self.mask_bool,'asinh', min_percent=0.5, max_percent=99.9,
                              min_cut=v1, max_cut=v2)  #'beautify' the image
        
        self.v1slider.configure(from_=np.min(self.dat), to=np.max(self.dat))
        self.v2slider.configure(from_=np.min(self.dat), to=np.max(self.dat))
        
        #set the slider starting values
        self.v1slider.set(v1)
        self.v2slider.set(v2)

        self.ax = self.fig.add_subplot()
        self.im = self.ax.imshow(self.dat,origin='lower',norm=norm_im)
        self.ax.set_xlim(0,len(self.dat)-1)
        self.ax.set_ylim(0,len(self.dat)-1)
        
        self.ax.set_title(f'{galaxyname} ({galaxyband})',fontsize=15)

        self.im_length = np.shape(self.dat)[0]
        self.ymin = int(self.im_length/2-(0.20*self.im_length))
        self.ymax = int(self.im_length/2+(0.20*self.im_length))
        self.x=self.im_length/2
        
        #initiate self.current_bar (just an invisible line...for now)
        self.current_bar, = self.ax.plot([self.im_length/2,self.im_length/2+1],
                                         [self.im_length/2,self.im_length/2+1],
                                         color='None')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_display)    
        
        #activate the draw square/rectangle/quadrilateral/four-sided polygon event
        self.connect_event=self.canvas.mpl_connect('button_press_event',self.drawSqRec)
        
        #add canvas 'frame'
        self.label = self.canvas.get_tk_widget()
        self.label.grid(row=0,column=0,columnspan=3,rowspan=6)
        
        self.galaxy_name = galaxyname    #will need for saving .wav file...
        self.band = galaxyband                 #same rationale
        
    def change_canvas_event(self):
        
        if int(self.var.get())==0:
            self.canvas.mpl_disconnect(self.connect_event)
            self.canvas.mpl_disconnect(self.connect_event_midi)
            self.connect_event = self.canvas.mpl_connect('button_press_event',self.drawSqRec)
        if int(self.var.get())==1:
            self.canvas.mpl_disconnect(self.connect_event)
            self.connect_event = self.canvas.mpl_connect('button_press_event',self.placeBar)
            try:
                self.connect_event_midi = self.canvas.mpl_connect('button_press_event', self.midi_singlenote)
            except:
                pass
         
    #create command function to print info popup message
    def popup(self):
        messagebox.showinfo('Unconventional README.md',self.textbox)
    
    #how silly that I must create a separate popup function for FITS information. sigh.
    def popup_info(self):
        
        try:
            hdu1 = fits.open(str(self.path_to_im.get()))
            self.textbox_info = hdu1[0].header
            hdu1.close()
        except:
            self.textbox_info = 'No header information available.'
        
        popup = tk.Toplevel()     #creates a window on top of the parent frame
        
        vscroll = tk.Scrollbar(popup, orient=tk.VERTICAL)   #generates vertical scrollbar
        vscroll.pack(side=tk.RIGHT, fill=tk.Y)   #PACKS scrollbar -- because this is a new window, we are not bound to using the grid

        text = tk.Text(popup, wrap=None, yscrollcommand=vscroll.set)   #initiate textbox in window; adds vertical and horizontal scrollbars; wrap=None prevents lines from being cut off
        text.pack(expand=True, fill=tk.BOTH)
        
        vscroll.config(command=text.yview)   #not entirely sure what this entails
        
        text.insert(tk.END, self.textbox_info)
    
    #it may not be the most efficient function, as it calculates the distances between every line coordinate and the given (x,y); however, I am not clever enough to conjure up an alternative solution presently.
    def find_closest_bar(self):
        
        #initiate distances list --> for a given (x,y), which point in every line in self.all_line_coords
        #is closest to (x,y)? this distance will be placed in the distances list.
        self.distances=[]
        
        coord=(self.x,self.y)
        
        for line in self.all_line_coords:
            tree = spatial.KDTree(line)
            result=tree.query([coord])
            self.distances.append(result[0])
        
        self.closest_line_index = np.where(np.asarray(self.distances)==np.min(self.distances))[0][0]
    
    def find_closest_mean(self,meanlist):
        
        #from https://stackoverflow.com/questions/12141150/from-list-of-integers-get-number-closest-to-a-given-value
        self.closest_mean_index = np.where(np.asarray(meanlist) == min(meanlist, key=lambda x:abs(x-float(self.mean_px))))[0][0]     
    
    def placeBar(self, event):  
        
        self.x=event.xdata
        self.y=event.ydata
        
        #remove current bar, if applicable
        try:
            self.current_bar.remove()
        except:
            pass
        
        #remove animation bar, if applicable
        try:
            self.l.remove()
        except:
            pass
        
        #if user clicks outside the image bounds, then problem-o.
        if event.inaxes:
            
            #if no rotation of rectangle, just create some vertical bars.
            if (self.angle == 0):
                
                #if x is within the rectangle bounds, all is well. 
                if (self.x<=self.xmax) & (self.x>=self.xmin):
                    pass
                else:
                    #if x is beyond the right side of the rectangle, line will be placed at rightmost end
                    if (self.x>=self.xmax):
                        self.x = self.xmax
                    
                    #if x is beyond the left side of the rectangle, line will be placed at leftmost end
                    if (self.x<=self.xmin):
                        self.x = self.xmin
                        
                n_pixels = int(self.ymax-self.ymin)   #number of pixels between ymin and ymax
                line_x = np.zeros(n_pixels)+int(self.x)
                line_y = np.linspace(self.ymin,self.ymax,n_pixels)       
                self.current_bar, = self.ax.plot(line_x,line_y,linewidth=3,color='red')

                #extract the mean pixel value from this bar
                value_list = np.zeros(n_pixels)
                for index in range(n_pixels):
                    y_coord = line_y[index]
                    px_value = self.dat[int(y_coord)][int(self.x)]   #x will be the same...again, by design.
                    value_list[index] = px_value
                mean_px = '{:.2f}'.format(np.mean(value_list))
                self.val.config(text=f'Mean Pixel Value: {mean_px}',font='Ariel 18')
                self.canvas.draw()      
            
            else:
                
                self.find_closest_bar()   #outputs self.closest_line_index
                
                line_mean = self.mean_list[self.closest_line_index]
                line_coords = self.all_line_coords[self.closest_line_index]
            
                line_xvals = np.asarray(line_coords)[:,0]
                line_yvals = np.asarray(line_coords)[:,1]
                
                self.current_bar, = self.ax.plot([line_xvals[0],line_xvals[-1]],[line_yvals[0],line_yvals[-1]],
                                                linewidth=3,color='red')

                #extract the mean pixel value from this bar
                mean_px = '{:.2f}'.format(line_mean)

                self.val.config(text=f'Mean Pixel Value: {mean_px}',font='Ariel 16')
                self.canvas.draw()
            
            self.mean_px = mean_px
            
                                           
        else:
            print('Keep inside of the bounds of either the rectangle or the image!')
            self.val.config(text='Mean Pixel Value: None', font='Ariel 16')
    
    
    ###FOR RECTANGLES --> CLICK TWICE, DICTATE INCLINATION###
    
    def func(self,x,m,b):
        return m*x+b
    
    #from https://stackoverflow.com/questions/34372480/rotate-point-about-another-point-in-degrees-python
    def rotate(self, point_to_be_rotated, center_point = (0,0)):
        angle_rad = self.angle*np.pi/180
        xnew = np.cos(angle_rad)*(point_to_be_rotated[0] - center_point[0]) - np.sin(angle_rad)*(point_to_be_rotated[1] - center_point[1]) + center_point[0]
        ynew = np.sin(angle_rad)*(point_to_be_rotated[0] - center_point[0]) + np.cos(angle_rad)*(point_to_be_rotated[1] - center_point[1]) + center_point[1]

        return (round(xnew,2),round(ynew,2))
    
    #extract x and y vertex coordinates, and the slope of the lines connecting these points
    #this function "returns" lists of (x,y) vertices, and the slopes of the rectangle perimeter lines
    #NOTE: I choose np.max(x)-np.min(x) as the number of elements comprising each equation. seems fine.
    def get_xym(self):
        
        #self.event_bounds contains the list [self.x1,self.y1,self.x2,self.y2]
        self.p1 = [self.event_bounds[0],self.event_bounds[1]]   #coordinates of first click event
        self.p2 = [self.event_bounds[2],self.event_bounds[3]]   #coordinates of second click event
        
        if self.angle%90 != 0:      #if angle is not divisible by 90, can rotate using this algorithm. 
                        
            n_spaces = int(np.abs(self.p1[0] - self.p2[0]))   #number of 'pixels' between x coordinates
            
            (xc,yc) = ((self.p1[0]+self.p2[0])/2, (self.p1[1]+self.p2[1])/2)
            one_rot = self.rotate(point_to_be_rotated = self.p1, center_point = (xc,yc))
            two_rot = self.rotate(point_to_be_rotated = self.p2, center_point = (xc,yc))
            three_rot = self.rotate(point_to_be_rotated = (self.p1[0],self.p2[1]), center_point = (xc,yc))
            four_rot = self.rotate(point_to_be_rotated = (self.p2[0],self.p1[1]), center_point = (xc,yc))

            x1 = np.linspace(one_rot[0],three_rot[0],n_spaces)
            m1 = (one_rot[1] - three_rot[1])/(one_rot[0] - three_rot[0])
            y1 = three_rot[1] + m1*(x1 - three_rot[0])

            x2 = np.linspace(one_rot[0],four_rot[0],n_spaces)
            m2 = (one_rot[1] - four_rot[1])/(one_rot[0] - four_rot[0])
            y2 = four_rot[1] + m2*(x2 - four_rot[0])

            x3 = np.linspace(two_rot[0],three_rot[0],n_spaces)
            m3 = (two_rot[1] - three_rot[1])/(two_rot[0] - three_rot[0])
            y3 = two_rot[1] + m3*(x3 - two_rot[0])

            x4 = np.linspace(two_rot[0],four_rot[0],n_spaces)
            m4 = (two_rot[1] - four_rot[1])/(two_rot[0] - four_rot[0])
            y4 = two_rot[1] + m4*(x4 - two_rot[0])

            self.x_rot = [x1,x2,x3,x4]
            self.y_rot = [y1,y2,y3,y4]
            self.m_rot = [m1,m2,m3,m4]
            self.n_spaces = n_spaces
            
            self.one_rot = one_rot
            self.two_rot = two_rot
            self.three_rot = three_rot
            self.four_rot = four_rot

        elif (self.angle/90)%2 == 0:  #if angle is divisible by 90 but is 0, 180, 360, ..., no change to rectangle
            
            n_spaces = int(np.abs(self.p1[0] - self.p2[0]))   #number of 'pixels' between x coordinates
            
            x1 = np.zeros(50)+self.p1[0]
            y1 = np.linspace(self.p2[1],self.p1[1],n_spaces)

            x2 = np.linspace(self.p1[0],self.p2[0],n_spaces)
            y2 = np.zeros(50)+self.p2[1]

            x3 = np.linspace(self.p2[0],self.p1[0],n_spaces)
            y3 = np.zeros(50)+self.p1[1]

            x4 = np.zeros(50)+self.p2[0]
            y4 = np.linspace(self.p1[1],self.p2[1],n_spaces)

            self.x_rot = [x1,x2,x3,x4]
            self.y_rot = [y1,y2,y3,y4]
            self.m_rot = [0,0,0,0]
            self.n_spaces = n_spaces
            
            self.one_rot = self.p1
            self.two_rot = self.p2
            self.three_rot = (self.p1[0],self.p2[1])
            self.four_rot = (self.p2[0],self.p1[1])
        
    def RecRot(self):
    
        self.get_xym()   #defines and initiates self.x_rot, self.y_rot, self.m_rot
                
        #create lists
        list_to_mean = []
        self.mean_list = []   #only need to initialize once
        self.all_line_coords = []   #also only need to initialize once --> will give x,y coordinates for every line (hence the variable name).
        
        intvar = int(self.var_w1w3.get())
        
        #for my next trick...I shall attempt to combine w1 and w3 MIDI notes into one file, if the user deems such as desirable. I will likely be the only user to ever utilize this feature.
        if intvar>0:
            self.band_alt = 'W3' if self.band=='W1' else 'W1'
            self.dat_alt = fits.getdata(str(self.path_to_im.get()).replace(self.band,self.band_alt))
            list_to_mean_alt = []
            self.mean_list_alt = []
        
        for i in range(self.n_spaces):  #for the entire n_spaces extent: 
                                        #find x range of between same-index points on opposing sides of the 
                                        #rectangle, determine the equation variables to 
                                        #connect these elements within this desired x range, 
                                        #then find this line's mean pixel value. 
                                        #proceed to next set of elements, etc.

            #points from either x4,y4 (index=3) or x1,y1 (index=0)
            #any angle which is NOT 0,180,360,etc.
            if self.angle%90 != 0:
                self.all_bars = np.zeros(self.n_spaces**2).reshape(self.n_spaces,self.n_spaces)
                xpoints = np.linspace(self.x_rot[3][i],self.x_rot[0][-(i+1)],self.n_spaces)
                b = self.y_rot[0][-(i+1)] - (self.m_rot[2]*self.x_rot[0][-(i+1)])
                ypoints = self.func(xpoints,self.m_rot[2],b)
                
                #convert xpoint, ypoint to arrays, round all elements to 2 decimal places, convert back to lists
                self.all_line_coords.append(list(zip(np.ndarray.tolist(np.round(np.asarray(xpoints),3)),
                                                np.ndarray.tolist(np.round(np.asarray(ypoints),3)))))
                
                for n in range(len(ypoints)):
                    #from the full data grid x, isolate all of values occupying the rows (xpoints) in 
                    #the column ypoints[n]
                    list_to_mean.append(self.dat[int(ypoints[n])][int(xpoints[n])])
                    
                    if intvar>0:
                        list_to_mean_alt.append(self.dat_alt[int(ypoints[n])][int(xpoints[n])])
                         
                self.mean_list.append(np.mean(list_to_mean))
                list_to_mean = []
                
                if intvar>0:
                    self.mean_list_alt.append(np.mean(list_to_mean_alt))
                    list_to_mean_alt = []
            
            #0,180,360,etc.
            if (self.angle/90)%2 == 0:
                xpoints = np.linspace(self.x_rot[3][i],self.x_rot[0][-(i+1)],self.n_spaces)
                b =self.y_rot[0][-(i+1)] - (self.m_rot[2]*self.x_rot[0][-(i+1)])
                ypoints = self.func(xpoints,self.m_rot[2],b)
                
                #convert xpoint, ypoint to arrays, round all elements to 2 decimal places, convert back to lists
                self.all_line_coords.append(list(zip(np.ndarray.tolist(np.round(np.asarray(xpoints),3)),
                                                np.ndarray.tolist(np.round(np.asarray(ypoints),3)))))
                
                for n in range(len(ypoints)):
                    #from the full data grid x, isolate all of values occupying the rows (xpoints) in 
                    #the column ypoints[n]
                    list_to_mean.append(self.dat[int(ypoints[n])][int(xpoints[n])])
                    
                    if intvar>0:
                        list_to_mean_alt.append(self.dat_alt[int(ypoints[n])][int(xpoints[n])])
                    
                self.mean_list.append(np.mean(list_to_mean))
                list_to_mean = []
                
                if intvar>0:
                    self.mean_list_alt.append(np.mean(list_to_mean_alt))
                    list_to_mean_alt = []
            
        #check if all_line_coords arranged from left to right
        #if not, sort it (flip last list to first, etc.) and reverse mean_list accordingly
        #first define coordinates of first and second "starting coordinates"
        first_coor = self.all_line_coords[0][0]
        second_coor = self.all_line_coords[1][0]
        
        #isolate the x values
        first_x = first_coor[0]
        second_x = second_coor[0]
        
        #if the first x coordinate is greater than the second, then all set. 
        #otherwise, lists arranged from right to left. fix.
        #must also flip mean_list so that the values remain matched with the correct lines
        if first_x<second_x:
            self.all_line_coords.sort()
            self.mean_list.reverse()
            
            if intvar>0:
                self.mean_list_alt.reverse()

    def create_rectangle(self,x_one=None,x_two=None,y_one=None,y_two=None):
        
        #the "try" statement will only work if the user-input angle is a float (and not a string)
        #otherwise, angle will default to zero, meaning no rotation
        try:
            self.angle = float(self.angle_box.get())
            if (self.angle/90)%2 == 0:      #if 0,180,360,etc., no different from 0 degree rotation (no rotation)
                self.angle = 0
            if (self.angle/90)%2 == 1:      #if 90, 270, etc., just approximate to be 89.9
                self.angle = 89.9
        except:
            self.angle = 0
            self.angle_box.delete(0,tk.END)
            self.angle_box.insert(0,str(self.angle))
            
        try:
            for line in [self.line_eins,self.line_zwei,self.line_drei,self.line_vier]:
                line_to_remove = line.pop(0)
                line_to_remove.remove()
        except:
            pass
        
        if (self.angle== 0)|(isinstance(self.angle,str)):
            if x_one is not None:    
                         
                self.line_one = self.ax.plot([x_one,x_one],[y_one,y_two],color='crimson',linewidth=2)
                self.line_two = self.ax.plot([x_one,x_two],[y_one,y_one],color='crimson',linewidth=2)
                self.line_three = self.ax.plot([x_two,x_two],[y_one,y_two],color='crimson',linewidth=2)
                self.line_four = self.ax.plot([x_one,x_two],[y_two,y_two],color='crimson',linewidth=2)
                
            else:
            
                self.get_xym()   #defines and initiates self.x_rot, self.y_rot, self.m_rot

                x1,x2,x3,x4=self.one_rot[0],self.two_rot[0],self.three_rot[0],self.four_rot[0]
                y1,y2,y3,y4=self.one_rot[1],self.two_rot[1],self.three_rot[1],self.four_rot[1]

                self.line_eins = self.ax.plot([x1,x3],[y1,y3],color='crimson',linewidth=2)   #1--3
                self.line_zwei = self.ax.plot([x1,x4],[y1,y4],color='crimson',linewidth=2)   #1--4
                self.line_drei = self.ax.plot([x2,x3],[y2,y3],color='crimson',linewidth=2)   #2--3
                self.line_vier = self.ax.plot([x2,x4],[y2,y4],color='crimson',linewidth=2)   #2--4

                self.canvas.draw()

        if self.angle!=0:
            
            #a nonzero angle means the user has already created the unaltered rectangle
            #that is, the coordinates already exist in self.event_bounds (x1,x2,y1,y2)
            #these are called in get_xym
            
            self.get_xym()   #defines and initiates self.x_rot, self.y_rot, self.m_rot

            x1,x2,x3,x4=self.one_rot[0],self.two_rot[0],self.three_rot[0],self.four_rot[0]
            y1,y2,y3,y4=self.one_rot[1],self.two_rot[1],self.three_rot[1],self.four_rot[1]
                        
            self.line_eins = self.ax.plot([x1,x3],[y1,y3],color='crimson')   #1--3
            self.line_zwei = self.ax.plot([x1,x4],[y1,y4],color='crimson')   #1--4
            self.line_drei = self.ax.plot([x2,x3],[y2,y3],color='crimson')   #2--3
            self.line_vier = self.ax.plot([x2,x4],[y2,y4],color='crimson')   #2--4

            self.canvas.draw()
            
    def drawSqRec(self, event):
        
        #remove animation line, if applicable
        try:
            self.l.remove()
        except:
            pass
        
        #remove current bar, if applicable
        try:
            self.current_bar.remove()
        except:
            pass
        
        try:
            self.angle = float(self.angle_box.get())
        except:
            self.angle = 0
            self.angle_box.delete(0,tk.END)
            self.angle_box.insert(0,str(self.angle))
        
        #collect the x and y coordinates of the click event
        #if first click event already done, then just define x2, y2. otherwise, define x1, y1.
        if (self.x1 is not None) & (self.y1 is not None):
            self.x2 = event.xdata
            self.y2 = event.ydata
        else:
            self.x1 = event.xdata
            self.y1 = event.ydata
            first_time=True
        
        #the user has clicked only the 'first' rectangle corner...
        if (self.x1 is not None) & (self.x2 is None):
            #if the corner is within the canvas, plot a dot to mark this 'first' corner
            if event.inaxes:
                self.bound_check=True
                dot = self.ax.scatter(self.x1,self.y1,color='crimson',s=10,marker='*')
                self.sq_mean_value = self.dat[int(self.x1),int(self.y1)]
                self.canvas.draw()
                #for whatever reason, placing dot.remove() here will delete the dot after the second click
                dot.remove()
        
        #if the 'first' corner is already set, then plot the rectangle and print the output mean pixel value
        #within this rectangle
        if (self.x2 is not None):
            
            #assign all event coordinates to an array
            self.event_bounds = [self.x1.copy(),self.y1.copy(),self.x2.copy(),self.y2.copy()]
            
            if event.inaxes:
                if (self.bound_check):
                    self.create_rectangle(x_one=self.x1,x_two=self.x2,y_one=self.y1,y_two=self.y2)
                    self.canvas.draw()
                    
            #reset parameters for next iteration
            self.bound_check = None
            self.x1=None
            self.x2=None
            self.y1=None
            self.y2=None
            
            #similar phenomenon as dot.remove() above.
            try:
                for line in [self.line_one,self.line_two,self.line_three,self.line_four]:
                    line_to_remove = line.pop(0)
                    line_to_remove.remove()
            except:
                pass
    
    # Function for opening the file explorer window
    def browseFiles(self):
        filename = filedialog.askopenfilename(initialdir = self.initial_browsedir, title = "Select a File", filetypes = ([("FITS Files", ".fits")]))
        self.path_to_im.delete(0,tk.END)
        self.path_to_im.insert(0,filename)    
        
    def browseFiles_alt(self):
        self.filename_alt = filedialog.askopenfilename(initialdir = self.initial_browsedir, title = "Select a File", filetypes = ([("FITS Files", ".fits")]))
        return
    
    def reproject_alt_im(self):
        return
            
    
    
    
##########
#the sonification-specific functions...
##########

    #typical sonification mapping function; maps value(s) from one range to another range; returns floats
    def map_value(self, value, min_value, max_value, min_result, max_result):
        result = min_result + (value - min_value)/(max_value - min_value)*(max_result - min_result)
        return result
    
    def midi_setup_bar(self):
        
        #remove animation bar, if applicable
        try:
            self.l.remove()
        except:
            pass
        
        #define various quantities required for midi file generation
        self.y_scale = float(self.y_scale_entry.get())
        self.strips_per_beat = 10
        self.vel_min = int(self.vel_min_entry.get())
        self.vel_max = int(self.vel_max_entry.get())
        self.bpm = int(self.bpm_entry.get())
        self.program = int(self.program_entry.get())   #the instrument!
        self.duration = float(self.duration_entry.get())
        
        try:
            self.angle = float(self.angle_box.get())
            #if the angle angle is no different from 0 (e.g., 180, 360, etc.), just set the angle = 0.
            if (self.angle/90)%2 == 0:
                self.angle = 0
            #if angle is 90, 270, etc., just approximate as 89.9 deg (avoids many problems -- including dividing by cos(90)=0 -- and 89.9 is sufficiently close to 90 degrees)
            if (self.angle/90)%2 == 1:
                self.angle = 89.9
        except:
            self.angle = 0
            self.angle_box.delete(0,tk.END)
            self.angle_box.insert(0,str(self.angle))
        
        selected_sig = self.keyvar.get()
        self.note_names = self.note_dict[selected_sig]
        self.note_names = self.note_names.split("-")   #converts self.note_names into a proper list of note strings
        
        print(selected_sig)
        #print(self.note_names)
                
        #use user-drawn rectangle in order to define xmin, xmax; ymin, ymax. if no rectangle drawn, then default to image width for x and some fraction of the height for y.
        try:
            #for the case where the angle is not rotated
            if self.angle == 0:
                
                self.xmin = int(self.event_bounds[2]) if (self.event_bounds[0]>self.event_bounds[2]) else int(self.event_bounds[0])
                self.xmax = int(self.event_bounds[0]) if (self.event_bounds[0]>self.event_bounds[2]) else int(self.event_bounds[2])
                self.ymin = int(self.event_bounds[3]) if (self.event_bounds[1]>self.event_bounds[3]) else int(self.event_bounds[1])
                self.ymax = int(self.event_bounds[1]) if (self.event_bounds[1]>self.event_bounds[3]) else int(self.event_bounds[3])
            
            #if rectangle is rotated, use rotated coordinates to find mins and maxs
            else:
                xvertices=np.array([self.one_rot[0],self.two_rot[0],self.three_rot[0],self.four_rot[0]])
                yvertices=np.array([self.one_rot[1],self.two_rot[1],self.three_rot[1],self.four_rot[1]])
                
                self.xmin = np.min(xvertices)
                self.xmax = np.max(xvertices)
                
                self.ymin = np.min(yvertices)
                self.ymax = np.max(yvertices)
                
        except:
            print('Defaulting to image parameters for xmin, xmax; ymin, ymax.')
            self.xmin=0
            self.xmax=self.im_length
            self.ymin = int(self.im_length/2-(0.20*self.im_length))
            self.ymax = int(self.im_length/2+(0.20*self.im_length))
            
        self.xminmax_entry.delete(0,tk.END)
        mean_px_min = '{:.2f}'.format(self.xmin)
        mean_px_max = '{:.2f}'.format(self.xmax)
        self.xminmax_entry.insert(0,f'{mean_px_min}, {mean_px_max}')
        
        if self.angle == 0:
            cropped_data = self.dat[self.ymin:self.ymax, self.xmin:self.xmax]   #[rows,columns]; isolates pixels within the user-defined region
            mean_strip_values = []   #create empty array for mean px values of the strips
            vertical_lines = [cropped_data[:, i] for i in range(self.xmax-self.xmin)]
            
            #creating list of vertical strip coordinates (will need for animation!)
            x_coords = np.arange(self.xmin,self.xmax,1)
            y_coords = np.arange(self.ymin,self.ymax,1)
            self.all_line_coords = []
            for i in range(self.xmax-self.xmin):
                x = np.zeros(len(y_coords))+x_coords[i]
                y = y_coords
                self.all_line_coords.append(list(zip(np.ndarray.tolist(np.round(x,3)),
                                                np.ndarray.tolist(np.round(y,3)))))
            
            #creating mean strip values from the vertical line pixel values
            for line in vertical_lines:
                mean_strip_values.append(np.mean(line))
            
            if int(self.var_w1w3.get())>0:
                
                self.band_alt = 'W3' if self.band=='W1' else 'W1'
                self.dat_alt = fits.getdata(str(self.path_to_im.get()).replace(self.band,self.band_alt))
                
                cropped_data_alt = self.dat_alt[self.ymin:self.ymax, self.xmin:self.xmax]
                mean_strip_values_alt = []   #create empty array for mean px values of the strips
                vertical_lines = [cropped_data_alt[:, i] for i in range(self.xmax-self.xmin)]
                
                for line in vertical_lines:
                    mean_strip_values_alt.append(np.mean(line))
                
            #need to define for when playing single note on the GUI
            self.mean_list_norot = mean_strip_values        
        
        if self.angle != 0:
            self.RecRot()
            mean_strip_values = self.mean_list
            
            if int(self.var_w1w3.get())>0:
                mean_strip_values_alt = self.mean_list_alt
    
        #rescale strip number to beats
        self.t_data = np.arange(0,len(mean_strip_values),1) / self.strips_per_beat   #convert to 'time' steps
        
        y_data = self.map_value(mean_strip_values,min(mean_strip_values),max(mean_strip_values),0,1)   #normalizes values
        y_data_scaled = y_data**self.y_scale
        
        #the following converts note names into midi notes
        note_midis = [str2midi(n) for n in self.note_names]  #list of midi note numbers
        n_notes = len(note_midis)
                                                            
        #MAPPING DATA TO THE MIDI NOTES!        
        self.midi_data = []
        #for every data point, map y_data_scaled values such that smallest/largest px is lowest/highest note
        for i in range(len(self.t_data)):   #assigns midi note number to whichever y_data_scaled[i] is nearest
            #apply the "note inversion" if desired --> high values either assigned high notes or, if inverted, low notes
            if int(self.var_rev.get())==0:
                note_index = round(self.map_value(y_data_scaled[i],0,1,0,n_notes-1))
            if int(self.var_rev.get())==1:
                note_index = round(self.map_value(y_data_scaled[i],0,1,n_notes-1,0))
            self.midi_data.append(note_midis[note_index])

        #map data to note velocities (equivalent to the sound volume)
        self.vel_data = []
        for i in range(len(y_data_scaled)):
            note_velocity = round(self.map_value(y_data_scaled[i],0,1,self.vel_min,self.vel_max)) #larger values, heavier sound
            self.vel_data.append(note_velocity)
              
        if int(self.var_w1w3.get())>0:

            #t_data is the same
            y_data_alt = self.map_value(mean_strip_values_alt, min(mean_strip_values_alt), max(mean_strip_values_alt) ,0, 1)

            y_data_scaled_alt = y_data_alt**self.y_scale

            self.midi_data_alt = []
            self.vel_data_alt = []

            for i in range(len(y_data_scaled)):
                note_velocity = round(self.map_value(y_data_scaled_alt[i],0,1,self.vel_min,self.vel_max)) #larger values, heavier sound
                self.vel_data_alt.append(note_velocity)

            for i in range(len(self.t_data)):
                #apply the "note inversion" if desired --> high values either assigned high notes or, if inverted, low notes
                if int(self.var_rev.get())==0:
                    note_index = round(self.map_value(y_data_scaled_alt[i],0,1,0,n_notes-1))
                if int(self.var_rev.get())==1:
                    note_index = round(self.map_value(y_data_scaled_alt[i],0,1,n_notes-1,0))

                self.midi_data_alt.append(note_midis[note_index])
                
        self.midi_allnotes() 
    
    def midi_compare_w1w3(self):
        relative_diff = (np.asarray(self.midi_data)-np.asarray(self.midi_data_alt))/(np.asarray(self.midi_data))
        #a lot is happening here...
        #converting to list an array of bools (with the criterion of abs(relative difference)>5%) that
        #is then itself converted to an array of integers (0, 1) and multiplied by 127, which is the
        #maximum volume.
        bool_vals = (np.abs(relative_diff)<0.05)
        self.relative_vel = np.ndarray.tolist(bool_vals.astype(int)*127)
                
        #little to no relative difference? NO VOLUME! if there is a difference, then 
        self.relative_midi = np.ndarray.tolist(np.zeros(len(self.relative_vel))+np.min(self.midi_data)) #annnnd, lowest midi note value
        
    def midi_allnotes(self):
        
        self.create_rectangle()
        
        #create midi file object, add tempo
        self.memfile = BytesIO()   #create working memory file (allows me to play the note without saving the file...yay!)
        
        if int(self.var_w1w3.get())>0:
            
            #generate the relative velocity and midi note lists!
            self.midi_compare_w1w3()
            
            midi_file = MIDIFile(3)
            
            midi_file.addTempo(track=0,time=0,tempo=self.bpm)
            midi_file.addTempo(track=1,time=0,tempo=self.bpm)
            midi_file.addTempo(track=2,time=0,tempo=self.bpm)
            
            midi_file.addProgramChange(tracknum=0,channel=0,time=0,program=self.program)
            midi_file.addProgramChange(tracknum=1,channel=0,time=0,program=self.program)
            midi_file.addProgramChange(tracknum=2,channel=1,time=0,program=47)
            
            for i in range(len(self.t_data)):
                #I keep the velocity at 100 in order to best compare the two tracks
                midi_file.addNote(track=0, channel=0, pitch=self.midi_data[i], time=self.t_data[i], duration=self.duration,volume=100)
                midi_file.addNote(track=1, channel=0, pitch=self.midi_data_alt[i], time=self.t_data[i], duration=self.duration,volume=100)
                midi_file.addNote(track=2, channel=1, pitch=int(self.relative_midi[i]), time=self.t_data[i], duration=self.duration,volume=int(self.relative_vel[i]))
                
            
            midi_file.writeFile(self.memfile)
        
        else:
            midi_file = MIDIFile(1) #one track
            midi_file.addTempo(track=0,time=0,tempo=self.bpm) #only one track, so track=0th track; begin at time=0, tempo is bpm
            midi_file.addProgramChange(tracknum=0, channel=0, time=0, program=self.program)
            #add midi notes to file
            for i in range(len(self.t_data)):
                midi_file.addNote(track=0, channel=0, pitch=self.midi_data[i], time=self.t_data[i], duration=self.duration, volume=self.vel_data[i])
            midi_file.writeFile(self.memfile)

        mixer.init()
        self.memfile.seek(0)
        mixer.music.load(self.memfile)
        
        #I have to create an entirely new memfile in order to...wait for it...measure the audio length!
        self.memfile_mido = BytesIO()
        midi_file.writeFile(self.memfile_mido)
        self.memfile_mido.seek(0)
        mid = MidiFile(file=self.memfile_mido)
        self.length_of_file = mid.length #-self.duration     
       
        mixer.music.play()
        self.sweep_line()
        
        self.midi_file = midi_file   #will need for saving as .wav file
        
    def midi_singlenote(self,event):
        #the setup for playing *just* one note...using the bar technique. :-)
        self.memfile = BytesIO()   #create working memory file (allows me to play the note without saving the file...yay!)
        
        midi_file = MIDIFile(1) #one track
        midi_file.addTrackName(0,0,'Note')
        midi_file.addTempo(track=0, time=0, tempo=self.bpm)
        midi_file.addProgramChange(tracknum=0, channel=0, time=0, program=self.program)
        
        #for the instance where there is no rotation
        if self.angle == 0:

            self.find_closest_mean(self.mean_list_norot)  #determine the index at which the mean_list element    
                                                          #is closest to the current bar mean outputs 
                                                          #self.closest_mean_index
        else:
            self.find_closest_mean(self.mean_list)
            
        #extract the midi and velocity notes associated with that index. 
        single_pitch = self.midi_data[self.closest_mean_index]
        single_volume = self.vel_data[self.closest_mean_index]
        
        midi_file.addNote(track=0, channel=0, pitch=single_pitch, time=self.t_data[1], duration=1, volume=single_volume)   #isolate the one note corresponding to the click event, add to midi file; the +1 is to account for the silly python notation conventions
        
        midi_file.writeFile(self.memfile)
        #with open(homedir+'/Desktop/test.mid',"wb") as f:
        #    self.midi_file.writeFile(f)

        mixer.init()
        self.memfile.seek(0)   #for whatever reason, have to manually 'rewind' the track in order for mixer to play
        mixer.music.load(self.memfile)
        mixer.music.play()       
    
    ###ANIMATION FUNCTIONS###
    
    def get_wav_length(self,file):
        wav_length = mixer.Sound(file).get_length() - 3   #there seems to be ~3 seconds of silence at the end of each file, so the "- 4" trims this lardy bit. 
        print(f'File Length (seconds): {mixer.Sound(file).get_length()}')
        return wav_length

    def sweep_line(self):
        
        #remove current bar, if applicable
        try:
            self.current_bar.remove()
        except:
            pass
        
        line, = self.ax.plot([], [], lw=1)
        
        self.l,v = self.ax.plot(self.xmin, self.ymin, self.xmax, self.ymax, lw=2, color='red')
        len_of_song_ms = (self.length_of_file-self.duration)*(1e3) #milliseconds
        
        #there are len(self.midi_data)-1 intervals per len_of_song_ms, so
        nintervals = len(self.midi_data)-1
        
        #for the duration of each interval, ...
        self.duration_interval = len_of_song_ms/nintervals   #milliseconds
        
        #note...blitting removes the previous lines
        self.line_anim = animation.FuncAnimation(self.fig, self.update_line_gui, frames=len(self.t_data), 
                                                 interval=self.duration_interval,fargs=(self.l,), 
                                                 blit=True, repeat=False)
    
    #FOR THE GUI ANIMATION
    def update_line_gui(self, num, line):
        current_pos = mixer.music.get_pos()   #milliseconds

        current_time_sec = current_pos / 1e3   #seconds

        # Find the index corresponding to the current time
        frame = min(int((current_time_sec / (self.length_of_file-self.duration)) * len(self.t_data)), len(self.t_data) - 1)

        line_xdat, line_ydat = map(list, zip(*self.all_line_coords[frame]))
        line.set_data([line_xdat[0], line_xdat[-1]], [line_ydat[0], line_ydat[-1]])
        return line,
    
    #FOR W1+W3 OVERLAY.    
    def update_line_all(self, num, line1, line2, line3):

        xvals = np.arange(0, self.xmax_anim+1, 0.05)
        i = xvals[num]
        line1.set_data([i, i], [self.ymin_anim-5, self.ymax_anim+5])

        xvals_alt = self.map_value(xvals,0,np.max(xvals),0,len(self.all_line_coords)-1)
        i_alt = int(xvals_alt[num])

        line_xdat, line_ydat = map(list, zip(*self.all_line_coords[i_alt]))
        line2.set_data([line_xdat[0], line_xdat[-1]], [line_ydat[0], line_ydat[-1]])
        line3.set_data([line_xdat[0], line_xdat[-1]], [line_ydat[0], line_ydat[-1]])

        return line1, line2, line3,
    
    #ONLY ONE WAVELENGTH BAND? BENE - ONLY TWO LINES TO UPDATE.
    def update_line_one(self,num,line1,line2):
        
        i = self.xvals_anim[num]
        line1.set_data([i, i], [self.ymin_anim-5, self.ymax_anim+5])
        
        xvals_alt = self.map_value(self.xvals_anim,0,np.max(self.xvals_anim),0,len(self.all_line_coords)-1)
        i_alt = int(xvals_alt[num])

        line_xdat, line_ydat = map(list, zip(*self.all_line_coords[i_alt]))
        line2.set_data([line_xdat[0], line_xdat[-1]], [line_ydat[0], line_ydat[-1]])
        
        return line1, line2,
    
    def create_midi_animation(self):
        
        self.save_sound()
        
        ani_savename = self.path_to_repos+'saved_mp4files/'+str(self.galaxy_name)+'-'+str(self.band)+'.mp4'   #using our current file conventions to define self.galaxy_name (see relevant line for further details); will save file to saved_mp4files directory
            
        if os.path.isfile(ani_savename):    
            self.namecounter_ani+=1
            ani_savename = self.path_to_repos+'saved_mp4files/'+str(self.galaxy_name)+'-'+str(self.band)+'-'+str(self.namecounter_ani)+'.mp4'                
        else:
            self.namecounter_ani=0
        
        if int(self.var_w1w3.get())>0:
            
            fig = figure.Figure(layout="constrained") 
            spec = fig.add_gridspec(2, 2)

            #ax1 will be the MIDI note plot...
            ax1 = fig.add_subplot(spec[0,:])
            ax2 = fig.add_subplot(spec[1,0])
            ax3 = fig.add_subplot(spec[1,1])
            
            #add alt values to ax1
            ax1.scatter(self.t_data, self.midi_data_alt, self.vel_data_alt, alpha=0.5,
                       edgecolors='black',color='tab:orange',label=self.band_alt)
            
            v1_3 = scoreatpercentile(self.dat_alt*self.mask_bool,0.5)
            v2_3 = scoreatpercentile(self.dat_alt*self.mask_bool,99.9)
            norm_im3 = simple_norm(self.dat_alt*self.mask_bool,'asinh', min_percent=0.5, max_percent=99.9,
                                  min_cut=v1_3, max_cut=v2_3)  #'beautify' the image

            ax3.imshow(self.dat_alt,origin='lower',norm=norm_im3,cmap='gray',alpha=0.9)
            line3, = ax3.plot([], [], lw=1)
            l3,v = ax3.plot(self.xmin, self.ymin, self.xmax, self.ymax, lw=2, color='tab:orange')
            ax3.text(0.05,0.95, self.band_alt,
                horizontalalignment='left',
                verticalalignment='top',
                transform=ax3.transAxes,
                color='tab:orange',fontsize=13,
                fontweight='bold',
                backgroundcolor='white')

            #concatenate the MIDI lists~
            self.ymin_anim = int(np.min(self.midi_data+self.midi_data_alt))
            self.ymax_anim = int(np.max(self.midi_data+self.midi_data_alt))
        
        else:
            
            fig = figure.Figure(layout="constrained")
            spec = fig.add_gridspec(2, 1)
            ax1 = fig.add_subplot(spec[0,:])
            ax2 = fig.add_subplot(spec[1,0])
                        
            self.ymin_anim = int(np.min(self.midi_data))
            self.ymax_anim = int(np.max(self.midi_data))
        
        v1_2 = float(self.v1slider.get())
        v2_2 = float(self.v2slider.get())
        norm_im2 = simple_norm(self.dat*self.mask_bool,'asinh', min_percent=0.5, max_percent=99.9,
                                  min_cut=v1_2, max_cut=v2_2)  #'beautify' the image
        ax2.imshow(self.dat,origin='lower',norm=norm_im2,cmap='gray',alpha=0.9)
        
        line2, = ax2.plot([],[],lw=1)
        l2,v = ax2.plot(self.xmin,self.ymin,self.xmax,self.ymax,lw=2,color='green')
        ax2.text(0.05,0.95, self.band,
                horizontalalignment='left',
                verticalalignment='top',
                transform=ax2.transAxes,
                color='green',fontsize=13,
                fontweight='bold',
                backgroundcolor='white')
        
        ax1.scatter(self.t_data, self.midi_data, self.vel_data, alpha=0.5, color='green', 
                    marker='^', edgecolors='black', label=self.band)
        ax1.legend(fontsize=10,loc='upper left')
        
        line1, = ax1.plot([], [], lw=2)

        self.xmin_anim = 0
        self.xmax_anim = np.max(self.t_data)

        self.xvals_anim = np.arange(0, self.xmax_anim+1, 0.05)   #possible x-values for each pixel line, increments of 0.05 (which are close enough that the bar appears to move continuously)

        l1,v = ax1.plot(self.xmin_anim, self.ymin_anim, self.xmax_anim, self.ymax_anim, lw=2, color='red')
        
        if int(self.var_w1w3.get())>0:
            line_anim = animation.FuncAnimation(fig, self.update_line_all, frames=len(self.xvals_anim), fargs=(l1,l2,l3,),blit=True)
        else:
            line_anim = animation.FuncAnimation(fig, self.update_line_one, frames=len(self.xvals_anim), fargs=(l1,l2,),blit=True)
        
        ax1.set_xlabel('Time interval (s)', fontsize=12)
        ax1.set_ylabel('MIDI note', fontsize=12)
        fig.suptitle(self.galaxy_name,fontsize=15)
        
        FFWriter = animation.FFMpegWriter()
        line_anim.save(ani_savename,fps=len(self.xvals_anim)/(self.time))      
        
        del fig     #I am finished with the figure, so I shall delete references to the figure.
        
        ani_both_savename = self.path_to_repos+'saved_mp4files/'+str(self.galaxy_name)+'-'+str(self.band)+'-concat.mp4'
        ani_both_savename = f'{self.path_to_repos}saved_mp4files/{self.galaxy_name}-{self.band}.mp4'
        
        while os.path.exists('{}{:d}.mp4'.format(ani_both_savename, self.namecounter_ani_both)):
            self.namecounter_ani_both += 1
        filename = '{}{:d}.mp4'.format(ani_both_savename,self.namecounter_ani_both)
        
        input_video = ffmpeg.input(ani_savename)
        input_audio = ffmpeg.input(self.wav_savename)
        
        #comment out these next two lines and "uncomment" the third for the final version!
        os.system('rm /Users/k215c316/Desktop/test.mp4')
        ffmpeg.output(input_video.video, input_audio.audio, '/Users/k215c316/Desktop/test.mp4',codec='copy').run(quiet=True)
        #ffmpeg.output(input_video.video, input_audio.audio, ani_both_savename,codec='copy').run(quiet=True)
        
        #ffmpeg.concat(input_video, input_audio, v=1, a=1).output(ani_both_savename).run(capture_stdout=True, capture_stderr=True)
            
        self.download_success()
        
        self.textbox = 'Done! Check the saved_mp4file directory for the final product.'
        self.popup()
    
    #when file(s) are finished downloading, there will be a ding sound indicating completion. it's fun.
    def download_success(self):
        path = os.getcwd()+'/success.mp3'
        mixer.init()
        mixer.music.set_volume(0.25)
        mixer.music.load(path)
        mixer.music.play()
        
if __name__ == "__main__":
    
    #parameter.txt file unpacking here

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
    
    matplotlib.rcParams['animation.ffmpeg_path'] = path_to_ffmpeg   #need for generating animations...
    
    app = App(path_to_repos, initial_browsedir, soundfont, window_geometry)
    app.mainloop()
    #app.destroy()    
    
    
    #I should ALSO record a video tutorial on how to operate this doohickey.