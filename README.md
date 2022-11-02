HaloInfiniteGetter
===============
A simple way to get live Halo data straight from Halo Waypoint.

------------------------------

[![MIT License](https://img.shields.io/github/license/Cubicpath/HaloInfiniteGetter?style=for-the-badge)][license]

[![PyPI](https://img.shields.io/pypi/v/hi-getter?label=PyPI&logo=pypi&style=flat-square)][homepage]
[![Python](https://img.shields.io/pypi/pyversions/hi-getter?label=Python&logo=python&style=flat-square)][python]
[![CPython](https://img.shields.io/pypi/implementation/hi-getter?label=Impl&logo=python&style=flat-square)][python]

------------------------------

**Note: This project is in a public alpha, and as such, many features are not complete.**

### Disclaimer:
_**HaloInfiniteGetter is in no way associated with, endorsed by, or otherwise affiliated with the
Microsoft Corporation, Xbox Game Studios, or 343 Industries. Depending on how you use it, use of this app
may or may not be considered abuse by the aforementioned parties.**_

### Table of Contents
- [Changelog][changelog_github]
- [License][license_github]
- [Disclaimer](#disclaimer)
- [About](#about)
- [How to Use](#how-to-use)
     - [Installation](#installation)
     - [Authentication](#authentication)
     - [Searching](#searching)
          - [Knowing Where to Search](#knowing-where-to-search)
          - [GET](#get)
          - [SCAN](#scan)
     - [Cache Explorer](#cache-explorer)
     - [Importing and Exporting Cached Requests](#importing-and-exporting-cached-requests)
     - [Outputs](#outputs)
          - [Media Output](#media-output)
          - [Text Output](#text-output)
     - [Themes](#themes)
          - [Theme File Structure](#theme-file-structure)


About:
---------------
HaloInfiniteGetter is a GUI application written using [Qt for Python][PySide] that allows you to easily view data
hosted on [HaloWaypoint] API endpoints.

You can view both Image and Text output, with these results being cached in the user's `.cache/hi_getter/cached_requests` directory,
to eliminate unnecessary API calls.

How to Use:
---------------

### Installation:
- First, install Python 3.10 using [this link][python310]
- Then, open command prompt (Win + R -- type in "cmd") and type `pip install hi_getter`
  - Optionally, to install the latest unstable version, type `pip install git+https://github.com/Cubicpath/HaloInfiniteGetter.git`
- And you are done! To launch the program simply type `hi_getter`
  - Once launched, you can create a desktop shortcut by using the `Create Desktop Shortcut` tool
under the `Tools` context menu

### Authentication:
As this app is unofficial, you must use your own API key, which you can get by logging in to [HaloWaypoint] and either getting
data from the authentication headers, or from the website's cookies.

Guide:
- Sign in to www.halowaypoint.com using your xbox account
- Navigate to the Cookies for www.halowaypoint.com
  - On Firefox -- F12 > Move to the "Storage" tab > Under "Cookies" select https://www.halowaypoint.com
- Double-click the "wpauth" cookie value and copy with CTRL + C
- Open the Settings window, unlock the input by pressing the "Edit Auth Key" button, then paste the copied value.

![Settings](https://i.imgur.com/79t0MTpl.png)

- Press the Set button, and you should now be authenticated!


### Searching:

#### Knowing Where to Search:

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

### Cache Explorer:
You can view all cached files using the Cache Explorer, which is on the left-hand side of the main window.

It has 1 setting:
1. **Icon Mode** --- Changes how the file/folder icons are rendered
   - **No Icons** --- Removes all icons in the view
   - **Default (Default)** --- Renders icons normally (like explorer)
   - **Preview Images** --- Use image previews as icons for images.
      This can use upwards of ~2GB of memory if you have a lot of image files

Context Menu actions:
- **Open in View** --- Open the cached file's contents in one of the output views
- **Open in Default App** --- Open the cached file in its extension's default app
- **Folding**
  - **Expand** --- Expand the selected directory
  - **Expand Recursively** --- Expand this directory and any subdirectories
  - **Expand All** --- Expand all directories
  - **Collapse** --- Collapse the selected directory
  - **Collapse All** --- Collapse all directories
- **Copy Full Path** --- Copy the cached file's path
- **Copy Endpoint Path** --- Copy the path, translated into it's associated endpoint
- **Copy File Contents** --- Copy the contents of the file onto your clipboard.

![Cache Explorer](https://i.imgur.com/KbdOE95l.png)


### Importing and Exporting Cached Requests
You can use the `File` context menu to easily import and export archive files containing cached requests.
Once imported, you can view the data in the [Cache Explorer](#cache-explorer).

Supported archive types are:
- 7Zip Archives (`*.7z`)
- ZIP Files (`*.zip` & `*.piz`)
- TAR Files (`*.tar`, `*.tar.gz`, `*.tgz`, `*.tar.bz2`, `*.tbz2`, `*.tar.xz`, `*.txz`)
   - `gzip`, `bzip2`, and `xz` are the supported compression algorithms


### Outputs:
Both the media and the text output can be detached and reattached from the main window.
This allows greater flexibility, like viewing only the image in fullscreen.

![Imgur](https://i.imgur.com/n82Any7l.png)

#### Media Output:
The media output shows the currently loaded image to the user, scaled to fit the current window.

It has two settings:
1. **Aspect Ratio Mode** --- Changes how the aspect-ratio is transformed to fit the window
   - **Ignore** --- Transform the aspect ratio to meet the output's dimensions
   - **Keep (Default)** --- Keep the aspect ratio without expanding past the output's dimensions
   - **Expanding** --- Expand the image's size to keep its aspect ratio
2. **Image Transform Mode** --- Changes how the image is rendered to a different size
   - **Fast (Default)** --- Faster, looks more jagged
   - **Smooth** --- Smooths edges, looks better in some cases

#### Text Output:
The text output displays any text data loaded by the given path, or an error response from the server.

Path are automatically detected and hyperlinked for ease of use, which allows you to easily browse
multiple paths in succession.

It has one setting:
1. **Line Wrap Mode** --- Changes how lines are wrapped inside the text output
   - **No Wrap** --- No line wrapping, use the horizontal scroll wheel instead
   - **Widgets (Default)** --- Line wrap if a word does not fit the text output's dimensions
   - **Fixed Pixel** --- Line wrap after every space/seperator
   - **Fixed Column** --- Line wrap after every character (excluding spaces)

### Themes:
Themes are a way to style already-existing elements (Think CSS). They are held in a directory with their resources
and stylesheet in the same folder level.

#### Theme File Structure:
    ../
    │
    ├───[theme_id]/
    │       ├─── [icon1_name].svg
    │       ├─── [icon2_name].svg
    │       ├─── [icon3_name].svg
    │       └─── stylesheet.qss
    │

The current builtin themes are:
- `Breeze Dark`
- `Breeze Light`
- `Legacy (Default Qt)`

While the current breeze themes are slightly modified versions, you can view the original themes at [BreezeStyleSheets].

[BreezeStyleSheets]: https://github.com/Alexhuszagh/BreezeStyleSheets "BreezeStyleSheets"
[changelog_github]: https://github.com/Cubicpath/HaloInfiniteGetter/blob/master/CHANGELOG.md "Changelog"
[HaloWaypoint]: https://www.halowaypoint.com "Halo Waypoint"
[homepage]: https://pypi.org/project/hi-getter/ "HaloInfiniteGetter PyPI"
[license]: https://choosealicense.com/licenses/mit "MIT License"
[license_github]: https://github.com/Cubicpath/HaloInfiniteGetter/blob/master/LICENSE "MIT License"
[PySide]: https://pypi.org/project/PySide6/ "PySide6"
[python]: https://www.python.org "Python"
[python310]: https://www.python.org/downloads/release/python-3100/ "Python 3.10"
