## CheckIfExplicit
A Python script to check if a particular song, adequately tagged, is marked as "Explicit" on Apple's iTunes database, using [Apple's public APIs](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/index.html#//apple_ref/doc/uid/TP40017632-CH3-SW1) and the python [Requests](https://docs.python-requests.org/en/latest/) library to check and then the [eyed3](https://github.com/nicfit/eyeD3) library to write this in the file itself.

### Install
- Download or clone the repository
- Run `pip install -r requeriments.txt` to install the required libraries
- Run `explicit.py <FOLDER PATH> [-m] [-co COUNTRYCODE] [-a] [-s FOLDERNAME] [-nr]`

### Docker
If you have Docker and Docker-Compose in your system, you can use the containerized script without installing it in your system.
- Download or clone the repository.
- Edit the last line of `docker-compose.yml` to indicate the path of the folder that contains all of your Artist folders (example: `'./music:/music'`)
- Run `docker-compose run --rm checkexplicit <ARTIST PATH> [FLAGS]` (example: `docker-compose run --rm checkexplicit ./music/Metallica -m -nr`)

### Flags
`-m`: **(Optional)** Manual mode. If the script can't do an automatic match, it will ask the user to select the closest option from a list.

`-co COUNTRYCODE` **(Optional)** Country code from the store the user wishes to query. **Default:** US

`-a` **(Optional)** Approximate search. When searching album/song names, the script will try to match with the closest option it can find instead of trying to do an exact match.

`-s FOLDERNAME` **(Optional)** Single Album Search. If the user writes here, inside quotation marks, the name of a folder that is inside of the Artist folder as indicated on the first argument, the script will only scan that folder.

`-nr` **(Optional)** No Rename. By default, if the script can't find an automatic match and the user has selected an option from the suggestion list, the script will offer to rename the Album/Song to match Apple's data. This flag will skip this question.

### Usage

The script expects as its first argument a path to a folder named as an Artist, containing one or more folders inside names as an Album, containing one or more audio files inside.

`Artist -> Album(s) -> Song(s)`

When started, the script will read the name of the root folder and will make a first request to the iTunes Search API to request the `artistID` field. If the artist exists on the database, the script will then make a second request to get all albums by the artist.

With the list of albums in memory, the script will look at each folder inside of the Artist folder, get its name, and try to find an object inside of the requested albums list whose `collectionName` tag matches the name of the folder.

**By default**, if the script can't get a match, it will throw a warning and move into the next folder if there's one. This behavior can be changed  by appending the `-m` flag to the initial command; in that case, the script will show some similar results and let the user manually select if one of them is the album they were trying to search.

The user can also use the `-a` flag to do an approximated search. In this case, instead of trying to get an exact match, the script will try to get the closest match possible. While this requires less user interaction, it also comes with a greater chance of false results, and should be used with caution.

If there's no match, but the user knows the album/song is available on Apple Music, they can change the country's store the script is changing with the `-co` flag. By default, the script checks the US store, but it supports any [two letter country code.](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)

Once there's a match, either automatic or manual, the script will make a new request to the API to download the list of songs of that album.

Then, for each file inside of the Album folder, the script will use `eyed3` to load the file metadata. It will then try to match the file's `Title` tag with the `trackName` tag in the requested song list. As with the album, if there's no automatic match, the song will be skipped, and this behavior can be changed with the `-m` and `-a` flags.

After matching, the script will check the `trackExplicitness` tag of the song (either `notExplicit`, `explicit` or `cleaned`) and write a `ITUNESADVISORY` tag in the audio file with a number related to the result (`0`,`1` or `2`).

This process will repeat until every file of every folder inside the root folder has been scanned. At the end, the script will show how many songs were tagged (automatically or manually) and how many couldn't be matched with iTunes' database.

### Rate limit
iTunes' Search API is rate-limited to 20 requests per minute. To respect this, the script tracks the timestamp of every request it makes. If the rate-limit is reached, the script will notify the user and halt operation for 60 seconds.

### Why?

This script is useful in very specific circustances. In most cases, a standard file tagger with compatibility with the iTunes API will allow the user to request the `trackExplicitness` track along the rest of the metadata. However, in the case of an user with an existing music organization system wanting to get this tag but not to touch any other metadata, this scripts brings a quick and dirty way of doing exactly that.

It also served for me as a way of practicing my quite rusty Python and to experiment with both the `requests` and `eye3d` libraries.

### Contributing
Any pull requests are welcome!