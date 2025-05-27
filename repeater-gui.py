#Set shortcut key to play from start time
#Add hotkeys to skip, scrub, load preset etc
#Add midi support, set a midi command to play/pause/rewind etc
#Save presets with track, pic, and timeframe
#Add hotkey to start while ignoring pre-time
#Add preset button to open track in spotify (current_track has spotify link)
#Add volume fade option

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from string_to_time import StringToTime as stt
import time
from tkinter import *
from tkinter import ttk
from PIL import ImageTk, Image
import threading
from os import getenv
import requests
from io import BytesIO
from webbrowser import open_new
import json

SAVE_PATH = "presets/savefile.txt"

#0 is highest, 2 is lowest
IMG_QUALITY = {
    "high": 0,
    "mid": 1,
    "low": 2
}

HINT_TEXT = {
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
    "hello_message": "Tip: You can hit Enter in the start or end field to start the service.",
    "album_cover": "Click on the album cover to open the album in Spotify.",
    "album_label": "Click on the album name to open the album in Spotify.",
    "artist_label": "Click on the artist name to open the artist in Spotify.",
    "song_label": "Click on the song name to open the song in Spotify.",
    "save_preset_button": "Adds the current parameters to a preset, to recall later.",
    "remove_preset_button": "Removes the selected preset.",
    "load_preset_button": "Loads the selected preset",
    "move_up_button": "Moves the preset up in the list.",
    "move_down_button": "Moves the preset down in the list.",
    "preset_cover": "Click the album cover in the preset to start playing the song.",
    "pause_button": "Play/Pause. Stops the loop service.",
    "rewind_button": "Rewinds the current song to the beginning.",
    "prev_button": "Plays the previous song.",
    "next_button": "Plays the next song.",
    "clear_button": "Clears all input fields."
}

presets = {

}

root = Tk()
root.title("Spotify Repeater")
loop = BooleanVar(value=True)

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
prev_album_name = ""
prev_song_name = ""

artist_name = StringVar()
album_name = StringVar()
song_name = StringVar()
release_date = StringVar()
#Already converted
song_duration = StringVar()
album_link = ""
song_link = ""
artist_link = ""
preset_name = StringVar()
cover_img_name = ""

def updateInfo():
    global artist_name
    global album_name
    global song_name
    #global release_date
    #global song_duration
    global artist_link
    global album_link
    global song_link
    global cover_img
    global album_cover
    global album_cover_box
    global artist_label
    global album_label
    global song_label
    global prev_album_name
    global prev_song_name
    info = sp.current_user_playing_track()
    #If a song is playing, info won't be None
    if info != None:
        #song_duration.set(stt.convertTimeToString(info['item']['duration_ms'], return_format=2))
        if prev_song_name != info['item']['name']:
            song_name.set(info['item']['name'])
            prev_song_name = info['item']['name']
            song_link = info['item']['uri']
            song_label.bind('<Button-1>', lambda a, m=song_link: open_new(m))
        #Probably not the best way to update the picture
        #Configure doesn't seem to work
        if prev_album_name != info['item']['album']['name']:
            prev_album_name = info['item']['album']['name']
            #Artist names
            artist_name_buf = ""
            num_artists = 0
            artists = info['item']['artists']
            for artist in artists:
                num_artists += 1
                if num_artists == 1:
                    artist_name_buf += artist['name']
                else:
                    artist_name_buf += ", " + artist['name']

            artist_name.set(artist_name_buf)
            album_name.set(info['item']['album']['name'])
            #release_date.set(info['item']['album']['release_date'])
            #Only the first artist
            artist_link = info['item']['artists'][0]['uri']
            album_link = info['item']['album']['uri']
            #0 is the highest res, 2 the lowest
            cover_img = requests.get(info['item']['album']['images'][IMG_QUALITY['mid']]['url']).content
            image = resizeImg(cover_img, 150, 150, Image.LANCZOS)
            album_cover = ImageTk.PhotoImage(image)
            album_cover_box = Label(root, image=album_cover)
            album_cover_box.grid(row=6, column=0, rowspan=30, columnspan=3, padx=10, pady=(10,0))
            album_cover_box.bind('<Enter>', lambda a, m="album_cover": showHint(m))
            album_cover_box.bind('<Button-1>', lambda a, m=album_link: open_new(m))
            artist_label.bind('<Button-1>', lambda a, m=artist_link: open_new(m))
            album_label.bind('<Button-1>', lambda a, m=album_link: open_new(m))
    else:
        song_name.set("Not playing")
        album_name.set("Not playing")
        artist_name.set("Not playing")

