import requests
import eyed3
import sys
import os
from datetime import datetime
from time import sleep
from colorama import init
from printColor import printError, printInfo, printWarning, printSuccess
import difflib
import argparse

class CheckForExplicit():
    def __init__(self):
        self.taggedSongs = []
        self.errorSongs = []
        self.folder = ""
        self.country = "us"
        if len(sys.argv) == 1:
            self.printHelp()
            return
        self.requestCount = []
        init(autoreset=True)
        self.checkMode = False
        self.exactSearch = True
        self.singleFolder = ""
        self.noRename = False
        self.parser = argparse.ArgumentParser(add_help=True)
        self.parser.add_argument("folder")
        self.parser.add_argument("-m","--manual",action="store_true")
        self.parser.add_argument("-co","--country")
        self.parser.add_argument("-a","--approx", action="store_true")
        self.parser.add_argument("-s","--single")
        self.parser.add_argument("-nr","--no_rename",action="store_true")
        self.parse_args(self.parser.parse_args())
        self.main()

    def parse_args(self,args):
        print(args)
        if args.manual:
            self.checkMode = True
        if args.country is not None:
            self.country = args.country[:2]
        if args.approx:
            self.exactSearch = False
        if args.single is not None:
            self.singleFolder = args.single
        if args.no_rename:
            self.noRename = True
        self.folder = args.folder

    def main(self) -> bool:
        artistID = self.getArtistId(self.folder.split("/")[-1])
        if artistID == -1:
            printError("Artist not found.")
            return False
        albums = self.getAllAlbumsByArtist(artistID)
        if len(albums) == 0:
            printError("Albums not found")
            return False
        if self.singleFolder != "":
            fullpath = self.folder + "/" + self.singleFolder
            self.readFolders(albums,fullpath)
        else:
            for name in os.listdir(self.folder):
                fullpath = self.folder + "/" + name
                self.readFolders(albums,fullpath)
        printInfo("Tagged songs: " + str(len(self.taggedSongs)))
        printInfo("\n".join(self.taggedSongs))
        print("\n---------\n")
        printError("Songs not found: " + str(len(self.errorSongs)))
        printError("\n".join(self.errorSongs))
        return True

    def getArtistId(self, artistName:str) -> int:
        printInfo("Searching for: " + artistName)
        self.handleRateLimit()
        response = requests.get('https://itunes.apple.com/search?term=' + artistName + '&entity=allArtist&attribute=allArtistTerm&country=' + self.country)
        if response.ok:
            o = response.json()
            return o['results'][0]["artistId"]
        else:
            printError("Something went wrong getting the request (Rate limited?)")
            return -1

    def getAllAlbumsByArtist(self, artistId:int) -> list:
        printInfo("Getting all albums")
        self.handleRateLimit()
        response = requests.get('https://itunes.apple.com/lookup?id=' + str(artistId) + '&entity=album&country='+self.country)
        if response.ok:
            o = response.json()
            return o["results"]
        else:
            printError("Something went wrong while loading the album list (Rate limited?)")
            return []

    def readFolders(self, albums:list, fullpath:str) -> bool:
        if os.path.isdir(fullpath):
            name = fullpath.split("/")[-1]
            print("Searching for album: " + name)
            if self.exactSearch:
                results = [a for a in albums if a["wrapperType"] != "artist" and name.lower() == a["collectionName"].lower()]
            else:
                names = [a["collectionName"] for a in albums if a["wrapperType"] != "artist"]
                names = sorted(names,key=lambda x:difflib.SequenceMatcher(None,x,name).ratio())
                results = [a for a in albums if a["wrapperType"] != "artist" and a["collectionName"] == names[-1]]
            if len(results) != 0:
                printInfo(f"Album found: {results[0]['collectionName']}")
                songs = self.getSongs(results[0]["collectionId"])
                self.handleAlbum(fullpath,songs)
            else:
                if self.checkMode == False:
                    printError("Album not found! Run the command again with the -m flag to check options.")
                    self.errorSongs.append(fullpath + "/*")
                else:
                    find = self.tryToFind(name, albums,"collectionName")
                    if len(find) == 0:
                        printError("Album not found")
                        self.errorSongs.append(fullpath + "/*")
                    else:
                        if self.noRename == False:
                            printWarning("Would you like to rename the folder to the correct album name? (y/n)")
                            printWarning(f"{name} -> {find['collectionName']}")
                            choice = input()
                            if choice == "y":
                                oPath = fullpath
                                fullpath = self.folder +"/" + find["collectionName"]
                                os.rename(oPath,fullpath)
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
            try:
                metadata = eyed3.load(fullpath + "/" + file)
                title = metadata.tag.title
            except AttributeError as e:
                printError(f"File {file} is not a audio file, skipping")
                continue
            printInfo("Searching song: "+ title)
            if self.exactSearch:
                result = [a for a in songs if a["wrapperType"] != "collection" and title.lower() == a["trackName"].lower()]
            else:
                names = [a["trackName"] for a in songs if a["wrapperType"] != "collection"]
                names = sorted(names,key=lambda x:difflib.SequenceMatcher(None,x,title).ratio())
                result = [a for a in songs if a["wrapperType"] != "artist" and a["trackName"] == names[-1]]
            if len(result) == 0:
                if self.checkMode == False:
                    printError("Song not found! Run the command again with the -m flag to check options.")
                    self.errorSongs.append(fullpath + "/" + file)
                    continue
                else:
                    find = self.tryToFind(title,songs,"trackName",1)
                    if find != {}:
                        result = [find]
                        if self.noRename == False:
                            printWarning("Would you like to change the title tag to the correct song name? (y/n)")
                            printWarning(f"{title} -> {find['trackName']}")
                            choice = input()
                            if choice == "y":
                                metadata.tag.title = find["trackName"]
                    else:
                        printError("Song not found!")
                        self.errorSongs.append(fullpath + "/" + file)
                        continue
            printInfo(f"Song found: {result[0]['trackName']}")
            explicit = result[0]["trackExplicitness"]
            if len(metadata.tag.user_text_frames) > 0 and "ITUNESADVISORY" in metadata.tag.user_text_frames:
                printWarning("This song is already tagged, skipping...")
                continue
            metadata.tag.user_text_frames.set(str(ratings[explicit]),"ITUNESADVISORY")
            metadata.tag.save()
            printSuccess("Song tagged! " + title + f"({explicit})")
            self.taggedSongs.append(fullpath + "/" + file)


    def tryToFind(self,title:str, collection:list, tag:str, start:int=0) -> dict:
        names = [a[tag] for a in collection[start:] if a["wrapperType"] != "artist"]
        matches = difflib.get_close_matches(title,names,10,0.3)
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
        print("USAGE: explicit.py <Path to Artist Folder> [-m] [-co COUNTRYCODE]")
        print("-m (Optional): Try to suggest options for unknown albums/songs")
        print("-co [COUNTRYCODE] (Optional): Search in the store of the selected country. Default: us")
        print("-a (Optional): Approximation mode. The script will search for similar album/song titles instead of exact matches. Requires less user interaction, but there's higher possibility of false results.")
        print("-s [FOLDERNAME] (Optional): Single mode. Write here the name of a folder inside of the Artist folder and the script will only scan that folder.")
    
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
