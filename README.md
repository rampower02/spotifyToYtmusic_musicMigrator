# spotifyToYtmusic_musicMigrator
INTENDED USE
The main script can copy Spotify playlists and favorite songs as playlists on YouTube music.
It's meant to be used (on a windows machine) to migrate form using a moddedd version of Spotify to Youtube Revanced, which you can find on google (for listening to music on your phone. 
On pc I use SpotX).

As the YTmusic search isn't optimized, after the program finishes to copy any playlist it will create a text file in the 'mismatch' folder named after the playlist, where you will find which songs it was unable to copy and you can add manually to your playlists. It still creates some undetected mismatch, so you may have to modify some more songs manually.
You can also access transfer mismatch list files through the main program.

THIS IS A BETA VERSION and is intended for being distributed only within my personal friend circle.  

SETUP
You firstly need to get Youtube revanced and YTMusic revanced running. You will also need a premium-ish version of Spotify running. Since this program uses APIs you will need a premium account for both Youtube and Spotify. When I firstly used this automation I had an Echo version of Spotify and it worked for me.
In order to use the musicMigrator app you need to run "1st step - startSetup.bat" ("Open with Powershell" - it's recommended you run it as admin). This file executes all that's needed. Make sure to have all files downloaded in the same folder.
The setup file will create some folders and files, you can manually access transfer mismatch list files in the mismatch folder.
If you haven't installed revanced manager on your phone, you can find APKs for all the followings app on google. You'll need Revanced Manager, MicroG, and ReVanced YouTube Music.

MAIN PROGRAM EXECUTION
At the end of the setup, the main program should automatically start, 
but you can always start it by opening 'musicMigrator.bat'

ADDITIONAL INFO
(This is my first public project, so it's pretty rough and has some limitations.)
The program uses a terminal-based interface.
Liked songs from Spotify are saved on Youtube music in a new playlist.

DISCLAIMER
This is the beta version. I've tested the program and I can confirm it's fully operational on my machine up to 07/04/2025 01:43, but as this project isn't intended for large distribution, it's use is temporary, and I'm by no means a professional. if you find this on github and can be of use to you, go ahead and try it, but know it could not work.	