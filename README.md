## CheckIfExplicit
A Python script to check if a particular song, adequately tagged, is marked as "Explicit" on Apple's iTunes database, using Apple's public APIs and the python Requests library to check and then the eyed3 library to write this in the file itself.

WIP.

The script expects as an argument a path to a folder with folders inside. The script will use the name of the root folder as the Artist Name and make two requests to the iTunes API to get the Artist ID and then the list of albums.

Then, for each folder inside the root folder, the script will get the name of the folder as the Album Name and try to find it on the saved request. If it does find it, it will make a new request for the list of songs from that album.

it will then iterate over each audio file inside the folder and read its metadata to get its Title tag and search it inside the requested song list, and if found, will check if the requested metadata has a trackExplicitness tag.

If it does, the script will write the content of the tag as a comment on the audio file and move to the next file.