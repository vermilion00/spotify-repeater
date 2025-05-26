#Set shortcut key to play from start time
#Add hotkeys to skip, scrub, load preset etc
#Add midi support, set a midi command to play/pause/rewind etc
#Display currently playing track with pic
#Save presets with track, pic, and timeframe
#Add hotkey to start while ignoring pre-time
#Show cover art and song information below current screen

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from string_to_time import StringToTime as stt
import time
from tkinter import *
from tkinter import ttk
import threading
from os import getenv

start_time = 0
end_time = 0
pre_time = 0
post_time = 0
duration = 0
stop = False
t = stt(input_unit="s", input_format=0, return_unit="s", return_type="float", return_format=1)
first_loop = False
restart_loop = False
#Necessary, since they're on separate threads
start_inf_flag = False
start_loop_flag = False
hint_label_text = ""

hint_text = {
    "start_entry": "The timestamp that the section begins at. Leave blank to start the song from 0.",
    "end_entry": "The timestamp that the section ends at. Hit enter to start the loop service.",
    "start_button": "Starts the service, depending on the parameters entered.",
    "stop_button": "Stops the service without pausing playback.",
    "hard_stop_button": "Stops the service and pauses playback",
    "copy_button": "Copies the current Spotify timestamp into the field next to it.",
    "loop_check": "Check to restart the section when it ends, if an end time is set.",
    "pre-time_entry": "Sets an amount of time before the section starts after starting the service.",
    "post-time_entry": "Sets an amount of time before the loop repeats.",
    "duration_entry": "The duration of the currently selected section.",
    "hello_message": "Hit Enter in the start or end field to start the service.",
    "clear": ""
}

def startEvent(event=None):
    global start_time
    global end_time
    global pre_time
    global post_time
    global duration
    global start_inf_flag
    global start_loop_flag
    global stop
    global first_loop
    start_time = t.translate(start_time_entry.get())
    end_time = t.translate(end_time_entry.get())
    duration = end_time - start_time

    #Update duration field
    if end_time > 0:
        #Inserting text doesn't work if the button is disabled
        duration_entry.config(state=NORMAL)
        duration_entry.delete('0', 'end')
        duration_entry.insert(0, t.translateTimeToString(duration))
        duration_entry.config(state=DISABLED)
    pre_time = t.translate(pre_time_entry.get())
    post_time = t.translate(post_time_entry.get())
    if duration > 0:
        start_loop_flag = True
        start_inf_flag = False
        first_loop = True
        stop = True
    elif start_time > 0:
        start_inf_flag = True
        start_loop_flag = False
    else:
        stop = True
        start_inf_flag = False
        start_loop_flag = False

#On separate Thread
def startInf():
    global start_inf_flag
    global start_time
    global pre_time
    while True:
        if start_inf_flag:
            if pre_time > 0:
                try:
                    sp.pause_playback()
                except:
                    pass
                time.sleep(pre_time)
            start_inf_flag = False
            try:
                #While the rest is in s, this requires ms
                sp.seek_track(int(start_time * 1000))
            except:
                print("Something went wrong while trying to seek.")
            #Trying to start playback when already playing gives an error
            try:
                sp.start_playback()
            except:
                pass
        else:
            #TODO: Play around with the time
            time.sleep(0.1)

#On separate Thread
def startLoop():
    global start_loop_flag
    global stop
    global loop
    global start_time
    global end_time
    global post_time
    global first_loop
    global restart_loop
    global duration
    while True:
        if start_loop_flag:
            if stop:
                stop = False
            if pre_time > 0 and first_loop:
                first_loop = False
                try:
                    sp.pause_playback()
                except:
                    pass
                time.sleep(pre_time)
            start_loop_flag = False
            try:
                #While the rest is in s, this requires ms
                sp.seek_track(int(start_time * 1000))
            except:
                print("Seeking track failed")

            #Trying to start playback when already playing gives an error
            try:
                sp.start_playback()
            except:
                pass

            try:
                temp_time = time.time()
                while not stop and time.time() < (temp_time + duration):
                    time.sleep(0.1)
            except:
                print("Start or end time is set incorrectly")
            
            #Assume music is paused if stop is set
            if not stop:
                try:
                    sp.pause_playback()
                except:
                    pass

            #Exit condition
            if loop.get() == True and not stop:
                start_loop_flag = True
                if post_time > 0:
                    temp_time = time.time()
                    while not stop and time.time() < (temp_time + post_time):
                        time.sleep(0.1)
        else:
            time.sleep(0.1)

def copyTimestamp(btn):
    global start_time
    global end_time
    global duration
    track_info = sp.current_user_playing_track()
    match btn.casefold():
        case "start":
            start_time = track_info['progress_ms'] / 1000 #in s
            start_time_entry.delete('0', 'end')
            start_time_entry.insert(0, t.translateTimeToString(start_time))
        case "end":
            end_time = track_info['progress_ms'] / 1000 #in s
            end_time_entry.delete('0', 'end')
            end_time_entry.insert(0, t.translateTimeToString(end_time))
    if start_time > 0 and end_time > 0:
        duration = end_time - start_time
        duration_entry.config(state=NORMAL)
        duration_entry.delete('0', 'end')
        duration_entry.insert(0, t.translateTimeToString(duration))
        duration_entry.config(state=DISABLED)

