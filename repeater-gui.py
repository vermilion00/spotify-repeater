#Set shortcut key to play from start time
#Add hotkeys to skip, scrub, load preset etc
#Add midi support, set a midi command to play/pause/rewind etc
#Add hotkey to start while ignoring pre-time
#Add volume fade option
#Scrolling song info labels

#TODO:
#Fix song playing for a split second when preset is loaded
#Fix main view shifting around when preset view is expanded

#MARK: Imports
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from string_to_time import StringToTime as stt
from string_to_time import TimeToString as tts
import time
from tkinter import *
from tkinter import ttk
from PIL import ImageTk, Image
import threading
from os import getenv, makedirs, path, remove
from ctypes import windll
import requests
from io import BytesIO
from webbrowser import open_new
import json
from re import sub
from tkscrolledframe import ScrolledFrame

#MARK: Constants
NOT_PLAYING_IMG = ".presets/not_playing.jpg"
SAVE_DIR = ".presets"
SAVE_PATH = ".presets/savefile.txt"
FORBIDDEN_CHARS = r'[\\/:*?"<>|]' #Not allowed in windows file names
test = r'Test\<>///|||???::*'

#In char units
PLAYER_LABEL_WIDTH = 44
PRESET_LABEL_WIDTH = 20

#TODO: Make sure this works on other platforms
#Make presets folder if it doesn't exist
if not path.exists(SAVE_DIR):
    makedirs(SAVE_DIR)
    ret = windll.kernel32.SetFileAttributesW(SAVE_DIR, 0x02)

#0 is highest, 2 is lowest
IMG_QUALITY = {
    "high": 0,
    "mid": 1,
    "low": 2
}

#MARK: Hints
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
    "clear_button": "Clears all input fields.",
    "show_presets_button": "Shows the preset sidebar.",
    "hide_presets_button": "Hides the preset sidebar.",
    "preset_bar": "Click on a preset to be able to load or delete it.",
    "delete_preset_button": "Deletes the selected preset.",
    "preset_name_entry": "Enter the name for the saved preset."
}

data = {

}

#Stub for later features
settings = {
    'show_presets': True
}

#MARK: Update Info
#On separate thread
def updateInfo():
    global artist_name
    global album_name
    global song_name
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
    while True:
        info = sp.current_user_playing_track()
        #If a song is playing, info won't be None
        if info != None:
            if prev_song_name != info['item']['name']:
                song_name.set(info['item']['name'])
                prev_song_name = info['item']['name']
                song_link = info['item']['uri']
                song_label.bind('<Button-1>', lambda a, m=song_link: open_new(m))
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
                #Only the first artist
                artist_link = info['item']['artists'][0]['uri']
                album_link = info['item']['album']['uri']
                #Probably not the best way to update the picture
                #Configure doesn't seem to work
                cover_img = requests.get(info['item']['album']['images'][IMG_QUALITY['mid']]['url']).content
                image = resizeImg(cover_img, 150, 150, Image.LANCZOS)
                album_cover = ImageTk.PhotoImage(image)
                album_cover_box = Label(mainframe, image=album_cover)
                album_cover_box.grid(row=6, column=0, rowspan=30, columnspan=3, padx=10, pady=(10,0))
                #TODO: Is it really necessary to rebind all of these on a change?
                album_cover_box.bind('<Enter>', lambda a, m="album_cover": showHint(m))
                album_cover_box.bind('<Button-1>', lambda a, m=album_link: openURL(m))
                artist_label.bind('<Button-1>', lambda a, m=artist_link: openURL(m))
                album_label.bind('<Button-1>', lambda a, m=album_link: openURL(m))
        else:
            song_name.set("Not playing")
            album_name.set("Not playing")
            artist_name.set("Not playing")
        time.sleep(1)

