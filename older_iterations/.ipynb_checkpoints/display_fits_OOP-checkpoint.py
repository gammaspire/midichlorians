'''
GOAL: re-format display_fits.py in a more readable format.
Layout adopted from https://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter/7557028#7557028
'''

import tkinter as tk
import numpy as np
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import pyplot as plt
from astropy.io import fits
from astropy.wcs import WCS
from tkinter import font as tkFont
from tkinter import messagebox

#create main window container, into which the first page will be placed.
class App(tk.Tk):
    
    def __init__(self, *args, **kwargs):          #INITIALIZE; will always run when App class is called.
        tk.Tk.__init__(self, *args, **kwargs)     #initialize tkinter; args are parameter arguments, kwargs can be dictionary arguments
        
        self.title('Sample Tkinter Structuring')
        self.geometry('1100x700')
        self.resizable(True, True)
        
        #will be filled with heaps of frames and frames of heaps. 
        container = tk.Frame(self)
        container.pack(side='top', fill='both', expand=True)     #fills entire container space
        container.grid_rowconfigure(0,weight=1)
        container.grid_columnconfigure(0,weight=1)

        ## Initialize Frames
        self.frames = {}     #empty dictionary
        frame = MainPage(container, self)   #define frame  
        self.frames[MainPage] = frame     #assign new dictionary entry {MainPage: frame}
        frame.grid(row=0,column=0,sticky='nsew')   #define where to place frame within the container...CENTER!
        
        self.show_frame(MainPage)  #a method to be defined below (see MainPage class)
    
    def show_frame(self, cont):     #'cont' represents the controller, enables switching between frames/windows...I think.
        frame = self.frames[cont]
        frame.tkraise()   #will raise window/frame to the 'front;' if there is more than one frame, quite handy.
        
        
