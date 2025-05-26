#Set shortcut key to play from start time
#Add hotkeys to skip, scrub, load preset etc
#Add midi support, set a midi command to play/pause/rewind etc
#Add button to copy spotify timestamp to field
#Display currently playing track with pic
#Save presets with track, pic, and timeframe
#Add hotkey to start while ignoring pre-time

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from string_to_time import StringToTime as stt
import time
from tkinter import *
from tkinter import ttk
import threading
from os import getenv

start_time = 0
stop_time = 0
pre_time = 0
post_time = 0
duration = 0
stop = False
t = stt(return_type="s", format=0, return_format="float")
first_loop = False
restart_loop = False
#Necessary, since they're on separate threads
start_inf_flag = False
start_loop_flag = False

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
        duration_entry.insert(0, stt.timeToString(duration, input_type="s"))
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
            if loop.get() == 1 and not stop:
                start_loop_flag = True
                if post_time > 0:
                    temp_time = time.time()
                    while not stop and time.time() < (temp_time + post_time):
                        time.sleep(0.1)
        else:
            time.sleep(0.1)

#TODO: Add this
def copyTimestamp():
    print("Copied timestamp")
    #track_info = sp.current_user_playing_track()

def stopEvent(event=None):
    global stop
    global start_loop_flag
    global start_inf_flag
    stop = True
    start_inf_flag = False
    start_loop_flag = False
    try:
        sp.pause_playback()
    except:
        pass

#TODO: Remove these (Environment Variables)
client_id = getenv('spotipy_client_id')
client_secret = getenv('spotipy_client_secret')

scope = ("user-modify-playback-state", "user-read-currently-playing")
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,client_secret=client_secret,redirect_uri="http://127.0.0.1:3000",scope=scope))

print(sp.current_user_playing_track())

inf_thread = threading.Thread(target=startInf)
loop_thread = threading.Thread(target=startLoop)
inf_thread.daemon = True
loop_thread.daemon = True
loop_thread.start()
inf_thread.start()

root = Tk()
root.title("Spotify Repeater")
loop = BooleanVar(value=True)
hello_msg = ttk.Label(root, padding="10 5 10 5", text="Set a start and a stop time to loop between, and optionally set dead times at the start and end of the loop.\nAlternatively, you can leave the end time blank to leave the song playing\nand use the hotkey to keep rewinding to the start time.")
hello_msg.grid(row=0, column=0, rowspan=2, columnspan=6)
start_time_msg = ttk.Label(root, text="Start time").grid(row=2, column=0)
start_time_str = "" #TODO: Do i need these?
start_time_entry = ttk.Entry(root, textvariable=start_time_str, width=15, justify=CENTER)
start_time_entry.grid(row=3, column=0)
start_time_entry.bind('<Return>', startEvent)
copy_start_time_btn = ttk.Button(root, text="C", command=copyTimestamp, width=2) 
copy_start_time_btn.grid(row=3, column=1)
end_time_msg = ttk.Label(root, text="End time").grid(row=2, column=2)
end_time_str = "" 
end_time_entry = ttk.Entry(root, textvariable=end_time_str, width=15, justify=CENTER)
end_time_entry.grid(row=3, column=2)
end_time_entry.bind('<Return>', startEvent)
# end_time_entry.bind('<FocusIn>', (lambda args: duration_entry.delete('0', 'end')))
copy_end_time_btn = ttk.Button(root, text="C", command=copyTimestamp, width=2) 
copy_end_time_btn.grid(row=3, column=3)
duration_msg = ttk.Label(root, text="Duration").grid(row=2, column=4)
duration_str = ""
duration_entry = ttk.Entry(root, textvariable=duration_str, state=DISABLED, justify=CENTER, width=9)
# duration_entry.bind('<FocusIn>', (lambda args: duration_entry.delete('0', 'end')))
# duration_entry.bind('<FocusIn>', (lambda args: end_time_entry.delete('0', 'end')))
duration_entry.grid(row=3, column=4)
duration_entry.bind('<Return>', startEvent)
pre_time_msg = ttk.Label(root, text="Pre-time").grid(row=4, column=0)
pre_time_str = ""
pre_time_entry = ttk.Entry(root, textvariable=pre_time_str, width=15, justify=CENTER)
pre_time_entry.grid(row=5, column=0)
post_time_msg = ttk.Label(root, text="Post-time").grid(row=4, column=2)
post_time_str = ""
post_time_entry = ttk.Entry(root, textvariable=post_time_str, width=15, justify=CENTER)
post_time_entry.grid(row=5, column=2)
start_btn = ttk.Button(root, text="Start", command=startEvent)
start_btn.grid(row=3, column=5)
stop_btn = ttk.Button(root, text="Stop", command=stopEvent)
stop_btn.grid(row=4, column=5)
loop_check = ttk.Checkbutton(root, state="selected", text="Loop", variable=loop).grid(row=5, column=5)
#Hacky way to get bottom padding to work because google doesn't help
empty_label = ttk.Label(root).grid(row=6, column=0)

#Focus on start time box when window opens
start_time_entry.focus_force()

#root.update()
root.mainloop()