#MARK: Start event
def startEvent(event=None):
    global duration
    global start_inf_flag
    global start_loop_flag
    global stop
    global first_loop
    updateEntries("all")
    #Necessary to avoid 0s loops
    stop = True
    if duration > 0:
        start_loop_flag = True
        start_inf_flag = False
        first_loop = True
    elif start_time > 0:
        start_inf_flag = True
        start_loop_flag = False
    else:
        start_inf_flag = False
        start_loop_flag = False

#On separate thread
def startService():
    global start_inf_flag
    global start_loop_flag
    while True:
        time.sleep(0.1)
        if start_inf_flag:
            #Functions called by thread stay on that thread
            startInf()
        elif start_loop_flag:
            startLoop()

#MARK: Start inf
def startInf():
    global start_inf_flag
    global start_time
    global pre_time
    global stop
    stop = False
    start_inf_flag = False
    if pre_time > 0:
        try:
            sp.pause_playback()
        except:
            pass
        time.sleep(pre_time)
    if not stop:
        try:
            #While the rest is in s, this requires ms
            sp.seek_track(position_ms=int(start_time * 1000))
            sp.start_playback()
        except:
            print("Something went wrong while trying to seek.")

#MARK: Start loop
def startLoop():
    global start_loop_flag
    global start_time
    global end_time
    global pre_time
    global post_time
    global stop
    global loop
    global first_loop
    start_loop_flag = False
    if stop:
        stop = False
    if pre_time > 0 and first_loop:
        first_loop = False
        try:
            sp.pause_playback()
        except:
            pass
        time.sleep(pre_time)
    try:
        #While the rest is in s, this requires ms
        sp.seek_track(position_ms=int(start_time * 1000))
        sp.start_playback()
    except:
        print("Seeking track failed")
    try:
        temp_time = time.time()
        while not stop and time.time() < (temp_time + end_time - start_time):
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
        start_loop_flag = False

#MARK: Copy timestamp
def copyTimestamp(btn):
    global start_time
    global end_time
    global duration
    track_info = sp.current_user_playing_track()
    match btn.casefold():
        case "start":
            start_time = track_info['progress_ms'] / 1000 #in s
            start_time_entry.delete('0', 'end')
            start_time_entry.insert(0, s.translateTimeToString(start_time))
        case "end":
            end_time = track_info['progress_ms'] / 1000 #in s
            end_time_entry.delete('0', 'end')
            end_time_entry.insert(0, s.translateTimeToString(end_time))
    if start_time > 0 and end_time > 0:
        duration = end_time - start_time
        duration_entry.config(state=NORMAL)
        duration_entry.delete('0', 'end')
        duration_entry.insert(0, s.translateTimeToString(duration))
        duration_entry.config(state=DISABLED)

#MARK: Stop Event
def stopEvent(pause=False):
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

#MARK: Helper funcs
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

def openURL(url):
    if url != "":
        open_new(url)

def resizeImg(img_file, x=150, y=150, alg=Image.LANCZOS):
    img = Image.open(BytesIO(img_file))
    #NEAREST, BOX, BILINEAR, HAMMING, BICUBIC, LANCZOS
    img = img.resize((x, y), alg)
    return img

def showHint(field):
    global hint_label
    hint_label.configure(text=HINT_TEXT[field])

#MARK: Clear fields
def clearFields():
    global start_time
    global end_time
    global duration
    global pre_time
    global post_time
    global stop
    #Stop the service to avoid issues
    stop = True
    start_time = 0
    end_time = 0
    duration = 0
    pre_time = 0
    post_time = 0
    duration_entry.config(state=NORMAL)
    duration_entry.delete('0', 'end')
    duration_entry.insert(0, s.translateTimeToString(duration))
    duration_entry.config(state=DISABLED)
    start_time_entry.delete('0', 'end')
    end_time_entry.delete('0', 'end')
    pre_time_entry.delete('0', 'end')
    post_time_entry.delete('0', 'end')

