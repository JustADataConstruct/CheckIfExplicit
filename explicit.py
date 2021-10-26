import requests
import eyed3
import sys
import os

taggedSongs = []
errorSongs = []

def main() -> bool:
    if len(sys.argv) == 1:
        printHelp()
        return False
    artistID = getArtistId(sys.argv[1].split("/")[-1])
    if artistID == -1:
        print("Artist not found.")
        return False
    albums = getAllAlbumsByArtist(artistID)
    if len(albums) == 0:
        print("Albums not found")
        return False
    if readFolders(albums):
        print("Tagged songs: " + str(len(taggedSongs)))
        print("\n".join(taggedSongs))
        print("\n---------\n")
        print("Songs not found: " + str(len(errorSongs)))
        print("\n".join(errorSongs))
    return True

def getArtistId(artistName:str) -> int:
    print("Searching for: " + artistName)
    response = requests.get('https://itunes.apple.com/search?term=' + artistName + '&entity=allArtist&attribute=allArtistTerm')
    if response.ok:
        o = response.json()
        return o['results'][0]["artistId"]
    else:
        print("Something went wrong getting the request (Rate limited?)")
        #TODO: Do something about the rate limit.
        return -1

def getAllAlbumsByArtist(artistId:int) -> list:
    print("Getting all albums")
    response = requests.get('https://itunes.apple.com/lookup?id=' + str(artistId) + '&entity=album')
    if response.ok:
        o = response.json()
        return o["results"]
    else:
        print("Something went wrong while loading the album list (Rate limited?)")
        return []

def readFolders(albums:list) -> bool:
    for name in os.listdir(sys.argv[1]):
        fullpath = sys.argv[1] + "/" + name
        if os.path.isdir(fullpath):
            print("Searching for album: " + name)
            results = [a for a in albums if a["wrapperType"] != "artist" and a["collectionName"].lower() == name.lower()]
            if len(results) != 0:
                songs = getSongs(results[0]["collectionId"])
                if len(songs) == 0:
                    return False
                for file in os.listdir(fullpath):
                    if (os.path.isdir(file)):
                        continue
                    metadata = eyed3.load(fullpath + "/" + file)
                    title = metadata.tag.title
                    print("Searching song: "+ title)
                    result = [a for a in songs if a["wrapperType"] != "collection" and a["trackName"].lower() == title.lower()]
                    if len(result) == 0:
                        print("Song not found!")
                        errorSongs.append(title)
                        continue
                    explicit = result[0]["trackExplicitness"]
                    comment = metadata.tag.comments[0].text
                    metadata.tag.comments.set(comment + " [EXPLICIT: " + explicit + "]")
                    #TODO: Make sure it's not already tagged.
                    metadata.tag.save()
                    taggedSongs.append(title)
    return True
def getSongs(id:int) -> list:
    print("Getting songs...")
    response = requests.get('https://itunes.apple.com/lookup?id='+str(id)+'&entity=song')
    if response.ok:
        o = response.json()
        return o['results']
    else:
        print("Something went wrong while getting the song list (Rate limited?)")
        return []

def printHelp():
    print("USAGE: explicit.py FOLDERPATH")

if __name__  == "__main__":
    main()