def startEvent(event=None):
    # global start_time
    # global end_time
    # global pre_time
    # global post_time
    global duration
    global start_inf_flag
    global start_loop_flag
    global stop
    global first_loop
    # start_time = t.translate(start_time_entry.get())
    # end_time = t.translate(end_time_entry.get())
    # duration = end_time - start_time

    # #Update duration field
    # if end_time > 0:
    #     #Inserting text doesn't work if the button is disabled
    #     duration_entry.config(state=NORMAL)
    #     duration_entry.delete('0', 'end')
    #     duration_entry.insert(0, t.translateTimeToString(duration))
    #     duration_entry.config(state=DISABLED)
    # pre_time = t.translate(pre_time_entry.get())
    # post_time = t.translate(post_time_entry.get())
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

#TODO: Update to StringVar
def showHint(field):
    global hint_label
    hint_label.configure(text=HINT_TEXT[field])

def clearFields():
    global start_time
    global end_time
    global duration
    global pre_time
    global post_time
    start_time = 0
    end_time = 0
    duration = 0
    pre_time = 0
    post_time = 0
    duration_entry.config(state=NORMAL)
    duration_entry.delete('0', 'end')
    duration_entry.insert(0, t.translateTimeToString(duration))
    duration_entry.config(state=DISABLED)
    start_time_entry.delete('0', 'end')
    end_time_entry.delete('0', 'end')
    pre_time_entry.delete('0', 'end')
    post_time_entry.delete('0', 'end')

def playpause():
    global stop
    stop = True
    info = sp.current_user_playing_track()
    if not info == None:
        if info['is_playing']:
            try:
                sp.pause_playback()
            except:
                pass
        else:
            try:
                sp.start_playback()
            except:
                pass

def nextTrack():
    sp.next_track()
    #updateInfo()

def prevTrack():
    sp.previous_track()
    #updateInfo()

def rewind():
    sp.seek_track(0)

def resizeImg(img_file, x=150, y=150, alg=Image.LANCZOS):
    img = Image.open(BytesIO(img_file))
    #NEAREST, BOX, BILINEAR, HAMMING, BICUBIC, LANCZOS
    img = img.resize((x, y), alg)
    return img

#Put peroidic calls here
def update():
    updateInfo()
    root.after(3000, update)

def savePreset():
    global preset_name
    global song_name
    global song_link
    global album_name
    global album_link
    global artist_name
    global artist_link
    global start_time
    global end_time
    global pre_time
    global post_time
    global loop
    global duration
    global cover_img
    #TODO: Save preset to sidebar
    #TODO: Save cover image
    i = len(presets.keys())
    presets[str(i)] = {
        "name": preset_name.get(),
        "song_name": song_name.get(),
        "song_link": song_link,
        "album_name": album_name.get(),
        "album_link": album_link,
        "artist_name": artist_name.get(),
        "artist_link": artist_link,
        #"cover_img_name": cover_img_name, #file name of the jpg
        "start_time": start_time,
        "end_time": end_time,
        "pre_time": pre_time,
        "post_time": post_time,
        "loop": loop.get(),
        "duration": duration
    }
    json.dump(presets, open("presets/savefile.txt", 'w'))

def loadPreset():
    print("loaded preset")

