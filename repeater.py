#Add option for x amount of time before repeat
#Add option for x amount of time before first play
#Add option to toggle auto repeat
#Set shortcut key to play from start time
#Add hotkeys to skip, scrub, load preset etc
#Add midi support, set a midi command to play/pause/rewind etc
#If no end is selected, let music continue
#Allow entering duration instead of stop time (just because)
#Add button to copy spotify timestamp to field
#Display currently playing track with pic
#Save presets with track, pic, and timeframe

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from string_to_time import StringToTime as t
import time

t = t(return_unit="s", format=0, return_type="float")
#TODO: Remove these (Environment Variables)
client_id = "99a806166c72479f95636439a05cf4ec"
client_secret = "c40c82142d594cdea4b922b4faff8a38"

scope = ("user-modify-playback-state", "user-read-currently-playing")
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,client_secret=client_secret,redirect_uri="http://127.0.0.1:3000",scope=scope))

loop = True

#print(sp.current_user_playing_track())

#time.time() gives float in [s]
set_start_time = t.translate(input("Start time: "))
set_end_time = t.translate(input("End time: "))
while set_end_time <= set_start_time and set_end_time != 0:
    print("Error: End time needs to be higher than the start time!")
    set_end_time = t.translate(input("Set a new end time: "))
duration = set_end_time - set_start_time #in s
pre_time = t.translate(input("Pre-Time: "))
post_time = t.translate(input("Post-Time: "))
time.sleep(pre_time) #Sleep in [s]

#Pause Music at the end time
if set_end_time > 0:
    while True:
        try:
            #While the rest is in s, this requires ms
            sp.seek_track(int(set_start_time * 1000))
        except:
            print("Start time is set to an invalid value")
        #Trying to start playback when already playing gives an error
        try:
            sp.start_playback()
        except:
            pass
        #Check if this is accurate enough - if not, sleep for 1 less second and empty loop until the time is right
        time.sleep(duration)
        if loop and post_time > 0:
            sp.pause_playback()
            time.sleep(post_time)
        elif not loop:
            sp.pause_playback()
            test = input("Restart?")

#Let music play further until restart hotkey is hit            
else:
    while True:
        try:
            #While the rest is in s, this requires ms
            sp.seek_track(int(set_start_time * 1000))
        except:
            print("Start time is set to an invalid value")
        #Trying to start playback when already playing gives an error
        try:
            sp.start_playback()
        except:
            pass
        #Press hotkey to restart
        test = input()