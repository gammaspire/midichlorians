#all of the main interaction functions/widgets for the GUI window

from audiolazy import str2midi
from pygame import mixer                    #this library is what causes the loading delay methinks

import tkinter as tk
import numpy as np
import os

import matplotlib                          #I need this for matplotlib.use. sowwee.
matplotlib.use('TkAgg')    
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from matplotlib import figure              #see self.fig, self.ax.

from scipy.stats import scoreatpercentile
from scipy import spatial
from astropy.visualization import simple_norm
from astropy.io import fits
from tkinter import font as tkFont
from tkinter import messagebox
from tkinter import filedialog
import glob

#from mido import MidiFile

from rectangle_functions import rectangle
from sono_functions import sono_defs

homedir = os.getenv('HOME')
      
#inherits all from tk.Frame; will be on first window
class MainPage(tk.Frame):    
    
    def __init__(self, parent, controller, path_to_repos, initial_browsedir, soundfont, path_to_ffmpeg):
        
        matplotlib.rcParams['animation.ffmpeg_path'] = path_to_ffmpeg   #need for generating animations?
        
        #generalized parameters given in params.txt file
        self.path_to_repos = path_to_repos
        self.initial_browsedir = initial_browsedir
        self.soundfont = soundfont
        
        #summon the RECTANGLE FUNCTIONS! (see rectangle_functions.py for further information)
        self.rec_func = rectangle()
        
        #summon the SONIFICATION FUNCTIONS! (see son_functions.py for further information)
        self.son_func = sono_defs(soundfont=self.soundfont)
        
        #initiating variables for the self.drawSq function
        self.bound_check=None
        self.x1=None
        self.x2=None
        self.y1=None
        self.y2=None
        self.rec_func.angle=0
        
        #initiate a counter to ensure that files do not overwrite one another for an individual galaxy
        #note: NEEDED FOR THE SAVE WIDGET
        self.namecounter=0
        self.namecounter_ani=0
        self.namecounter_ani_both=0
                
        #dictionary for different key signatures
        self.note_dict = self.son_func.note_dict
        
        #isolate the key signature names --> need for the dropdown menu
        self.keyvar_options=list(self.note_dict.keys())

        #create empty string variable list, then set the default to option 2 (D Major)
        self.keyvar = tk.StringVar()
        self.keyvar.set(self.keyvar_options[2])
        
        #defines the number of rows/columns to resize when resizing the entire window.
        self.rowspan=10
        
        #define a font
        self.helv20 = tkFont.Font(family='Helvetica', size=20, weight='bold')
        
        #initiate (first) frame. there will only be one frame.
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
            
        #create sonification frame, which holds the event button for converting data into sound (midifile).
        #there are also heaps of text boxes with which the user can manipulate the sound conversion parameters
        self.frame_sono=tk.LabelFrame(self,text='Parameters (Click "Sonify" to play)',padx=5,pady=5)
        self.frame_sono.grid(row=7,column=2,rowspan=2,sticky='se')
        for i in range(self.rowspan):
            self.frame_sono.columnconfigure(i, weight=1)
            self.frame_sono.rowconfigure(i, weight=1)
        
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
    
    def populate_soni_widget(self):
        
        self.add_midi_button()
        
        #create all entry textboxes (with labels and initial values), midi button!
   
        #this checkbox inverts the note assignment such that high values have low notes and low values have high notes.
        self.var_rev = tk.IntVar()
        self.rev_checkbox = tk.Checkbutton(self.frame_sono, text='Note Inversion', onvalue=1, offvalue=0, variable=self.var_rev, font='Arial 17')
        self.rev_checkbox.grid(row=0,column=0,columnspan=2)
        
        ylab = tk.Label(self.frame_sono,text='yscale').grid(row=1,column=0)
        self.y_scale_entry = tk.Entry(self.frame_sono, width=10, borderwidth=2, bg='black', fg='lime green', 
                                      font='Arial 15')
        self.y_scale_entry.insert(0,'0.5')
        self.y_scale_entry.grid(row=1,column=1,columnspan=1)
        
        vmin_lab = tk.Label(self.frame_sono,text='Min Velocity').grid(row=2,column=0)
        self.vel_min_entry = tk.Entry(self.frame_sono, width=10, borderwidth=2, bg='black', fg='lime green', 
                                      font='Arial 15')
        self.vel_min_entry.insert(0,'10')
        self.vel_min_entry.grid(row=2,column=1,columnspan=1)
        
        vmax_lab = tk.Label(self.frame_sono,text='Max Velocity').grid(row=3,column=0)
        self.vel_max_entry = tk.Entry(self.frame_sono, width=10, borderwidth=2, bg='black', fg='lime green', 
                                      font='Arial 15')
        self.vel_max_entry.insert(0,'100')
        self.vel_max_entry.grid(row=3,column=1,columnspan=1)
        
        bpm_lab = tk.Label(self.frame_sono,text='BPM').grid(row=4,column=0)
        self.bpm_entry = tk.Entry(self.frame_sono, width=10, borderwidth=2, bg='black', fg='lime green', 
                                  font='Arial 15')
        self.bpm_entry.insert(0,'35')
        self.bpm_entry.grid(row=4,column=1,columnspan=1)
        
        xminmax_lab = tk.Label(self.frame_sono,text='xmin, xmax').grid(row=5,column=0)
        self.xminmax_entry = tk.Entry(self.frame_sono, width=10, borderwidth=2, bg='black', fg='lime green',
                                      font='Arial 15')
        self.xminmax_entry.insert(0,'x1, x2')
        self.xminmax_entry.grid(row=5,column=1,columnspan=1)
        
        key_lab = tk.Label(self.frame_sono,text='Key Signature').grid(row=6,column=0)
        self.key_menu = tk.OptionMenu(self.frame_sono, self.keyvar, *self.keyvar_options)
        self.key_menu.config(bg='black',fg='black',font='Arial 15')
        self.key_menu.grid(row=6,column=1,columnspan=1)
        
        program_lab = tk.Label(self.frame_sono,text='Instrument (0-127)').grid(row=7,column=0)
        self.program_entry = tk.Entry(self.frame_sono, width=10, borderwidth=2, bg='black', fg='lime green', 
                                      font='Arial 15')
        self.program_entry.insert(0,'0')
        self.program_entry.grid(row=7,column=1,columnspan=1)
        
        duration_lab = tk.Label(self.frame_sono,text='Duration (sec)').grid(row=8,column=0)
        self.duration_entry = tk.Entry(self.frame_sono, width=10, borderwidth=2, bg='black', fg='lime green', 
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
        self.saveani_button = tk.Button(self.frame_save, text='Save as MP4', padx=15, pady=10, font='Ariel 20',
                                        command=self.save_midi_animation)
        self.saveani_button.grid(row=0,column=1)
    
    def add_browse_button(self):
        self.button_explore = tk.Button(self.frame_buttons ,text="Browse", padx=20, pady=10, font=self.helv20, 
                                        command=self.browseFiles)
        self.button_explore.grid(row=1,column=0)
        
    def add_enter_button(self):
        self.path_button = tk.Button(self.frame_buttons, text='Enter/Refresh Canvas', padx=20, pady=10, font=self.helv20,command=self.initiate_canvas)
        self.path_button.grid(row=1,column=1)
    
    def add_midi_button(self):
        self.midi_button = tk.Button(self.frame_sono, text='Sonify', padx=20, pady=10, font=self.helv20, 
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
        self.rec_func.angle = float(self.angle_box.get())
        self.rec_func.angle += 1   #increment
        self.angle_box.delete(0,tk.END)   #delete current textbox entry
        self.angle_box.insert(0,str(self.rec_func.angle))   #update entry with incremented angle
        
        #automatically rotate the rectangle when + is clicked
        self.create_rectangle()
    
    def decrement(self):
        self.rec_func.angle = float(self.angle_box.get())
        self.rec_func.angle -= 1   #decrement
        self.angle_box.delete(0,tk.END)   #delete current textbox entry
        self.angle_box.insert(0,str(self.rec_func.angle))   #update entry with decremented angle        
        self.create_rectangle()
        
    def initiate_canvas(self):
        
        #delete any and all miscellany (galaxy image, squares, lines) from the canvas (created using 
        #self.init_display_size())
        self.label.delete('all')
        self.ax.remove()
        
        self.dat = fits.getdata(str(self.path_to_im.get()))
        
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
            self.mask_bool = np.zeros((len(self.dat),len(self.dat)))+1  #create a fully array of 1s, won't affect image
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
     
    #function for opening the file explorer window
    def browseFiles(self):
        filename = filedialog.askopenfilename(initialdir = self.initial_browsedir, title = "Select a File", filetypes = ([("FITS Files", ".fits")]))
        self.path_to_im.delete(0,tk.END)
        self.path_to_im.insert(0,filename) 
    
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
    
    #from the list of means, find the index at which the element is closest in value to the given mean pixel
    def find_closest_mean(self,meanlist):
        #from https://stackoverflow.com/questions/12141150/from-list-of-integers-get-number-closest-to-a-given-value
        self.closest_mean_index = np.where(np.asarray(meanlist) == min(meanlist, key=lambda x:abs(x-float(self.mean_px))))[0][0]     
    
    #plot the bar for the click event!
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
            if (self.rec_func.angle == 0):
                
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
            
    #########################
    ###PLOTTING RECTANGLES###
    #########################

    def create_rectangle(self,x_one=None,x_two=None,y_one=None,y_two=None):
        
        #the "try" statement will only work if the user-input angle is a float (and not a string)
        #otherwise, angle will default to zero, meaning no rotation
        try:
            self.rec_func.angle = float(self.angle_box.get())
            if (self.rec_func.angle/90)%2 == 0:      #if 0,180,360,etc., no different from 0 degree rotation (no rotation)
                self.rec_func.angle = 0
            if (self.rec_func.angle/90)%2 == 1:      #if 90, 270, etc., just approximate to be 89.9
                self.rec_func.angle = 89.9
        except:
            self.rec_func.angle = 0
            self.angle_box.delete(0,tk.END)
            self.angle_box.insert(0,str(self.rec_func.angle))
            
        try:
            for line in [self.line_eins,self.line_zwei,self.line_drei,self.line_vier]:
                line_to_remove = line.pop(0)
                line_to_remove.remove()
        except:
            pass
        
        if ((self.rec_func.angle== 0)|(isinstance(self.rec_func.angle,str)))&(x_one is not None):
            if x_one is not None:    
                         
                self.line_one = self.ax.plot([x_one,x_one],[y_one,y_two],color='crimson',linewidth=2)
                self.line_two = self.ax.plot([x_one,x_two],[y_one,y_one],color='crimson',linewidth=2)
                self.line_three = self.ax.plot([x_two,x_two],[y_one,y_two],color='crimson',linewidth=2)
                self.line_four = self.ax.plot([x_one,x_two],[y_two,y_two],color='crimson',linewidth=2)

        #if self.rec_func.angle!=0 and is not a string, AND x_one is None...
        else:    
            #a nonzero angle means the user has already created the unaltered rectangle
            #that is, the coordinates already exist in self.event_bounds (x1,x2,y1,y2)
            #these are called in get_xym

            self.rec_func.get_xym(event_bounds=self.event_bounds)   #defines and initiates self.x_rot, self.y_rot, self.m_rot
                
            x1,x2,x3,x4=self.rec_func.one_rot[0], self.rec_func.two_rot[0], self.rec_func.three_rot[0], self.rec_func.four_rot[0]
            y1,y2,y3,y4=self.rec_func.one_rot[1], self.rec_func.two_rot[1], self.rec_func.three_rot[1], self.rec_func.four_rot[1]    
                
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
            self.rec_func.angle = float(self.angle_box.get())
        except:
            self.rec_func.angle = 0
            self.angle_box.delete(0,tk.END)
            self.angle_box.insert(0,str(self.rec_func.angle))
        
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
    
    ############################
    ###SONIFICATION FUNCTIONS###
    ############################

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
            self.rec_func.angle = float(self.angle_box.get())
            #if the angle angle is no different from 0 (e.g., 180, 360, etc.), just set the angle = 0.
            if (self.rec_func.angle/90)%2 == 0:
                self.rec_func.angle = 0
            #if angle is 90, 270, etc., just approximate as 89.9 deg (avoids many problems -- including dividing by cos(90)=0 -- and 89.9 is sufficiently close to 90 degrees)
            if (self.rec_func.angle/90)%2 == 1:
                self.rec_func.angle = 89.9
        except:
            self.rec_func.angle = 0
            self.angle_box.delete(0,tk.END)
            self.angle_box.insert(0,str(self.rec_func.angle))
        
        selected_sig = self.keyvar.get()
        self.note_names = self.note_dict[selected_sig]
        self.note_names = self.note_names.split("-")   #converts self.note_names into a proper list of note strings
        
        print(selected_sig)
        #print(self.note_names)
        
        #using rectangle_functions.py to extract min and max coordinates from the two click events
        self.rec_func.get_minmax(self.event_bounds, self.im_length)
        self.xmin = self.rec_func.xmin
        self.xmax = self.rec_func.xmax
        self.ymin = self.rec_func.ymin
        self.ymax = self.rec_func.ymax
        
        self.xminmax_entry.delete(0,tk.END)
        mean_px_min = '{:.2f}'.format(self.xmin)
        mean_px_max = '{:.2f}'.format(self.xmax)
        self.xminmax_entry.insert(0,f'{mean_px_min}, {mean_px_max}')
        
        self.rec_func.get_line_vals(dat=self.dat, event_bounds=self.event_bounds)
        
        #re-define rec_func variables 
        self.all_line_coords = self.rec_func.all_line_coords
        mean_strip_values = self.rec_func.mean_strip_values
        self.mean_list = self.rec_func.mean_list
    
        #rescale strip number to beats
        self.t_data = np.arange(0,len(mean_strip_values),1) / self.strips_per_beat   #convert to 'time' steps
        
        y_data = self.son_func.map_value(mean_strip_values,min(mean_strip_values),max(mean_strip_values),0,1)   #normalizes values
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
                note_index = round(self.son_func.map_value(y_data_scaled[i],0,1,0,n_notes-1))
            if int(self.var_rev.get())==1:
                note_index = round(self.son_func.map_value(y_data_scaled[i],0,1,n_notes-1,0))
            self.midi_data.append(note_midis[note_index])

        #map data to note velocities (equivalent to the sound volume)
        self.vel_data = []
        for i in range(len(y_data_scaled)):
            note_velocity = round(self.son_func.map_value(y_data_scaled[i],0,1,self.vel_min,self.vel_max)) #larger values, heavier sound
            self.vel_data.append(note_velocity)
                
        self.midi_allnotes() 
        
    def midi_allnotes(self):
        
        self.create_rectangle()

        self.memfile, self.midi_file, self.length_of_file = self.son_func.write_midifile(self.bpm, self.program, self.duration, self.midi_data, self.t_data, self.vel_data)        
        
        self.son_func.play_sound(self.memfile)
        self.sweep_line()
                
    def midi_singlenote(self,event):

        #for the instance where there is no rotation
        if self.rec_func.angle == 0:
            #determine the index at which the mean_list element is closest to the current bar mean outputs
            self.find_closest_mean(self.mean_list)  
        else:
            self.find_closest_mean(self.mean_list)

        self.memfile = self.son_func.single_note_midi(self.closest_mean_index)
        
        self.son_func.play_sound(self.memfile)       
    
    def save_sound(self):
        
        #if self.memfile has been defined already, then save as .wav
        #notes: -file will automatically go to 'saved_wavfiles' directory
        #       -.wav will only save the most recent self.midi_file, meaning the user must click "Sonify" to 
                 #sonify their rectangle/parameter tweaks so that they might be reflected in the .wav
        
        if hasattr(self, 'midi_file'):
            
            midi_savename = self.path_to_repos+'saved_wavfiles/'+str(self.galaxy_name)+'-'+str(self.band)+'.mid'   #using our current file conventions to define self.galaxy_name (see relevant line for further details); will save file to saved_wavfile directory
            
            wav_savename = f'{self.path_to_repos}saved_wavfiles/{self.galaxy_name}-{self.band}-'
            
            self.son_func.save_sound(midi_savename, wav_savename, self.midi_file)
            
        #if user has not yet clicked "Sonify", then clicking button will activate a popup message
        else:
            self.textbox = 'Do not try to save an empty .wav file! Create a rectangle on the image canvas then click "Sonify" to generate MIDI notes.'
            self.popup()
    
    def save_midi_animation(self):
        
        self.save_sound()
        
        v1_2 = float(self.v1slider.get())
        v2_2 = float(self.v2slider.get())
        norm_im2 = simple_norm(self.dat*self.mask_bool,'asinh', min_percent=0.5, max_percent=99.9, min_cut=v1_2, max_cut=v2_2) 
        
        ani_savename = f'{self.path_to_repos}saved_mp4files/{self.galaxy_name}-{self.band}-'
        
        self.son_func.create_midi_animation(self.all_line_coords, ani_savename, norm_im2, 
                              self.dat,self.xmin, self.xmax, self.ymin, self.ymax, 
                              self.galaxy_name, self.band)
        
        self.textbox = 'Done! Check the saved_mp4file directory for the final product.'
        self.popup()
    
    
    #############################
    ###GUI ANIMATION FUNCTIONS###
    #############################

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