def updateEntries(entry):
    global start_time
    global end_time
    global pre_time
    global post_time
    global duration
    match entry.casefold():
        case "start_time":
            start_time = t.translate(start_time_entry.get())
            if end_time > start_time:
                duration = end_time - start_time
                duration_entry.config(state=NORMAL)
                duration_entry.delete('0', 'end')
                duration_entry.insert(0, t.translateTimeToString(duration))
                duration_entry.config(state=DISABLED)
        case "end_time":
            end_time = t.translate(end_time_entry.get())
            if end_time > start_time:
                duration = end_time - start_time
                duration_entry.config(state=NORMAL)
                duration_entry.delete('0', 'end')
                duration_entry.insert(0, t.translateTimeToString(duration))
                duration_entry.config(state=DISABLED)
        case "pre_time":
            pre_time = t.translate(pre_time_entry.get())
        case "post_time":
            post_time = t.translate(post_time_entry.get())

#Spotipy config
client_id = getenv('spotipy_client_id')
client_secret = getenv('spotipy_client_secret')
SCOPE = ("user-modify-playback-state", "user-read-currently-playing")
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,client_secret=client_secret,redirect_uri="http://127.0.0.1:3000",scope=SCOPE))

#Starts playback of the song
#sp.start_playback(uris=["spotify:track:02zclmxRto3GAUBdtV7D8i"])

info = sp.current_user_playing_track()
#TODO: Use local image instead of doing this
if info == None:
    cover_img = requests.get("https://media.istockphoto.com/id/1500490255/vector/paper-cover-with-worn-dirty-scratches-for-retro-cd-vinyl-music-album-grunge-texture-mockup.jpg?s=612x612&w=0&k=20&c=mNeHwdIWmXNXi-Rvq53psdee_5xQidKcEcjrxZQXPHk=").content
else:
    cover_img = requests.get(info['item']['album']['images'][IMG_QUALITY['mid']]['url']).content

#Threading stuff
inf_thread = threading.Thread(target=startInf)
loop_thread = threading.Thread(target=startLoop)
inf_thread.daemon = True
loop_thread.daemon = True
loop_thread.start()
inf_thread.start()

#Hello message
hello_msg = ttk.Label(root, padding="10 5 10 5", text="Set a start and a stop time to loop between, and optionally set dead times at the start\nand end of the loop. Alternatively, you can leave the end time blank to leave the song\nplaying and use the hotkey to keep rewinding to the start time.")
hello_msg.grid(row=0, column=0, rowspan=2, columnspan=7)
hello_msg.bind('<Enter>', lambda a, m="hello_message": showHint(m))

#Start time stuff
start_time_msg = ttk.Label(root, text="Start time").grid(row=2, column=1)
start_time_entry = ttk.Entry(root, width=15, justify=CENTER)
start_time_entry.grid(row=3, column=1)
start_time_entry.bind('<Return>', startEvent)
start_time_entry.bind('<FocusOut>', lambda a, m="start_time": updateEntries(m))
#Empty var in lambda to catch event argument from bind
start_time_entry.bind('<Enter>', lambda a, m="start_entry": showHint(m))
copy_start_time_btn = ttk.Button(root, text="C", command=lambda m="start": copyTimestamp(m), width=2) 
copy_start_time_btn.grid(row=3, column=1, sticky=E)
copy_start_time_btn.bind('<Enter>', lambda a, m="copy_button": showHint(m))

#End time stuff
end_time_msg = ttk.Label(root, text="End time").grid(row=2, column=3)
#Slightly wider because the cover messes it up
end_time_entry = ttk.Entry(root, width=16, justify=CENTER)
end_time_entry.grid(row=3, column=3)
end_time_entry.bind('<Return>', startEvent)
end_time_entry.bind('<Enter>', lambda a, m="end_entry": showHint(m))
end_time_entry.bind('<FocusOut>', lambda a, m="end_time": updateEntries(m))
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
pre_time_entry.bind('<FocusOut>', lambda a, m="pre_time": updateEntries(m))

