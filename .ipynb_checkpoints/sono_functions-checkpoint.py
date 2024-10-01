import os
from io import BytesIO

from mido import MidiFile
from midiutil import MIDIFile
from midi2audio import FluidSynth

from pygame import mixer

import ffmpeg

import matplotlib.animation as animation
from matplotlib import figure

import numpy as np



class sono_defs():
    
    def __init__(self, soundfont):
        
        self.soundfont = soundfont
        self.namecounter = 0
        self.namecounter_ani = 0
        self.namecounter_ani_both = 0
        
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
        
    #typical sonification mapping function; maps value(s) from one range to another range; returns floats
    def map_value(self, value, min_value, max_value, min_result, max_result):
        result = min_result + (value - min_value)/(max_value - min_value)*(max_result - min_result)
        return result
    
    def write_midifile(self, bpm, program, duration, midi_data, t_data, vel_data):
        
        self.midi_data = midi_data
        self.t_data = t_data
        self.vel_data = vel_data
        self.bpm = bpm
        self.program = program
        self.duration = duration
        
        #create midi file object, add tempo
        self.memfile = BytesIO()   #create working memory file (allows me to play the note without saving the file...yay!)
        midi_file = MIDIFile(1) #one track
        midi_file.addTempo(track=0,time=0,tempo=self.bpm) #only one track, so track=0th track; begin at time=0, tempo is bpm
        midi_file.addProgramChange(tracknum=0, channel=0, time=0, program=self.program)
        #add midi notes to file
        for i in range(len(self.t_data)):
            midi_file.addNote(track=0, channel=0, pitch=self.midi_data[i], 
                              time=self.t_data[i], duration=self.duration, volume=self.vel_data[i])
        midi_file.writeFile(self.memfile)
        
        #I have to create an entirely new memfile in order to...wait for it...measure the audio length!
        memfile_mido = BytesIO()
        midi_file.writeFile(memfile_mido)
        memfile_mido.seek(0)
        mid = MidiFile(file=memfile_mido)
        self.length_of_file = mid.length #-self.duration

        return self.memfile, midi_file, self.length_of_file
    
    def single_note_midi(self, closest_mean_index):
    
        #the setup for playing *just* one note...using the bar technique. :-)
        self.memfile = BytesIO()   #create working memory file (allows me to play the note without saving the file...yay!)
        
        midi_file = MIDIFile(1) #one track
        midi_file.addTrackName(0,0,'Note')
        midi_file.addTempo(track=0, time=0, tempo=self.bpm)
        midi_file.addProgramChange(tracknum=0, channel=0, time=0, program=self.program)
        
        #extract the midi and velocity notes associated with that index. 
        single_pitch = self.midi_data[closest_mean_index]
        single_volume = self.vel_data[closest_mean_index]
        
        midi_file.addNote(track=0, channel=0, pitch=single_pitch, time=self.t_data[1], duration=1, volume=single_volume)   #isolate the one note corresponding to the click event, add to midi file; the +1 is to account for the silly python notation conventions
        
        midi_file.writeFile(self.memfile)
        #with open(homedir+'/Desktop/test.mid',"wb") as f:
        #    self.midi_file.writeFile(f)
        
        return self.memfile  
    
    def play_sound(self, memfile):
        
        mixer.init()
        #for whatever reason, have to manually 'rewind' the track in order for mixer to play
        self.memfile.seek(0)
        mixer.music.load(memfile)
        mixer.music.play()
    
    #when file(s) are finished downloading, there will be a ding sound indicating completion. it's fun.
    def download_success(self):
        path = os.getcwd()+'/success.mp3'
        mixer.init()
        mixer.music.set_volume(0.25)
        mixer.music.load(path)
        mixer.music.play()
        
    def get_wav_length(self,file):
        wav_length = mixer.Sound(file).get_length() - 3   #there seems to be ~3 seconds of silence at the end of each file, so the "-3" trims this lardy bit. 
        print(f'File Length (seconds): {mixer.Sound(file).get_length()}')
        return wav_length
    
    def save_sound(self, midi_savename, wav_savename, midi_file):

        #write file
        with open(midi_savename,"wb") as f:
            midi_file.writeFile(f)

        #initiate FluidSynth class!
        #gain governs the volume of wavefile. I needed to tweak the source code of midi2audio to 
        #have the gain argument --> check my github wiki for instructions. :-)
        fs = FluidSynth(sound_font=self.soundfont, gain=3)   

        while os.path.exists('{}{:d}.wav'.format(wav_savename, self.namecounter)):
            self.namecounter += 1
        wav_savename = '{}{:d}.wav'.format(wav_savename,self.namecounter)

        fs.midi_to_audio(midi_savename, wav_savename) 

        self.download_success()   #play the jingle

        self.time = self.length_of_file

        self.wav_savename = wav_savename   #need for creating .mp4
        os.system(f'rm {midi_savename}')
        
        
    
    def update_line_one(self,num,line1,line2):

        i = self.xvals_anim[num]
        line1.set_data([i, i], [self.ymin_anim-5, self.ymax_anim+5])
        
        xvals_alt = self.map_value(self.xvals_anim, 
                                    0, np.max(self.xvals_anim), 
                                    0, len(self.all_line_coords)-1)
        i_alt = int(xvals_alt[num])

        line_xdat, line_ydat = map(list, zip(*self.all_line_coords[i_alt]))
        line2.set_data([line_xdat[0], line_xdat[-1]], [line_ydat[0], line_ydat[-1]])
        
        return line1, line2,
    
    def create_midi_animation(self, all_line_coords, ani_savename_unf, norm_im2, dat,
                             xmin, xmax, ymin, ymax, galaxy_name, band):
 
        self.all_line_coords = all_line_coords
        
        while os.path.exists('{}{:d}.mp4'.format(ani_savename_unf, self.namecounter_ani)):
            self.namecounter_ani += 1
        ani_savename = '{}{:d}.mp4'.format(ani_savename_unf,self.namecounter_ani)    
        
        fig = figure.Figure(layout='constrained')
        spec=fig.add_gridspec(2,1)
        ax1 = fig.add_subplot(spec[0,:])
        ax2 = fig.add_subplot(spec[1,0])
        
        ax2.imshow(dat, origin='lower', norm=norm_im2, cmap='gray', alpha=0.9)
        line2, = ax2.plot([],[],lw=1)
        l2,v = ax2.plot(xmin, ymin, xmax, ymax, lw=2, color='red')

        self.xmin_anim = 0
        self.xmax_anim = np.max(self.t_data)
        self.ymin_anim = int(np.min(self.midi_data))
        self.ymax_anim = int(np.max(self.midi_data))

        self.xvals_anim = np.arange(0, self.xmax_anim+1, 0.05)   #possible x-values for each pixel line, increments of 0.05 (which are close enough that the bar appears to move continuously)

        ax1.scatter(self.t_data, self.midi_data, self.vel_data, alpha=0.5, edgecolors='black')
        line, = ax1.plot([], [], lw=2)
        l1,v = ax1.plot(self.xmin_anim, self.ymin_anim, self.xmax_anim, self.ymax_anim, lw=2, color='red')
                
        ax1.set_xlabel('Time interval (s)', fontsize=12)
        ax1.set_ylabel('MIDI note', fontsize=12)
        fig.suptitle(galaxy_name,fontsize=15)
        
        line_anim = animation.FuncAnimation(fig, self.update_line_one, frames=len(self.xvals_anim), fargs=(l1,l2,), blit=True)

        FFWriter = animation.FFMpegWriter()
        line_anim.save(ani_savename,fps=len(self.xvals_anim)/self.time)      
        
        del fig     #I am finished with the figure, so I shall delete references to the figure.
        
        ani_both_savename_unf = ani_savename_unf+'concat'
        
        while os.path.exists('{}{:d}.mp4'.format(ani_both_savename_unf, self.namecounter_ani_both)):
            self.namecounter_ani_both += 1
        ani_both_savename = '{}{:d}.mp4'.format(ani_both_savename_unf,self.namecounter_ani_both)
        
        input_video = ffmpeg.input(ani_savename)
        input_audio = ffmpeg.input(self.wav_savename)
        
        ffmpeg.output(input_video.video,input_audio.audio,ani_both_savename,codec='copy').run(quiet=True)
        
        #for testing purposes (easy access), save concatenated file to Desktop
        #os.system('rm /Users/k215c316/Desktop/test.mp4')
        #ffmpeg.output(input_video.video, input_audio.audio, '/Users/k215c316/Desktop/test.mp4',codec='copy').run(quiet=True)
                  
        self.download_success()
        
        os.system(f'rm {ani_savename}') #remove audioless .mp4 file