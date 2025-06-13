> [!WARNING]
> Requires Spotify Premium due to restrictions on the Spotify API.
> As Spotify has placed heavy restrictions on their quota extension requests, you'll have to either host your own app on developer.spotify.com (FREE and easy to do) or send me a mail containing the e-mail address of your spotify account, so that I can give you access.
> You can reach me at nikolaisp3@gmail.com

This is a GUI to set and repeat specific sections of a song in Spotify, e.g. to make it easier to learn a specific section on an instrument.

![GUI](https://github.com/vermilion00/spotify-repeater/blob/main/images/gui.png)

Simply set a start and an end time for the section, and optionally a pre-time (to give you time to get ready to play the section) and a post-time (to give you a breather before the section restarts). You can also press the buttons next to the start time and end time entry fields to copy the currently playing Spotify timestamps.
Saving and recalling your sections by saving them as presets is also possible.

![GUI_with_presets](https://github.com/vermilion00/spotify-repeater/blob/main/images/gui_with_presets.png)

This uses my library [string_to_time](https://github.com/vermilion00/py-stringtotime) for the input. Accepted formats are hh:mm:ss.xxx and \_\_h \_\_m \_\_s \_\_\_ms, with and without spaces.

## Known issues
Opening the app without having Spotify playing can occasionally cause the song information updates to fail. Restarting fixes the issue.
The song information occasionally stops updating. Restarting fixes the issue.