#MARK: Save presets
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
    global menu_visibility
    global preset_num
    
    #Don't allow saving "not playing" presets
    if song_name.get() != "Not playing":
        image = resizeImg(cover_img, 60, 60, Image.LANCZOS)
        img_path = ".presets/" + sub(FORBIDDEN_CHARS, "", album_name.get()) + ".jpg"
        image.save(img_path)
        #TODO: If data[0] becomes the setting dict, remove the +1
        i = len(data.keys()) + 1
        name = preset_name.get()
        #Clear the preset name field
        preset_name.set("")
        if name == "":
            name = f"Preset {i}"
        preset = {
            "preset_name": name,
            "song_name": song_name.get(),
            "song_link": song_link,
            "album_name": album_name.get(),
            "album_link": album_link,
            "artist_name": artist_name.get(),
            "artist_link": artist_link,
            "img_path": img_path, #path and name of the jpg
            "start_time": start_time,
            "end_time": end_time,
            "pre_time": pre_time,
            "post_time": post_time,
            "loop": loop.get(),
            "duration": duration
        }
        data[str(i)] = preset
        json.dump(data, open(SAVE_PATH, 'w'), indent=4)
        preset_num += 1
        createPreset(i, preset, "from_buffer")
        if not menu_visibility:
            toggleMenu()

#MARK: Load preset
def loadPreset(preset):
    global data
    global start_time #int
    global start_time_entry
    global end_time #int
    global end_time_entry
    global pre_time #int
    global pre_time_entry
    global post_time #int
    global post_time_entry
    global song_name #StringVar
    global song_label
    global song_link #str
    global album_name #StringVar
    global album_label
    global album_link #str
    global artist_name #StringVar
    global artist_label
    global artist_link #str
    global duration #int
    global duration_entry
    global loop #BooleanVar
    global selected_preset
    if preset != selected_preset:
        preset = str(preset)
        start_time = data[preset]['start_time']
        start_time_entry.delete('0', 'end')
        start_time_entry.insert(0, s.translateTimeToString(start_time))
        end_time = data[preset]['end_time']
        end_time_entry.delete('0', 'end')
        end_time_entry.insert(0, s.translateTimeToString(end_time))
        pre_time = data[preset]['pre_time']
        pre_time_entry.delete('0', 'end')
        pre_time_entry.insert(0, s.translateTimeToString(pre_time))
        post_time = data[preset]['post_time']
        post_time_entry.delete('0', 'end')
        post_time_entry.insert(0, s.translateTimeToString(post_time))
        song_name.set(data[preset]['song_name'])
        song_link = data[preset]['song_link']
        song_label.bind('<Button-1>', lambda a, m=song_link: openURL(m))
        album_name.set(data[preset]['album_name'])
        album_link = data[preset]['album_link']
        #Start and stop playback immediately to avoid replacing the info
        sp.start_playback(context_uri=album_link, offset={"uri": song_link})
        sp.pause_playback()
        album_label.bind('<Button-1>', lambda a, m=album_link: openURL(m))
        artist_name.set(data[preset]['artist_name'])
        artist_link = data[preset]['artist_link']
        artist_label.bind('<Button-1>', lambda a, m=artist_link: openURL(m))
        loop.set(data[preset]['loop'])
        if end_time <= start_time:
            duration = 0
            duration_entry.config(state=NORMAL)
            duration_entry.delete('0', 'end')
            duration_entry.insert(0, "")
            duration_entry.config(state=DISABLED)
        else:
            duration = end_time - start_time
            duration_entry.config(state=NORMAL)
            duration_entry.delete('0', 'end')
            duration_entry.insert(0, s.translateTimeToString(duration))
            duration_entry.config(state=DISABLED)
        #Select preset code
        selectPreset(preset)

#MARK: Select Preset
def selectPreset(preset):
    global selected_preset
    global preset_list
    global preset_dict
    preset = int(preset)
    preset_dict[preset]['preset_frame'].config(relief=SUNKEN)
    if selected_preset != 0:
        preset_dict[selected_preset]['preset_frame'].config(relief=RAISED)
    selected_preset = preset
    
