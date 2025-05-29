# Requires Spotify Premium!
This is a GUI to set and repeat specific sections of a song in Spotify, e.g. to make it easier to learn a specific section on an instrument.

![GUI](https://github.com/vermilion00/spotify-repeater.git/blob/main/images/gui.png?raw=true)

Simply set a start and an end time for the section, and optionally a pre-time (to give you time to get ready to play the section) and a post-time (to give you a breather before the section restarts). You can also press the buttons next to the start time and end time entry fields to copy the currently playing Spotify timestamps.
You can also save and recall your sections by saving them as presets.

![GUI_with_presets](https://github.com/vermilion00/spotify-repeater.git/blob/main/images/gui_with_presets.png?raw=true)

This uses my library [string_to_time](https://github.com/vermilion00/py-stringtotime) for the input. Accepted formats are hh:mm:ss.xxx and \_\_h \_\_m \_\_s \_\_\_ms, with and without spaces.
> [!WARNING]
> Make sure that Spotify is playing before starting this program up!


