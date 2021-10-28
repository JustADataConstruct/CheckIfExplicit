import requests
import eyed3
import sys
import os
from datetime import datetime
from time import sleep
from colorama import init
from printColor import printError, printInfo, printWarning, printSuccess
import difflib

class CheckForExplicit():
    def __init__(self):
        self.taggedSongs = []
        self.errorSongs = []
        if len(sys.argv) == 1:
            self.printHelp()
            return
        self.mode = sys.argv[2] if len(sys.argv) == 3 else "-s"
        self.requestCount = []
        init(autoreset=True)
        self.main()

    def main(self) -> bool:
        artistID = self.getArtistId(sys.argv[1].split("/")[-1])
        if artistID == -1:
            printError("Artist not found.")
            return False
        albums = self.getAllAlbumsByArtist(artistID)
        if len(albums) == 0:
            printError("Albums not found")
            return False
        if self.readFolders(albums):
            printInfo("Tagged songs: " + str(len(self.taggedSongs)))
            printInfo("\n".join(self.taggedSongs))
            print("\n---------\n")
            printError("Songs not found: " + str(len(self.errorSongs)))
            printError("\n".join(self.errorSongs))
        return True

    def getArtistId(self, artistName:str) -> int:
        printInfo("Searching for: " + artistName)
        self.handleRateLimit()
        response = requests.get('https://itunes.apple.com/search?term=' + artistName + '&entity=allArtist&attribute=allArtistTerm')
        if response.ok:
            o = response.json()
            return o['results'][0]["artistId"]
        else:
            printError("Something went wrong getting the request (Rate limited?)")
            return -1

    def getAllAlbumsByArtist(self, artistId:int) -> list:
        printInfo("Getting all albums")
        self.handleRateLimit()
        response = requests.get('https://itunes.apple.com/lookup?id=' + str(artistId) + '&entity=album')
        if response.ok:
            o = response.json()
            return o["results"]
        else:
            printError("Something went wrong while loading the album list (Rate limited?)")
            return []

    def readFolders(self, albums:list) -> bool:
        for name in os.listdir(sys.argv[1]):
            fullpath = sys.argv[1] + "/" + name
            if os.path.isdir(fullpath):
                print("Searching for album: " + name)
                results = [a for a in albums if a["wrapperType"] != "artist" and name.lower() == a["collectionName"].lower()]
                if len(results) != 0:
                    songs = self.getSongs(results[0]["collectionId"])
                    self.handleAlbum(fullpath,songs)
                    if len(songs) == 0:
                        return False
                else:
                    if self.mode == "-s":
                        printError("Album not found! Run the command again with the -c flag to check options.")
                        self.errorSongs.append(fullpath + "/*")
                    else:
                        find = self.tryToFind(name, albums,"collectionName")
                        if len(find) == 0:
                            printError("Album not found")
                            self.errorSongs.append(fullpath + "/*")
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
            printInfo("Searching song: "+ title)
            result = [a for a in songs if a["wrapperType"] != "collection" and title.lower() == a["trackName"].lower()]
            if len(result) == 0:
                if self.mode == "-s":
                    printError("Song not found! Run the command again with the -c flag to check options.")
                    self.errorSongs.append(fullpath + "/" + file)
                    continue
                else:
                    find = self.tryToFind(title,songs,"trackName",1)
                    if find != {}:
                        result = [find]
                    else:
                        printError("Song not found!")
                        self.errorSongs.append(fullpath + "/" + file)
                        continue
            explicit = result[0]["trackExplicitness"]
            if len(metadata.tag.user_text_frames) > 0 and "ITUNESADVISORY" in metadata.tag.user_text_frames:
                printWarning("This song is already tagged, skipping...")
                continue
            metadata.tag.user_text_frames.set(str(ratings[explicit]),"ITUNESADVISORY")
            metadata.tag.save()
            printSuccess("Song tagged! " + title + f"({explicit}")
            self.taggedSongs.append(fullpath + "/" + file)


    def tryToFind(self,title:str, collection:list, tag:str, start:int=0) -> dict:
        names = [a[tag] for a in collection[start:] if a["wrapperType"] != "artist"]
        matches = difflib.get_close_matches(title,names,5)
        if len(matches) == 0:
            return {}
        printWarning("I couldn't find this item, but I found some suggestions. If you can see the correct element in this list, write its number and press enter, or just press enter to skip.")
        for (i, item) in enumerate(matches):
            print(f"[{i}] {item}")
        choice = input()
        if choice == "" or int(choice) > len(matches):
            return {}
        results = [a for a in collection[start:] if a["wrapperType"] != "artist" and a[tag] == matches[int(choice)]]
        return results[0]

    def getSongs(self, id:int) -> list:
        printInfo("Getting songs...")
        self.handleRateLimit()
        response = requests.get('https://itunes.apple.com/lookup?id='+str(id)+'&entity=song')
        if response.ok:
            o = response.json()
            return o['results']
        else:
            printError("Something went wrong while getting the song list (Rate limited?)")
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
                printWarning("iTunes Search API is rate-limited to 20 requests for minute. Trying again in 60 seconds...")
                sleep(60)
            else:
                self.requestCount.append(time)
                completed = True




if __name__  == "__main__":
    CheckForExplicit()