#MARK: Load from disk
def loadPresetsfromDisk():
    global data
    global preset_num
    try:
        with open(SAVE_PATH) as file:
            data = json.load(file)
        for i in data.keys():
            if i == "0":
                continue
            #TODO: If data[0] becomes setting dict, remove + 1
            preset_num += 1
            createPreset(i, data[i], mode="from_disk")
    except:
        pass
    #Expand preset bar at open
    if settings['show_presets'] == True and preset_num > 0:
        toggleMenu()
        # preset_bar_helper.pack(side='top', expand=True, fill='both')
        # menu_visibility = True
        # menu_btn.config(text="Hide presets")
        # menu_btn.bind('<Enter>', lambda a, m='hide_presets_button': showHint(m))

#MARK: Create Preset
def createPreset(i, data, mode="from_buffer"):
    global preset_num
    global preset_bar
    global cover_img
    global preset_list
    global preset_dict
    i = int(i)
    preset_frame = ttk.Frame(preset_bar, padding="", borderwidth=5, relief=RAISED)
    preset_frame.bind('<Button-1>', lambda a, m=preset_num: loadPreset(m))
    preset_name = data['preset_name']
    song_name = data['song_name']
    start_time = s.translateTimeToString(data['start_time'], return_unit="s", leave_blank=False)
    end_time = s.translateTimeToString(data['end_time'], return_unit="s")
    name_label = ttk.Label(preset_frame, text=preset_name, font=('Segoe UI', 8, 'bold'), width=PRESET_LABEL_WIDTH)
    name_label.bind('<Button-1>', lambda a, m=preset_num: loadPreset(m))
    name_label.grid(row=0, column=0, sticky=W)
    song_label = ttk.Label(preset_frame, text=song_name, font=('Segoe UI', 8), width=PRESET_LABEL_WIDTH)
    song_label.bind('<Button-1>', lambda a, m=preset_num: loadPreset(m))
    song_label.grid(row=1, column=0, sticky=W)
    if end_time == "":
        time = start_time
    else:
        time = start_time + " - " + end_time
    time_label = ttk.Label(preset_frame, text=time, font=('Segoe UI', 8), width=PRESET_LABEL_WIDTH)
    time_label.bind('<Button-1>', lambda a, m=preset_num: loadPreset(m))
    time_label.grid(row=2, column=0, sticky=W)
    preset_frame.pack(fill=X, expand=True)
    if mode == "from_buffer":
        image = resizeImg(cover_img, 60, 60, Image.LANCZOS)
    elif mode == "from_disk":
        image = open(data['img_path'], 'br')
        cover_img = image.read()
        image = Image.open(BytesIO(cover_img))
    album_cover = ImageTk.PhotoImage(image)
    album_cover_box = ttk.Label(preset_frame, image=album_cover)
    album_cover_box.grid(row=0, column=1, rowspan=3, sticky=E)
    album_cover_box.bind('<Button-1>', lambda a, m=preset_num: loadPreset(m))
    #Add to object to avoid the Garbage collector destroying the image
    preset_frame.photo = album_cover
    preset_list.append(preset_frame)
    preset_dict.update({preset_num: {
        "preset_frame": preset_frame,
        "name_label": name_label,
        "song_label": song_label,
        "time_label": time_label,
        "album_cover_box": album_cover_box
        }})

