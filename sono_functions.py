import os
from io import BytesIO
from mido import MidiFile
from midiutil import MIDIFile

from pygame import mixer


class sono_defs():
    
    def __init__(self, soundfont):
        
        self.soundfont = soundfont
        
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
        length_of_file = mid.length #-self.duration

        return self.memfile, midi_file, length_of_file
    
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