def stopEvent(pause):
    global stop
    global start_loop_flag
    global start_inf_flag
    stop = True
    start_inf_flag = False
    start_loop_flag = False
    if pause:
        try:
            sp.pause_playback()
        except:
            pass

def showHint(field):
    global hint_label
    hint_label.configure(text=hint_text[field])

#Spotipy config
client_id = getenv('spotipy_client_id')
client_secret = getenv('spotipy_client_secret')
scope = ("user-modify-playback-state", "user-read-currently-playing")
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,client_secret=client_secret,redirect_uri="http://127.0.0.1:3000",scope=scope))

#Threading stuff
inf_thread = threading.Thread(target=startInf)
loop_thread = threading.Thread(target=startLoop)
inf_thread.daemon = True
loop_thread.daemon = True
loop_thread.start()
inf_thread.start()

root = Tk()
root.title("Spotify Repeater")
loop = BooleanVar(value=True)

#Hello message
hello_msg = ttk.Label(root, padding="10 5 10 5", text="Set a start and a stop time to loop between, and optionally set dead times at the start\nand end of the loop. Alternatively, you can leave the end time blank to leave the song\nplaying and use the hotkey to keep rewinding to the start time.")
hello_msg.grid(row=0, column=0, rowspan=2, columnspan=7)
hello_msg.bind('<Enter>', lambda a, m="hello_message": showHint(m))

#Start time stuff
start_time_msg = ttk.Label(root, text="Start time").grid(row=2, column=1)
start_time_entry = ttk.Entry(root, width=15, justify=CENTER)
start_time_entry.grid(row=3, column=1)
start_time_entry.bind('<Return>', startEvent)
#Empty var in lambda to catch event argument from bind
start_time_entry.bind('<Enter>', lambda a, m="start_entry": showHint(m))
copy_start_time_btn = ttk.Button(root, text="C", command=lambda m="start": copyTimestamp(m), width=2) 
copy_start_time_btn.grid(row=3, column=1, sticky=E)
copy_start_time_btn.bind('<Enter>', lambda a, m="copy_button": showHint(m))

#End time stuff
end_time_msg = ttk.Label(root, text="End time").grid(row=2, column=3)
end_time_entry = ttk.Entry(root, width=15, justify=CENTER)
end_time_entry.grid(row=3, column=3)
end_time_entry.bind('<Return>', startEvent)
end_time_entry.bind('<Enter>', lambda a, m="end_entry": showHint(m))
# end_time_entry.bind('<FocusIn>', (lambda args: duration_entry.delete('0', 'end')))
copy_end_time_btn = ttk.Button(root, text="C", command=lambda m="end": copyTimestamp(m), width=2) 
copy_end_time_btn.grid(row=3, column=3, sticky=E)
copy_end_time_btn.bind('<Enter>', lambda a, m="copy_button": showHint(m))

#Duration stuff
duration_msg = ttk.Label(root, text="Duration").grid(row=2, column=4)
duration_entry = ttk.Entry(root, state=DISABLED, justify=CENTER, width=9)
duration_entry.bind('<Enter>', lambda a, m="duration_entry": showHint(m))
# duration_entry.bind('<FocusIn>', (lambda args: duration_entry.delete('0', 'end')))
# duration_entry.bind('<FocusIn>', (lambda args: end_time_entry.delete('0', 'end')))
duration_entry.grid(row=3, column=4)

#Pre-Time stuff
pre_time_msg = ttk.Label(root, text="Pre-time").grid(row=4, column=1)
pre_time_entry = ttk.Entry(root, width=15, justify=CENTER)
pre_time_entry.grid(row=5, column=1)
pre_time_entry.bind('<Enter>', lambda a, m="pre-time_entry": showHint(m))

#Post-Time stuffs
post_time_msg = ttk.Label(root, text="Post-time").grid(row=4, column=3)
post_time_entry = ttk.Entry(root, width=15, justify=CENTER)
post_time_entry.grid(row=5, column=3)
post_time_entry.bind('<Enter>', lambda a, m="post-time_entry": showHint(m))

#Start button
start_btn = ttk.Button(root, text="Start", command=startEvent)
start_btn.grid(row=2, column=5)
start_btn.bind('<Enter>', lambda a, m="start_button": showHint(m))

#Stop button
stop_btn = ttk.Button(root, text="Stop", command=lambda m=False: stopEvent(m))
stop_btn.grid(row=3, column=5)
stop_btn.bind('<Enter>', lambda a, m="stop_button": showHint(m))

#Hard Stop button
hard_stop_btn = ttk.Button(root, text="Hard Stop", command=lambda m=True: stopEvent(m))
hard_stop_btn.grid(row=4, column=5)
hard_stop_btn.bind('<Enter>', lambda a, m="hard_stop_button": showHint(m))

#Loop check box
loop_check = ttk.Checkbutton(root, state="selected", text="Loop", variable=loop)
loop_check.grid(row=5, column=5)
loop_check.bind('<Enter>', lambda a, m="loop_check": showHint(m))

#Hint label
hint_label = ttk.Label(root, text=hint_label_text, padding="0 5 0 5")
hint_label.grid(row=100, column=0, columnspan=7, rowspan=2)

#Focus on start time box when window opens
start_time_entry.focus_force()

#root.update()
root.mainloop()