#MARK: Delete Preset
def deletePreset():
    global data
    global selected_preset
    global preset_dict
    global preset_num
    global menu_visibility
    #Do nothing if no preset is selected
    if selected_preset != 0:
        #Presets are 1-indexed
        #Hide preset from preset frame
        preset_dict[selected_preset]['preset_frame'].pack_forget()
        #Move presets in dict and rebind loading
        for i in range(selected_preset, preset_num):
            if preset_num > 1:
                preset_dict.update({i: preset_dict[i+1]})
                data.update({str(i): data[str(i+1)]})
            preset_dict[i]['preset_frame'].bind('<Button-1>', lambda a, m=i: loadPreset(m))
            preset_dict[i]['name_label'].bind('<Button-1>', lambda a, m=i: loadPreset(m))
            preset_dict[i]['song_label'].bind('<Button-1>', lambda a, m=i: loadPreset(m))
            preset_dict[i]['time_label'].bind('<Button-1>', lambda a, m=i: loadPreset(m))
            preset_dict[i]['album_cover_box'].bind('<Button-1>', lambda a, m=i: loadPreset(m))
        #Check if another preset uses the same image
        selected_path = data[str(selected_preset)]['img_path']
        delete_path = True
        paths = []
        #TODO: Rework this into 1 loop
        for i in data.keys():
            if i == str(selected_preset):
                continue
            paths.append(data[i]['img_path'])
        for i in paths:
            if selected_path == i:
                delete_path = False
                break
        #Delete the image
        if path.exists(data[str(selected_preset)]['img_path']) and delete_path:
            remove(data[str(selected_preset)]['img_path'])
        #Remove the last preset
        preset_dict.pop(preset_num)
        data.pop(str(preset_num), None)
        #Write new dict to file
        json.dump(data, open(SAVE_PATH, 'w'), indent=4)
        #Reset preset counters
        preset_num -= 1
        selected_preset = 0
        if preset_num == 0 and menu_visibility:
            toggleMenu()

#MARK: Update Entries
def updateEntries(entry):
    global start_time
    global end_time
    global pre_time
    global post_time
    global duration
    global preset_name
    match entry.casefold():
        case "start_time":
            start_time = t.translate(start_time_entry.get())
            if end_time > start_time:
                duration = end_time - start_time
                duration_entry.config(state=NORMAL)
                duration_entry.delete('0', 'end')
                duration_entry.insert(0, s.translateTimeToString(duration))
                duration_entry.config(state=DISABLED)
        case "end_time":
            end_time = t.translate(end_time_entry.get())
            if end_time <= start_time:
                duration = 0
                duration_entry.config(state=NORMAL)
                duration_entry.delete('0', 'end')
                duration_entry.insert(0, "")
                duration_entry.config(state=DISABLED)
            else:
                duration = end_time - start_time
                duration_entry.config(state=NORMAL)
                duration_entry.delete('0', 'end')
                duration_entry.insert(0, s.translateTimeToString(duration))
                duration_entry.config(state=DISABLED)
        case "pre_time":
            pre_time = t.translate(pre_time_entry.get())
        case "post_time":
            post_time = t.translate(post_time_entry.get())
        # #Update all entries
        # case "preset_name_entry":
        #     preset_name.set(preset_name_entry.get())
        case _:
            start_time = t.translate(start_time_entry.get())
            end_time = t.translate(end_time_entry.get())
            pre_time = t.translate(pre_time_entry.get())
            post_time = t.translate(post_time_entry.get())
            if end_time <= start_time:
                duration = 0
                duration_entry.config(state=NORMAL)
                duration_entry.delete('0', 'end')
                duration_entry.insert(0, "")
                duration_entry.config(state=DISABLED)
            else:
                duration = end_time - start_time
                duration_entry.config(state=NORMAL)
                duration_entry.delete('0', 'end')
                duration_entry.insert(0, s.translateTimeToString(duration))
                duration_entry.config(state=DISABLED)

#MARK: Toggle Menu
def toggleMenu():
    global menu_visibility
    if menu_visibility:
        preset_bar_helper.pack_forget()
        menu_visibility = False
        menu_btn.config(text="Show presets")
        menu_btn.bind('<Enter>', lambda a, m='show_presets_button': showHint(m))
    else:
        preset_bar_helper.pack(side='top', expand=True, fill='both')
        menu_visibility = True
        menu_btn.config(text="Hide presets")
        menu_btn.bind('<Enter>', lambda a, m='hide_presets_button': showHint(m))