#Post-Time stuffs
post_time_msg = ttk.Label(root, text="Post-time").grid(row=4, column=3)
post_time_entry = ttk.Entry(root, width=15, justify=CENTER)
post_time_entry.grid(row=5, column=3)
post_time_entry.bind('<Enter>', lambda a, m="post-time_entry": showHint(m))
post_time_entry.bind('<FocusOut>', lambda a, m="post_time": updateEntries(m))

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
hint_label = ttk.Label(root, text=HINT_TEXT["hello_message"], padding="0 5 0 5")
hint_label.grid(row=100, column=0, columnspan=7, rowspan=2)

#Song info
#The following part saves to disk
# with open('album_cover.jpg', 'wb') as handler:
#     handler.write(cover_img)
# album_cover = ImageTk.PhotoImage(Image.open("album_cover.jpg"))
#Create image from buffer
    #NEAREST, BOX, BILINEAR, HAMMING, BICUBIC, LANCZOS
image = resizeImg(cover_img, 150, 150, Image.LANCZOS)
album_cover = ImageTk.PhotoImage(image)
album_cover_box = Label(root, image=album_cover)
album_cover_box.grid(row=6, column=0, rowspan=50, columnspan=3, padx=10, pady=(10,0))
album_cover_box.bind('<Button-1>', lambda a, m=album_link: open_new(m))
album_cover_box.bind('<Enter>', lambda a, m="album_cover": showHint(m))
song_label = ttk.Label(root, textvariable=song_name, padding="", font=("Segoe UI", 10, 'bold'))
song_label.grid(row=10, column=3, columnspan=4, sticky=W, pady=(10,0))
song_label.bind('<Button-1>', lambda a, m=song_link: open_new(m))
song_label.bind('<Enter>', lambda a, m="song_label": showHint(m))
album_label = ttk.Label(root, textvariable=album_name, padding="", font=("Segoe UI", 8))
album_label.grid(row=11, column=3, columnspan=4, sticky=W)
album_label.bind('<Button-1>', lambda a, m=album_link: open_new(m))
album_label.bind('<Enter>', lambda a, m="album_label": showHint(m))
artist_label = ttk.Label(root, textvariable=artist_name, padding="", font=("Segoe UI", 8))
artist_label.grid(row=12, column=3, columnspan=4, sticky=W)
artist_label.bind('<Button-1>', lambda a, m=artist_link: open_new(m))
artist_label.bind('<Enter>', lambda a, m="artist_label": showHint(m))

#Media button stuff
pause_btn = ttk.Button(root, text="O", command=playpause, width=3)
pause_btn.grid(row=14, column=3, padx=(30,0))
pause_btn.bind('<Enter>', lambda a, m="pause_button": showHint(m))
rewind_btn = ttk.Button(root, text="<", command=rewind, width=3)
rewind_btn.grid(row=14, column=3, padx=(0,30))
rewind_btn.bind('<Enter>', lambda a, m="rewind_button": showHint(m))
prev_btn = ttk.Button(root, text="<<", command=prevTrack, width=3)
prev_btn.grid(row=14, column=3, sticky=W, padx=(0,0))
prev_btn.bind('<Enter>', lambda a, m="prev_button": showHint(m))
next_btn = ttk.Button(root, text=">>", command=nextTrack, width=3)
next_btn.grid(row=14, column=3, sticky=E, padx=(0,0))
next_btn.bind('<Enter>', lambda a, m="next_button": showHint(m))
clear_fields_btn = ttk.Button(root, text="Clear all", command=clearFields)
clear_fields_btn.grid(row=15, column=5)
clear_fields_btn.bind('<Enter>', lambda a, m="clear_button": showHint(m))

#Preset stuff
save_preset_btn = ttk.Button(root, text="Save preset", command=savePreset)
save_preset_btn.grid(row=14, column=5)
save_preset_btn.bind('<Enter>', lambda a, m="save_preset_button": showHint(m))

#Focus on start time box when window opens
start_time_entry.focus_force()

#root.update()
#Keep song info updated every 5 seconds
update()
root.mainloop()