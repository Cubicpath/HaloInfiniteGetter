HaloInfiniteGetter
===============
A simple way to get live Halo data straight from Halo Waypoint.

------------------------------

[![MIT License](https://img.shields.io/github/license/Cubicpath/dyncommands?style=for-the-badge)][license]

[![PyPI](https://img.shields.io/pypi/v/hi-getter?label=PyPI&logo=pypi&style=flat-square)][homepage]
[![Python](https://img.shields.io/pypi/pyversions/hi-getter?label=Python&logo=python&style=flat-square)][python]
[![CPython](https://img.shields.io/pypi/implementation/hi-getter?label=Impl&logo=python&style=flat-square)][python]

------------------------------

**Note: This project is in a public alpha, and as such, many features are not complete.**

### Disclaimer:
_**HaloInfiniteGetter is in no way associated with, endorsed by, or otherwise affiliated with the
Microsoft Corporation, Xbox Game Studios, or 343 Industries. Depending on how you use it, use of this app
may or may not be considered abuse by the aforementioned parties.**_

About:
---------------
HaloInfiniteGetter is a GUI application written using [PyQt6][pyqt] that allows you to easily view data
hosted on [HaloWaypoint] API endpoints.

You can view both Image and Text output, with these results being cached in the cwd under the `hi_data` folder,
to eliminate unnecessary API calls.

How to use:
---------------

### Installation:
- First, install Python 3.10 using [this link][python310]
- Then, open command prompt (Win + R -- type in "cmd.exe") and type `pip install hi_getter`
  - Optionally, to install the latest unstable version, type `pip install git+https://github.com/Cubicpath/HaloInfiniteGetter.git`
- And you are done! To launch the program simply type `py -m hi_getter`

### Authentication:
As this app is unofficial, you must use your own API key, which you can get by logging in to [HaloWaypoint] and getting
data from the authentication headers.

**Note: Auto-renewal of authentication keys is not currently implemented,
so you will only be authenticated for a short amount of time.**

Guide:
- Sign in to www.halowaypoint.com using your xbox account
- Go to a page that requires authentication, like https://www.halowaypoint.com/halo-infinite/progression
- Record network traffic using developer tools
  - On Firefox -- F12 > Then navigate to the "Network" tab.
- Click on a GET request that is getting data from a restricted domain (economy / gamecms-hacs-origin)

![Example Request](https://i.imgur.com/yf6Cs4D.png)
- Under the "Request Headers" right-click the "x-343-authorization-spartan" header and select Copy.
Open the Settings window, Unlock the input by pressing the "Edit Auth Key" button, then paste the copied value.

![Headers](https://i.imgur.com/4QWxO8h.png)
![Settings](https://i.imgur.com/nB1nKCP.png)

- Press the Set button, and you should now be authenticated!

### Searching:

#### Knowing where to search:

![Input Section](https://i.imgur.com/8JPsG5y.png)

An example resource (`Progression/file/Calendars/Seasons/SeasonCalendar.json`) is pre-filled out in the
path input section.

You may omit `progression/file/` and `images/file/` from searches, so long as the file extension of the resource
indicates data or media (ex: json defaults as `progression/file/`, png and jpg defaults as `images/file/`).

#### GET:
Gets the singular resource from the given path and outputs it.

#### SCAN:
Recursively scan a given JSON resource for paths to more resources, ignoring already scanned resources.
This results in caching ALL resources that are referenced by any other resource with some tie to the original
resource path.

Outputs the original resource's data.

### Outputs:
Both the media and the text output can be detached and reattached from the main window.
This allows greater flexibility, like viewing only the image in fullscreen.

![Imgur](https://i.imgur.com/sS9rf4Q.png)

#### Media Output:
The media output shows the currently loaded image to the user, scaled to fit the current window.

It has two settings:
1. Aspect Ratio Mode --- Changes how the aspect-ratio is transformed to fit the window
   - Ignore --- Transform the aspect ratio to meet the output's dimensions
   - Keep (Default) --- Keep the aspect ratio without expanding past the output's dimensions
   - Expanding --- Expand the image's size to keep its aspect ratio
2. Image Transform Mode --- Changes how the image is rendered to a different size
   - Fast (Default) --- Faster
   - Smooth --- May look better in some cases

#### Text Output:
The text output displays any text data loaded by the given path, or an error response from the server.

Path are automatically detected and hyperlinked for ease of use, which allows you to easily browse
multiple paths in succession.

It has one setting:
1. Line Wrap Mode --- Changes how lines are wrapped inside the text output
   - No Wrap --- No line wrapping, use the horizontal scroll wheel instead
   - Widgets (Default) --- Line wrap if a word does not fit the text output's dimensions
   - Fixed Pixel --- Line wrap after every space/seperator
   - Fixed Column --- Line wrap after every character (excluding spaces)

### Themes:
Themes are a way to style already-existing elements (Think CSS). They are held in a directory with their resources
and stylesheet in the same folder level.

#### Theme file structure:
    ../
    │
    ├───[theme_id]/
    │       ├─── [icon1_name].svg
    │       ├─── [icon2_name].svg
    │       ├─── [icon3_name].svg
    │       └─── [theme_id].qss
    │

The current builtin themes are:
- Breeze Dark
- Breeze Light
- Legacy (Default PyQt)

While the current breeze themes are slightly modified versions, you can view the original themes at [BreezeStyleSheets].

[BreezeStyleSheets]: https://github.com/Alexhuszagh/BreezeStyleSheets "BreezeStyleSheets"
[HaloWaypoint]: https://www.halowaypoint.com "Halo Waypoint"
[homepage]: https://pypi.org/project/hi-getter/ "HaloInfiniteGetter PyPI"
[license]: https://choosealicense.com/licenses/mit "MIT License"
[pyqt]: https://pypi.org/project/PyQt6/ "PyQt6"
[python]: https://www.python.org "Python"
[python310]: https://www.python.org/downloads/release/python-3100/ "Python 3.10"