#MARK: Setup
#Spotipy config
client_id = getenv('spotipy_client_id')
client_secret = getenv('spotipy_client_secret')
SCOPE = ("user-modify-playback-state", "user-read-currently-playing")
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,client_secret=client_secret,redirect_uri="http://127.0.0.1:3000",scope=SCOPE))

#Threading stuff
service_thread = threading.Thread(target=startService)
info_thread = threading.Thread(target=updateInfo)
service_thread.daemon = True
info_thread.daemon = True
service_thread.start()
info_thread.start()

#MARK: Tkinter
root = Tk()
root.title("Spotify Repeater")
# root.geometry("660x350")
# root.maxsize(height=900)
# root.pack_propagate(False)
root.resizable(False, False)
#root.minsize()
#root.maxsize()
start_time = 0
end_time = 0
pre_time = 0
post_time = 0
duration = 0
stop = False
s = tts(input_unit="s", return_unit="ms", return_format=1)
t = stt(input_format=0, return_unit="s", return_type="float")
first_loop = False
restart_loop = False
#Necessary, since they're on separate threads
start_inf_flag = False
start_loop_flag = False
hint_label_text = ""
prev_album_name = ""
prev_song_name = ""
menu_visibility = False
preset_num = 0
loop = BooleanVar(value=True)
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
selected_preset = 0
preset_list = []
preset_dict = {}

mainframe = ttk.Frame(root, padding="1 1 1 1")
# mainframe.pack_propagate(False)
mainframe.pack(side='left', anchor=NW)

#Hello message
hello_msg = ttk.Label(mainframe, padding="10 5 10 5", text="Set a start and a stop time to loop between, and optionally set dead times at the start\nand end of the loop. Alternatively, you can leave the end time blank to leave the song\nplaying and use the hotkey to keep rewinding to the start time.")
hello_msg.grid(row=0, column=0, rowspan=2, columnspan=7)
hello_msg.bind('<Enter>', lambda a, m="hello_message": showHint(m))

#MARK: Entry
#Start time stuff
start_time_msg = ttk.Label(mainframe, text="Start time").grid(row=2, column=1)
start_time_entry = ttk.Entry(mainframe, width=15, justify=CENTER)
start_time_entry.grid(row=3, column=1)
start_time_entry.bind('<Return>', startEvent)
start_time_entry.bind('<FocusOut>', lambda a, m="start_time": updateEntries(m))
#Empty var in lambda to catch event argument from bind
start_time_entry.bind('<Enter>', lambda a, m="start_entry": showHint(m))

#End time stuff
end_time_msg = ttk.Label(mainframe, text="End time").grid(row=2, column=3)
#Slightly wider because the cover messes it up
end_time_entry = ttk.Entry(mainframe, width=16, justify=CENTER)
end_time_entry.grid(row=3, column=3)
end_time_entry.bind('<Return>', startEvent)
end_time_entry.bind('<Enter>', lambda a, m="end_entry": showHint(m))
end_time_entry.bind('<FocusOut>', lambda a, m="end_time": updateEntries(m))
# end_time_entry.bind('<FocusIn>', (lambda args: duration_entry.delete('0', 'end')))

#Duration stuff
duration_msg = ttk.Label(mainframe, text="Duration").grid(row=2, column=4)
duration_entry = ttk.Entry(mainframe, state=DISABLED, justify=CENTER, width=9)
duration_entry.bind('<Enter>', lambda a, m="duration_entry": showHint(m))
# duration_entry.bind('<FocusIn>', (lambda args: duration_entry.delete('0', 'end')))
# duration_entry.bind('<FocusIn>', (lambda args: end_time_entry.delete('0', 'end')))
duration_entry.grid(row=3, column=4)

#Pre-Time stuff
pre_time_msg = ttk.Label(mainframe, text="Pre-time").grid(row=4, column=1)
pre_time_entry = ttk.Entry(mainframe, width=15, justify=CENTER)
pre_time_entry.grid(row=5, column=1)
pre_time_entry.bind('<Enter>', lambda a, m="pre-time_entry": showHint(m))
pre_time_entry.bind('<FocusOut>', lambda a, m="pre_time": updateEntries(m))