#inherits all from tk.Frame; will be on first window
class MainPage(tk.Frame):    
    
    def __init__(self, parent, controller):
        
        #define a font
        self.helv20 = tkFont.Font(family='Helvetica', size=20, weight='bold')
        
        self.textbox="GOAL: display and loop through all .fits files (if any) in user directory. \n Gnarly features: status label, forward/back buttons in order to browse images, usw. \n In color scheme textbox, type a matplotlib color arg (e.g., rainbow, viridis, gray, cool), then click the button widget underneath. \n The user can do likewise with the save feature, replacing the entry text with the desired filename.png to save a .PNG of the current canvas display to the Desktop. \n Lastly, the canvas is click-interactive: left-click on an image pixel, and the output will modify the pixel's Cartesian coordinates, its RA and DEC coordinates, and its pixel value in the bottom-right frame."
        
        #first frame...
        tk.Frame.__init__(self,parent)
        
        #create display frame, which will hold the canvas and a few button widgets underneath.
        self.frame_display=tk.LabelFrame(self,text='Display',font='Vendana 15',padx=5,pady=5)
        self.frame_display.grid(row=0,column=0,rowspan=10)
        
        #create widgets frame, which currently only holds the color display editor.
        self.frame_widgets=tk.LabelFrame(self,text='Edit Color',padx=2,pady=2)
        self.frame_widgets.grid(row=0,column=1)
        
        #create coord frame, which holds the event labels for the x,y coordinates, RA,DEC coordinates, and the pixel value.
        self.frame_coord=tk.LabelFrame(self,text='Image Coords and Value',padx=5,pady=5)
        self.frame_coord.grid(row=5,column=1,sticky='se')
        
        #create buttons frame, which currently only holds the 'save' button and entry box.
        self.frame_buttons=tk.LabelFrame(self,text='Features',padx=5,pady=5)
        self.frame_buttons.grid(row=2,column=1)
        
        self.get_filedat()

        self.initiate_canvas(image_index=0)
        
        self.change_colormap_manual = lambda: (self.im.set_cmap(self.color_entry.get()), self.canvas.draw())
        self.add_colorwidget()
        
        self.add_statusbar(image_index=0)
        self.add_entry_png()
        self.add_px_info()
        
        self.add_forward_button(image_index=0)
        self.add_backward_button(image_index=0)
        self.add_info_button()
    
    def get_filedat(self):    
        path_to_dir = os.getcwd()   #get current working directory
        self.filenames = os.listdir(path_to_dir)   #create list of all filenames in working directory
        self.data_list = []
        self.file_titles = []     #titles for plt.imshow. if a 2D image, then title will be same a filename. 
        
        #filters out directory items that are not fits files and reads data from those that are.
        for file in np.asarray(self.filenames):
            if ('.fits' not in file):
                self.filenames.remove(file)
            else:
                self.data_list.append(fits.getdata(file))

        self.n_images = len(self.filenames)
        
        if self.n_images==0:
            print('No FITS files in cwd. GUI may not compile correctly, if at all.')

    def add_entry_png(self):
        self.png_name = tk.Entry(self.frame_buttons, width=35, borderwidth=2, bg='black', fg='lime green', font='Arial 20')
        self.png_name.insert(0,'figurename.png')
        self.png_name.grid(row=0,column=0)
        
        self.png_button = tk.Button(self.frame_buttons,text='Save .PNG',padx=20,pady=10,font=self.helv20,command=self.saveFig)
        self.png_button.grid(row=1,column=0)
    
    def add_statusbar(self,image_index):
        self.n_images = str(len(self.filenames))
        status = tk.Label(self.frame_display, text=f'Image {image_index+1} of {self.n_images}', bd=1, relief=tk.SUNKEN)
        status.grid(row=5,column=0,columnspan=3,sticky='we')
    
    def add_px_info(self):
        self.xy = tk.Label(self.frame_coord,text='x_coord, y_coord',font=self.helv20)
        self.xy.grid(row=0,column=0)
        self.val = tk.Label(self.frame_coord,text='Pixel Value: ',font=self.helv20)
        self.val.grid(row=1,column=0)
        self.radec = tk.Label(self.frame_coord,text='(RA (deg), DEC (deg))',font=self.helv20)
        self.radec.grid(row=2,column=0)
        
    def add_colorwidget(self):
        self.color_entry = tk.Entry(self.frame_widgets, width=35, borderwidth=5, bg='black',fg='lime green', font=('Arial 20'))
        self.color_entry.grid(row=0,column=0) 
        self.color_button = tk.Button(self.frame_widgets,text='Set Manual Color Scheme', font=self.helv20, command=self.change_colormap_manual)
        self.color_button.grid(row=1,column=0) 
        
    def add_forward_button(self,image_index):
        #if user has arrived at the last image, then disable the forward button.
        if image_index==int(self.n_images)-1:
            self.button_forward = tk.Button(self.frame_display, text='>>', font=self.helv20, fg='magenta', command=lambda:self.forward(image_index+1),state=tk.DISABLED)
        else:
            self.button_forward = tk.Button(self.frame_display, text='>>', font=self.helv20, fg='magenta', command=lambda:self.forward(image_index+1))
        self.button_forward.grid(row=4,column=2)

    def add_backward_button(self,image_index):
        if image_index==0:
            self.button_back = tk.Button(self.frame_display, text='<<', font=self.helv20, fg='magenta', command=lambda:self.back(image_index-1),state=tk.DISABLED)
        else:
            self.button_back = tk.Button(self.frame_display, text='<<', font=self.helv20, fg='magenta', command=lambda:self.back(image_index-1))
        self.button_back.grid(row=4,column=0)
            
    def add_info_button(self):
        self.info_button = tk.Button(self.frame_display, text='Click for Info', padx=15, pady=10, font='Ariel 20', command=self.popup)
        self.info_button.grid(row=4,column=1)
   
    #define the 'forward button widget'
    def forward(self, image_index):

        #eliminate the current canvas object, then close the plot. I add plt.close() for memory/performance purposes
        self.label.delete('all')
        plt.close()

        self.initiate_canvas(image_index=image_index)
        
        self.change_colormap_manual = lambda: (self.im.set_cmap(self.color_entry.get()), self.canvas.draw())
        self.add_colorwidget()

        self.add_statusbar(image_index=image_index)

        self.add_forward_button(image_index)
        self.add_backward_button(image_index)

    #define the 'back button' widget (see above for notes)    
    def back(self,image_index):

        self.label.delete('all')
        plt.close()

        self.initiate_canvas(image_index=image_index)
        
        self.change_colormap_manual = lambda: (self.im.set_cmap(self.color_entry.get()), self.canvas.draw())
        self.add_colorwidget()
        
        self.add_statusbar(image_index=image_index)
        
        self.add_forward_button(image_index)
        self.add_backward_button(image_index)
    
    def initiate_canvas(self,image_index):
        plt.figure(figsize=(3,3))
        try:
            self.dat=self.data_list[image_index]
            self.im=plt.imshow(self.dat,origin='lower')
            plt.title(self.filenames[image_index],fontsize=10)
            self.file_titles.append(self.filenames[image_index])
        except:
            self.dat=np.random.random((200,200))
            self.im=plt.imshow(self.dat,origin='lower')
            plt.title(self.filenames[image_index]+' not a 2D image.',fontsize=6)
            self.file_titles.append(self.filenames[image_index]+'.')
        im_length = np.shape(self.dat)[0]
        
        self.current_marker = plt.scatter(im_length/2,im_length/3,s=1,color='None')
        
        self.canvas = FigureCanvasTkAgg(plt.gcf(), master=self.frame_display)
        self.canvas.mpl_connect('button_press_event',lambda event: self.plotCoord(event, self.file_titles[image_index]))
        self.canvas.mpl_connect('button_press_event',lambda event: self.plotValue(event, self.dat, im_length))
               
        self.canvas.mpl_connect('button_press_event', self.markCursor)
 
        self.label = self.canvas.get_tk_widget()
        self.label.grid(row=0,column=0,columnspan=3,rowspan=4)    
    
    #create command function to print info popup message
    def popup(self):
        messagebox.showinfo('Unconventional README.md',self.textbox)
    
    def markCursor(self, event):
        x=event.xdata
        y=event.ydata
        self.current_marker.remove()
        self.current_marker = plt.scatter(x,y,s=15,facecolors='none',edgecolors='r',linewidths=1)
        self.canvas.draw()
    
    #create command function to extract coordinates aT ThE cLiCk Of A bUtToN
    #filename is file_title[index] --> if file is valid, then "try" proceeds as normal. if invalid, then "except."
    def plotCoord(self, event, filename):
        x = event.xdata
        y = event.ydata
        try:   #if x,y are within the plot bounds, then xdata and ydata will be floats; can round.
            x = np.round(x,3)
            y = np.round(y,3)
            image = fits.open(filename)
            #if im is .fits and not .fits.fz, use [0] instead of [1]
            if filename[-3:] == '.fz':
                header = image[1].header
            else:
                header = image[0].header
            w=WCS(header)
            RA, DEC = w.all_pix2world(x,y,0)
            RA = np.round(RA,3)
            DEC = np.round(DEC,3)
            self.xy.config(text=f'({x}, {y})',font=self.helv20)
            self.radec.config(text=f'({RA}, {DEC})',font=self.helv20)
        except:   #if outside of plot bounds, then xdata and ydata are NoneTypes; cannot round.
            self.xy.config(text=f'({x}, {y})',font=self.helv20)  
            self.radec.config(text=f'({None}, {None})',font=self.helv20)

    #create command function to extract a pixel value aT ThE cLiCk Of A bUtToN
    def plotValue(self, event, im_dat, length):
        x=event.xdata
        y=event.ydata
        try:
            x = int(x)
            y = int(y)
            value = im_dat[y][x]
            self.val.config(text='Pixel Value: %0.2f'%value,font=self.helv20)
        except:
            value = 'None'
            self.val.config(text='Pixel Value: None',font=self.helv20)     

    #command function to save a figure as shown, placed in (on?) Desktop.
    def saveFig(self):
        plt.savefig(os.getenv("HOME")+'/Desktop/'+str(self.png_name.get()),dpi=250)  
    
if __name__ == "__main__":
    app = App()
    app.mainloop()