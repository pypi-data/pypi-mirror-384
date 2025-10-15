## High Priority
* Accept iTunes URLs with "tv-season" or "tv-show" instead of "movie" in regex, and raise a specific error if the URL is not a movie saying that series scraping is not supported.
* Parse cue settings, convert them to string and compare them to original string to assure parsing works without issues.
* Add unit-tests (and use extras_require in setup.py to add test dependencies). Example test-cases:
    * Normal playlist
    * AppleTV URL
    * AppleTV URL with multiple playlists
    * Con Air movie (windows reserved)
* Make `load_playlist` method async?
* Add `source` (AppleTV+, etc.) field for media objects.

## Medium Priority
* Standardize language codes by using pre-defined language objects
* Add support for trailer playlists scraping
* Make a general redirect logic, so that when using 3rd party sites (like JustWatch), the scraped URL of a streamer will be "re-entered" and the matching scraper will be used.
* Add a `default-value` parameter for ConfigSetting, with auto-assigned default value if not provided, and remove default_config.
* Move remove-duplicates functionality to while creating the objects, to improve performance.
* Update AppleTV country codes
* When returning media data, return release date instead of just a year.
* When checking for updates, print a dynamic update command matching the installation (pip, pipx, etc.)
* Handle WEBVTT tags (like ruby or rtl) when converting to srt.
* Add an option to pull metadata with scrapers and update TMDB data.
* Allow passing arguments to override settings on the config
* Utilize "Rich" package for colored output and progress bar.

## Low Priority
* Add pre-commit config https://pre-commit.com/#2-add-a-pre-commit-configuration
* Remove `mergedeep` dependency and replace it with native code
* Add support for yaml / json config files.
* Add option to remove leading zeros from timestamps in WEBVTT subtitles (example: 12:26.500 instead of 00:12:26.500)
* Cache scraped playlists