#Post-Time stuffs
post_time_msg = ttk.Label(mainframe, text="Post-time").grid(row=4, column=3)
post_time_entry = ttk.Entry(mainframe, width=15, justify=CENTER)
post_time_entry.grid(row=5, column=3)
post_time_entry.bind('<Enter>', lambda a, m="post-time_entry": showHint(m))
post_time_entry.bind('<FocusOut>', lambda a, m="post_time": updateEntries(m))

#MARK: Buttons
#Copy buttons
copy_start_time_btn = ttk.Button(mainframe, text="C", command=lambda m="start": copyTimestamp(m), width=2) 
copy_start_time_btn.grid(row=3, column=1, sticky=E)
copy_start_time_btn.bind('<Enter>', lambda a, m="copy_button": showHint(m))
copy_end_time_btn = ttk.Button(mainframe, text="C", command=lambda m="end": copyTimestamp(m), width=2) 
copy_end_time_btn.grid(row=3, column=3, sticky=E)
copy_end_time_btn.bind('<Enter>', lambda a, m="copy_button": showHint(m))

#Start button
start_btn = ttk.Button(mainframe, text="Start", command=startEvent)
start_btn.grid(row=2, column=5)
start_btn.bind('<Enter>', lambda a, m="start_button": showHint(m))

#Stop button
stop_btn = ttk.Button(mainframe, text="Stop", command=lambda m=False: stopEvent(m))
stop_btn.grid(row=3, column=5)
stop_btn.bind('<Enter>', lambda a, m="stop_button": showHint(m))

#Hard Stop button
hard_stop_btn = ttk.Button(mainframe, text="Hard Stop", command=lambda m=True: stopEvent(m))
hard_stop_btn.grid(row=4, column=5)
hard_stop_btn.bind('<Enter>', lambda a, m="hard_stop_button": showHint(m))

#Loop check box
loop_check = ttk.Checkbutton(mainframe, state="selected", text="Loop", variable=loop)
loop_check.grid(row=5, column=5)
loop_check.bind('<Enter>', lambda a, m="loop_check": showHint(m))

#Hint label
hint_label = ttk.Label(mainframe, text=HINT_TEXT["hello_message"], padding="0 5 0 5")
hint_label.grid(row=100, column=0, columnspan=7, rowspan=2)

#MARK: Song info
#Create image from buffer
info = sp.current_user_playing_track()
if info == None:
    stock_img = open(NOT_PLAYING_IMG, 'br')
    cover_img = stock_img.read()
    #Need to open as BytesIO for it to work
    image = Image.open(BytesIO(cover_img))
else:
    cover_img = requests.get(info['item']['album']['images'][IMG_QUALITY['mid']]['url']).content
    #NEAREST, BOX, BILINEAR, HAMMING, BICUBIC, LANCZOS
    image = resizeImg(cover_img, 150, 150, Image.LANCZOS)
album_cover = ImageTk.PhotoImage(image)
album_cover_box = ttk.Label(mainframe, image=album_cover)
album_cover_box.grid(row=6, column=0, rowspan=50, columnspan=3, padx=10, pady=(10,0))
album_cover_box.bind('<Button-1>', lambda a, m=album_link: openURL(m))
album_cover_box.bind('<Enter>', lambda a, m="album_cover": showHint(m))
song_label = ttk.Label(mainframe, textvariable=song_name, padding="", font=("Segoe UI", 10, 'bold'), width=PLAYER_LABEL_WIDTH)
song_label.grid(row=10, column=3, columnspan=4, sticky=W, pady=(10,0))
song_label.bind('<Button-1>', lambda a, m=song_link: openURL(m))
song_label.bind('<Enter>', lambda a, m="song_label": showHint(m))
album_label = ttk.Label(mainframe, textvariable=album_name, padding="", font=("Segoe UI", 8), width=PLAYER_LABEL_WIDTH)
album_label.grid(row=11, column=3, columnspan=4, sticky=W)
album_label.bind('<Button-1>', lambda a, m=album_link: openURL(m))
album_label.bind('<Enter>', lambda a, m="album_label": showHint(m))
artist_label = ttk.Label(mainframe, textvariable=artist_name, padding="", font=("Segoe UI", 8), width=PLAYER_LABEL_WIDTH)
artist_label.grid(row=12, column=3, columnspan=4, sticky=W)
artist_label.bind('<Button-1>', lambda a, m=artist_link: openURL(m))
artist_label.bind('<Enter>', lambda a, m="artist_label": showHint(m))

