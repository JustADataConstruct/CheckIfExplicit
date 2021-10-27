import requests
import eyed3
import sys
import os
from datetime import datetime
from time import sleep

class CheckForExplicit():
    def __init__(self):
        self.taggedSongs = []
        self.errorSongs = []
        if len(sys.argv) == 1:
            self.printHelp()
            return
        self.mode = sys.argv[2] if len(sys.argv) == 3 else "-s"
        self.requestCount = []
        self.main()

    def main(self) -> bool:
        artistID = self.getArtistId(sys.argv[1].split("/")[-1])
        if artistID == -1:
            print("Artist not found.")
            return False
        albums = self.getAllAlbumsByArtist(artistID)
        if len(albums) == 0:
            print("Albums not found")
            return False
        if self.readFolders(albums):
            print("Tagged songs: " + str(len(self.taggedSongs)))
            print("\n".join(self.taggedSongs))
            print("\n---------\n")
            print("Songs not found: " + str(len(self.errorSongs)))
            print("\n".join(self.errorSongs))
        return True

    def getArtistId(self, artistName:str) -> int:
        print("Searching for: " + artistName)
        self.handleRateLimit()
        response = requests.get('https://itunes.apple.com/search?term=' + artistName + '&entity=allArtist&attribute=allArtistTerm')
        if response.ok:
            o = response.json()
            return o['results'][0]["artistId"]
        else:
            print("Something went wrong getting the request (Rate limited?)")
            #TODO: Do something about the rate limit.
            return -1

    def getAllAlbumsByArtist(self, artistId:int) -> list:
        print("Getting all albums")
        self.handleRateLimit()
        response = requests.get('https://itunes.apple.com/lookup?id=' + str(artistId) + '&entity=album')
        if response.ok:
            o = response.json()
            return o["results"]
        else:
            print("Something went wrong while loading the album list (Rate limited?)")
            return []

    def readFolders(self, albums:list) -> bool:
        for name in os.listdir(sys.argv[1]):
            fullpath = sys.argv[1] + "/" + name
            if os.path.isdir(fullpath):
                print("Searching for album: " + name)
                cleanedAlbum = name.split("(")[0].split("[")[0]
                results = [a for a in albums if a["wrapperType"] != "artist" and cleanedAlbum.lower() in a["collectionName"].lower()]
                if len(results) != 0:
                    songs = self.getSongs(results[0]["collectionId"])
                    self.handleAlbum(fullpath,songs)
                    if len(songs) == 0:
                        return False
                else:
                    if self.mode == "-s":
                        print("Album not found!")
                    else:
                        find = self.tryToFind(name, albums,"collectionName")
                        if len(find) == 0:
                            print("Album not found")
                        else:
                            songs = self.getSongs(find["collectionId"])
                            self.handleAlbum(fullpath,songs)
        return True

    def handleAlbum(self,fullpath:str, songs:list):
        ratings = {
            'notExplicit' :0,
            'explicit' :1,
            'cleaned':2,
        }
        for file in os.listdir(fullpath):
            if (os.path.isdir(file)):
                continue
            metadata = eyed3.load(fullpath + "/" + file)
            title = metadata.tag.title
            print("Searching song: "+ title)
            cleaned = title.split("(")[0].split("[")[0] #Get the first part of a song before parenthesis, to maximize chance of finding results.
            result = [a for a in songs if a["wrapperType"] != "collection" and cleaned.lower() in a["trackName"].lower()]
            if len(result) == 0:
                if self.mode == "-s":
                    print("Song not found!")
                    self.errorSongs.append(fullpath + "/" + file)
                    continue
                else:
                    find = self.tryToFind(cleaned,songs,"trackName",1)
                    if find != {}:
                        result = [find]
                    else:
                        print("Song not found!")
                        self.errorSongs.append(fullpath + "/" + file)
                        continue
            explicit = result[0]["trackExplicitness"]
            if len(metadata.tag.user_text_frames) > 0 and "ITUNESADVISORY" in metadata.tag.user_text_frames:
                print("This song is already tagged, skipping...")
                continue
            metadata.tag.user_text_frames.set(str(ratings[explicit]),"ITUNESADVISORY")
            metadata.tag.save()
            print("Song tagged! " + title + f"({explicit}")
            self.taggedSongs.append(fullpath + "/" + file)


    def tryToFind(self,title:str, collection:list, tag:str, start:int=0) -> dict:
        word = title[0:5]
        results = [a for a in collection[start:] if a["wrapperType"] != "artist" and word.lower() in a[tag].lower()]
        print("I couldn't find this item, but I found some suggestions. If you can see the correct element in this list, write its number and press enter, or just press enter to skip.")
        for (i, item) in enumerate(results):
            print(f"[{i}] {item[tag]}")
        choice = input()
        if choice == "" or int(choice) > len(results):
            return {}
        return results[int(choice)]

    def getSongs(self, id:int) -> list:
        print("Getting songs...")
        self.handleRateLimit()
        response = requests.get('https://itunes.apple.com/lookup?id='+str(id)+'&entity=song')
        if response.ok:
            o = response.json()
            return o['results']
        else:
            print("Something went wrong while getting the song list (Rate limited?)")
            return []

    def printHelp(self):
        print("USAGE: explicit.py <Path to Artist Folder> [-s / -c]")
        print("-s (Optional): Skip any unknown albums/songs (default)")
        print("-c (Optional): Try to suggest options for unknown albums/songs")
    
    def handleRateLimit(self):
        completed = False
        while completed == False:
            time = datetime.now()
            self.requestCount[:] = [x for x in self.requestCount if int(round(abs((time - x).total_seconds()) / 60)) < 1]
            if len(self.requestCount) > 19:
                print("iTunes Search API is rate-limited to 20 requests for minute. Trying again in 60 seconds...")
                sleep(60)
            else:
                self.requestCount.append(time)
                completed = True




if __name__  == "__main__":
    CheckForExplicit()