#MARK: Media button stuff
pause_btn = ttk.Button(mainframe, text="O", command=playpause, width=3)
pause_btn.grid(row=14, column=3, padx=(30,0))
pause_btn.bind('<Enter>', lambda a, m="pause_button": showHint(m))
rewind_btn = ttk.Button(mainframe, text="<", command=lambda a=0: sp.seek_track(a), width=3)
rewind_btn.grid(row=14, column=3, padx=(0,30))
rewind_btn.bind('<Enter>', lambda a, m="rewind_button": showHint(m))
prev_btn = ttk.Button(mainframe, text="<<", command=lambda: sp.previous_track(), width=3)
prev_btn.grid(row=14, column=3, sticky=W, padx=(0,0))
prev_btn.bind('<Enter>', lambda a, m="prev_button": showHint(m))
next_btn = ttk.Button(mainframe, text=">>", command=lambda: sp.next_track(), width=3)
next_btn.grid(row=14, column=3, sticky=E, padx=(0,0))
next_btn.bind('<Enter>', lambda a, m="next_button": showHint(m))
clear_fields_btn = ttk.Button(mainframe, text="Clear all", command=clearFields)
clear_fields_btn.grid(row=14, column=5)
clear_fields_btn.bind('<Enter>', lambda a, m="clear_button": showHint(m))

#Preset stuff
save_preset_btn = ttk.Button(mainframe, text="Save preset", command=savePreset)
save_preset_btn.grid(row=15, column=5)
save_preset_btn.bind('<Enter>', lambda a, m="save_preset_button": showHint(m))
delete_preset_btn = ttk.Button(mainframe, text="Delete preset", command=deletePreset)
delete_preset_btn.grid(row=16, column=5)
delete_preset_btn.bind('<Enter>', lambda a, m="delete_preset_button": showHint(m))
preset_name_label = ttk.Label(mainframe, text="Preset name", justify=CENTER)
preset_name_label.grid(row=14, column=4)
preset_name_entry = ttk.Entry(mainframe, textvariable=preset_name, width=15, justify=CENTER)
preset_name_entry.grid(row=15, column=4)
preset_name_entry.bind('<Enter>', lambda a, m="preset_name_entry": showHint(m))
preset_name_entry.bind('<FocusOut>', lambda a, m="preset_name_entry": updateEntries(m))

#MARK: Sidebar stuff
menu_btn = ttk.Button(mainframe, text="Show presets", command=toggleMenu)
menu_btn.grid(row=17, column=5)
menu_btn.bind('<Enter>', lambda a, m='show_presets_button': showHint(m))
preset_bar_helper = ScrolledFrame(root, width=198, height=347, scrollbars='vertical')
# preset_bar_helper.pack(side='top', expand=True, fill='both')
preset_bar_helper.bind_scroll_wheel(root)
preset_bar = preset_bar_helper.display_widget(Frame)
preset_bar_helper.bind('<Enter>', lambda a, m="preset_bar": showHint(m))

loadPresetsfromDisk()

#Focus on start time box when window opens
start_time_entry.focus_force()

#root.update()
#Keep song info updated every second
# update()
root.mainloop()