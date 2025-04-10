import os
import re
import json
import time
import spotipy
import winsound
from datetime import date
from difflib import SequenceMatcher
from spotipy.oauth2 import SpotifyOAuth
from ytmusicapi import YTMusic, OAuthCredentials
from ytmusicapi.exceptions import YTMusicServerError

CONFIG_DIR = "config"
MISMATCH_DIR = "mismatch_files"
freq = 1500  # Beep frequency used to notify the user when a process is complete
tempo = 1000  # Beep time
yt = None #variabili globali che rappresentano l'uso delle api di spotify e ytmusic
sp = None

def ensure_config_dir():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

def UninstallAll():  # CURRENTLY NOT SUPPORTED
    print("Caution, this process will uninstall resources needed to run this program. Do you wish to proceed? (y/n)")
    confirm = input().strip().lower()
    if confirm == 'y':
        print("Uninstall process not yet supported.")  # Placeholder message
        return True
    return False

def isYTmusicAPI_connected():
    global yt
    try:
        user_info = yt.get_authenticated_user()
        if user_info:
            print(f"YTMusic is already connected: {user_info['user']['name']}")
            return True
        else:
            return False
    except Exception as e:
        #print(f"Error checking YTMusic connection: {e}")
        return False
        
def connectToYTmusicAPI():
    global yt
    try:
        ensure_config_dir()
        with open(os.path.join(CONFIG_DIR, "ytmusic_auth.json"), "r") as file:
            credentials = json.load(file)
        YT_CLIENT_ID = credentials.get("client_id")
        YT_CLIENT_SECRET = credentials.get("client_secret")
        if not YT_CLIENT_ID or not YT_CLIENT_SECRET:
            raise ValueError("\nClient ID or Secret missing in ytmusic_auth.json file.")
        yt = YTMusic(os.path.join(CONFIG_DIR, "oauth.json"), oauth_credentials=OAuthCredentials(client_id=YT_CLIENT_ID, client_secret=YT_CLIENT_SECRET))
        account_info = yt.get_account_info()
        account_name = account_info.get("accountName", "Unknown")
        if account_name:
            print("YTMusic connected successfully to:", account_name)
    except Exception as e:
        raise RuntimeError(f"\nError while trying to connect to YTMusicAPI: {e}")

def isSpotifyAPI_connected():
    global sp
    try:
        user = sp.current_user()
        print("Spotify is already connected:", user["display_name"])
        return True
    except spotipy.SpotifyException:
        return False
    except Exception as e:
        #print(f"Error checking Spotify connection: {e}")
        return False

def connectToSpotifyAPI():
    global sp
    try:
        ensure_config_dir()
        with open(os.path.join(CONFIG_DIR, "spotify_auth.json"), "r") as file:
            credentials = json.load(file)
        SPOTIFY_CLIENT_ID = credentials.get("client_id")
        SPOTIFY_CLIENT_SECRET = credentials.get("client_secret")
        if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
            raise ValueError("\nClient ID or Secret missing in spotify_auth.json file.")
        auth_manager = SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri="http://127.0.0.1:8888/callback",
            scope="user-library-read playlist-read-private playlist-read-collaborative",
            cache_path=os.path.join(CONFIG_DIR, "spotify_token.json")
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        user = sp.current_user()
        if user:
            print("Spotify connected successfully to:", user["display_name"])
    except Exception as e:
        raise RuntimeError(f"\nError while trying to connect to SpotifyAPI: {e}")
    
def getPlaylists(source):
    global sp, yt
    playlists = []
    offset = 0
    if source == "Spotify":
        try:
            user_id = sp.current_user()["id"]  # Ottiene l'ID dell'utente autenticato
            while True:
                response = sp.user_playlists(user_id, offset=offset)
                if not response["items"]:
                    break
                for playlist in response["items"]:
                    playlist_name = playlist["name"]
                    track_count = playlist["tracks"]["total"]
                    playlist_id = playlist["id"]
                    playlists.append((playlist_name, track_count, playlist_id))
                offset += len(response["items"])  # Continua a prendere le playlist in caso siano molte
        except Exception as e:
            print(f"\nError while retrieving playlists from Spotify: {e}")
    elif source == "Ytmusic":
        user_playlists = yt.get_library_playlists()
        for playlist in user_playlists:
            playlist_name = playlist.get('title', 'Unknown')
            track_count = playlist.get('count', '0')
            playlist_id = playlist.get('playlistId', None)
            if playlist_id:
                playlists.append((playlist_name, track_count, playlist_id))
    return playlists

def get_playlist_tracks(source, playlist_id):
    global sp, yt
    songs = []
    offset = 0
    if source == "Spotify":
        try:
            while True:
                playlist = sp.playlist_tracks(playlist_id, limit=100, offset=offset)
                if not playlist["items"]:
                    break
                songs.extend([(track["track"]["name"], track["track"]["artists"][0]["name"], track["track"]["id"]) for track in playlist["items"]])
                offset += 100
            return songs
        except Exception as e:
            print(f"\nError while retrieving playlist tracks: {e}")
            return None
    elif source == "YTmusic":
        print("This process isn't supported yet.")
        return None

def transferPlaylist(sp_playlist_id, playlist_name, source, destination):
    global yt, sp
    file_directory = get_mismatch_directory(playlist_name)
    if source == "Youtube":
        print("This process isn't supported yet.")
    elif source == "Spotify":
        check_and_delete_YTplaylists(playlist_name, False)
        print(f"Fetching songs from {playlist_name}...")
        songs = get_playlist_tracks(source, sp_playlist_id)
        print(f"Beginning transfer of {len(songs)} songs to {playlist_name} from {source} to {destination}.")
        print("\nThis process runs in the background. You may minimize this app.\n")
        yt_playlist_id = yt.create_playlist(f"{playlist_name}", "Automatic copy from f{source}")
        error_counter = 0
        for idx, song in enumerate(songs, 1):
            name, artist, song_id = song
            try:
                search_query = f"{name} {artist}"
                search_results = yt.search(search_query, filter="songs", limit=10, ignore_spelling=True)
                if not search_results: 
                    raise ValueError("No search results found")
                better_result = find_best_match(song, search_results)
                if not better_result or 'videoId' not in better_result: 
                    raise ValueError(f"Mismatch: song not found on YouTube Music.")
                yt.add_playlist_items(yt_playlist_id, [better_result['videoId']])
                video_title = better_result.get('title', 'Unknown')
                video_artist = ', '.join([a['name'] for a in better_result.get('artists', [])])
                print(f"[{idx}/{len(songs)}] Adding: {video_title} - {video_artist}")
            except Exception as e:
                with open(file_directory, "a", encoding="utf-8") as file:
                    if error_counter == 0:
                        file.write(f"Songs not added automatically from playlist '{playlist_name}' to YTmusic:\n")
                    file.write(f"{name} - {artist}: {e}\n")
                print(f"Error while adding: {name} - {artist}: {e}")
                error_counter += 1
        
        winsound.Beep(freq, tempo)
        print(f"Transfer completed. Check {file_directory} for any errors. ({error_counter} errors)")
        return

def getSPFavoriteTracks():
    global sp
    favTracks = []
    try:
        offset = 0
        while True:
            results = sp.current_user_saved_tracks(limit=50, offset=offset)
            for item in results['items']:
                track_name = item['track']['name']
                artist_name = item['track']['artists'][0]['name']
                track_id = item['track']['id']
                favTracks.append((track_name, artist_name, track_id))
            if len(results['items']) < 50:
                break
            offset += 50
        return favTracks
    except Exception as e:
        print(f"\nError while retrieving favorite tracks: {e}")
        return None

def copyFavSongs_toYT_playlist(favTracks):
    global yt
    playlist_title = f"Favorite songs from Spotify ({date.today().strftime('%d/%m/%Y')})"
    file_directory = get_mismatch_directory(None)
    try:
        yt_playlist_id = yt.create_playlist(title=playlist_title, description="Automatic transfer from Spotify")
    except Exception as e:
        print(f"\nError creating playlist: {e}")
        return
    print(f"\nStarting transfer of {len(favTracks)} songs to playlist: '{playlist_title}'")
    print("--------------------------------------------------")
    error_counter = 0
    success_counter = 0
    processed_tracks = 0
    for idx, favTrack in enumerate(favTracks, 1):
        track_name, artist_name, track_id = favTrack
        processed_tracks += 1
        try:
            search_query = f"{track_name} {artist_name}"
            search_results = yt.search(search_query, filter="songs", limit=10, ignore_spelling=True)
            if not search_results:
                raise ValueError("No search results found")
            better_result = find_best_match(favTrack, search_results)
            if not better_result or 'videoId' not in better_result:
                raise ValueError("No valid match found in search results")
            video_title = better_result.get('title', 'Unknown')
            video_artist = ', '.join([a['name'] for a in better_result.get('artists', [])])
            print(f"[{idx}/{len(favTracks)}] Adding: {video_title} - {video_artist}")
            yt.add_playlist_items(yt_playlist_id, [better_result['videoId']])
            success_counter += 1
        except Exception as e:
            error_counter += 1
            error_msg = f"Error processing '{track_name} - {artist_name}': {str(e)}"
            print(f"[{idx}/{len(favTracks)}] ERROR: {error_msg}")
            with open(file_directory, "a", encoding="utf-8") as f:
                if error_counter == 1:
                    f.write("=== Favorite songs transfer errors ===\n")
                f.write(f"{error_msg}\n")
    print("\nTransfer summary:")
    print(f"- Total tracks processed: {processed_tracks}")
    print(f"- Successfully added: {success_counter}")
    print(f"- Errors encountered: {error_counter}")
    if error_counter > 0:
        print(f"\nCheck '{file_directory}' for details on errors")
    winsound.Beep(freq, tempo)
    return 

def check_and_delete_YTplaylists(name_or_pattern, is_pattern=True):
    global yt
    matching_playlists = []
    try:
        YTplaylists = yt.get_library_playlists(limit=None)
    except Exception as e:
        print(f"Error retrieving playlists from YTmusic: {e}")
        return
    for playlist in YTplaylists:
        if (is_pattern and re.match(name_or_pattern, playlist['title'])) or (not is_pattern and playlist['title'] == name_or_pattern):
            matching_playlists.append(playlist)
    if len(matching_playlists) == 1:
        playlist_name = matching_playlists[0]['title']
        choice = input(f"Playlist '{playlist_name}' found. Do you wish to delete it? (y/n) ")
        while choice.strip().lower() not in ['y', 'n']:
            choice = input("Unrecognized input. ")
        if choice.strip().lower() == 'y':
            try:
                yt.delete_playlist(matching_playlists[0]['playlistId'])
                print(f"Playlist '{playlist_name}' successfully deleted.")
            except Exception as e:
                print(f"Error deleting playlist: {e}")
    elif len(matching_playlists) > 1:
        print("Multiple matching playlists found:")
        for i, playlist in enumerate(matching_playlists):
            print(f"{i+1}. {playlist['title']}")
        choice = input("Do you wish to delete one or more of them? (y/y to all/n) ")
        while choice.strip().lower() not in ['y', 'y to all', 'n']:
            choice = input("Unrecognized input. ")
        if choice.strip().lower() == 'y to all':
            for playlist in matching_playlists:
                try:
                    yt.delete_playlist(playlist['playlistId'])
                    print(f"Playlist '{playlist['title']}' deleted.")
                except Exception as e:
                    print(f"Error deleting playlist '{playlist['title']}': {e}")

def erase_YTliked_songs(liked_songs):# QUESTA FUNZIONE NON VIENE USATA E SEMBRA NON FUNZIONARE
    global yt
    for song in liked_songs:
        try:
            video_id = song.get('videoId')
            name = song.get('title')
            if song.get('likeStatus') == 'LIKE':
                yt.rate_song(video_id, 'INDIFFERENT')
        except Exception as e:
            print(f"\nError while erasing {name} from YTmusic liked songs: \n{e}")

def merge_liked_songs_onYT(favTracks, liked_songs):# QUESTA FUNZIONE NON VIENE USATA E SEMBRA NON FUNZIONARE
    global yt
    file_directory = get_mismatch_directory(None)
    print("Fetching liked songs from YouTube Music...")
    liked_songs_dict = {song['videoId']: song['title'].lower() for song in liked_songs}
    print(f"Found {len(liked_songs_dict)} already liked songs on YouTube Music.")
    error_counter = 0
    added_counter = 0
    for favTrack in favTracks:
        track_name, artist_name, track_id = favTrack
        try:
            search_query = f"{track_name} {artist_name}"
            search_results = yt.search(search_query, filter="songs", limit=5, ignore_spelling=True)
            better_result = find_best_match(track_name, search_results)
            if not better_result:
                raise ValueError(f"Mismatch: {track_name} - {artist_name} not found on YouTube Music.")
            video_id = better_result['videoId']
            song_title = better_result['title'].lower()
            if not (video_id in liked_songs_dict or song_title in liked_songs_dict.values()):
                yt.rate_song(video_id, "LIKE")
                added_counter += 1
        except Exception as e:
            print(f"Error during merging of liked songs: {e}")
            with open(file_directory, "a", encoding="utf-8") as f:
                if error_counter == 0:
                    f.write("Favorite songs not added automatically:\n")
                f.write(f"{track_name} - {artist_name}, {e}\n")
            error_counter += 1
    winsound.Beep(freq, tempo)
    print(f"Merge completed: {added_counter} songs added. ({error_counter} errors)")

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def find_best_match(song, search_results):
    track_name, artist_name, track_id = song  # ValueError: too many values to unpack (expected 3)
    best_match = None
    best_score = -1
    for result in search_results:
        result_title = result.get("title", "")
        result_artists = [artist["name"].lower() for artist in result.get("artists", [])]
        if not result_title or not result_artists:
            continue
        if result_title.lower() == track_name.lower() and artist_name.lower() in result_artists:
            return result
        score = similarity(track_name, result_title)
        artist_score = max(similarity(artist_name, res_artist) for res_artist in result_artists) if result_artists else 0
        total_score = score + artist_score
        if total_score > best_score:
            best_score = total_score
            best_match = result
        if best_score < 0.5:
            raise ValueError(f"No good match found (max similarity between songs on the two platforms: {best_score:.2f})")
    return best_match

def ensure_mismatch_dir():
    if not os.path.exists(MISMATCH_DIR):
        os.makedirs(MISMATCH_DIR)

def get_mismatch_directory(playlist_name):
    if playlist_name is None:
        clean_name = "favSongs"
    else:
        clean_name = re.sub(r'\W+', '_', playlist_name.lower())
    ensure_mismatch_dir()
    return os.path.join(MISMATCH_DIR, f"mismatch_{clean_name}.txt")

def checkMismatch(file_directory, open_file):
    if not os.path.exists(file_directory):
        open(file_directory, 'w', encoding="utf-8").close()
        print(f"File '{file_directory}' not found. A new one has been created.")
        return False
    with open(file_directory, 'r', encoding="utf-8") as f:
        content = f.read().strip()
    if not content:
        print(f"File '{file_directory}' is empty.")
        return False
    if open_file:
        os.system(f"notepad {file_directory}")
    return True

def clearMismatch(file_directory):
    with open(file_directory, "w", encoding="utf-8") as f:
        f.write("")
    print(f"Mismatch file '{file_directory}' has been cleared.")

def open_selected_mismatch_files():
    if not os.path.exists(MISMATCH_DIR):
        print("Mismatch directory not found.")
        return
    files = [f for f in os.listdir(MISMATCH_DIR) if os.path.isfile(os.path.join(MISMATCH_DIR, f))]
    if not files:
        print("No mismatch files found in the directory.")
        return
    print("Mismatch files found:")
    for i, file_directory in enumerate(files, start=1):
        print(f"{i}. {file_directory}")
    while True:
        selection = input("Enter the numbers of the files you want to open (separated by spaces) or type 'exit' to cancel: ").strip()
        if selection.lower() == 'exit':
            print("Operation cancelled.")
            return
        try:
            indexes = [int(x) for x in selection.split() if x.isdigit()]
        except Exception as e:
            print("Invalid input. Please try again.")
            continue
        if all(1 <= idx <= len(files) for idx in indexes) and indexes:
            break
        else:
            print("One or more indexes are invalid. Please try again.")
    for idx in indexes:
        file_path = os.path.join(MISMATCH_DIR, files[idx-1])
        os.system(f'notepad "{file_path}"')

def askCommands():
    commands = {
        "1": "Transfer from Spotify to YT Music",
        "3": "Open Transfer mismatch list",
        "2": "Transfer from YT Music to Spotify",
        "4": "Uninstall all resources",
        "5": "Exit                             "}
    while True:
        print("\nAvailable commands (enter the number):")
        for key, value in commands.items():
            print(f"({key}) {value}", end="    ")
            if key == "3" or key == "4": print("")
        choice = input("Select an option: ").strip()
        if choice in commands:
            return choice
        if choice.lower() == "exit":
            return '5'
        else:
            print("Unrecognized input. Please try again.")

def main():
    while True:
        command = askCommands()
        if command == "5":
            break
        elif command == "4":
            UninstallAll()
        elif command == "3":
            open_selected_mismatch_files()
        elif command == "1":
            transferFrom = "Spotify" 
            transferTo = "YTmusic"           
            if not isSpotifyAPI_connected():
                try:
                    connectToSpotifyAPI()
                except Exception as e:
                    print(f"\n{e}\nExiting.")
                    return False
            if not isYTmusicAPI_connected():
                try:
                    connectToYTmusicAPI()
                except Exception as e:
                    print(f"\n{e}\nExiting.")
                    return False
            print("Fetching User informations, please wait...")
            playlists = getPlaylists(transferFrom)
            favTracks = getSPFavoriteTracks() 
            if not playlists and not favTracks:
                print("No playlists nor favorite songs found.\n Exiting.")
                return None
            if playlists: 
                print("\nAvailable playlists:")
                for idx, (name, num, playlist_id) in enumerate(playlists, start=1):
                    print(f"({idx}) {name} - {num} songs")
            else:
                print("No playlists found.")
            if favTracks:
                print(f"Favorite songs: {len(favTracks)}\nMind that, if you wish to transfer your favorite songs from Spotify to YTmusic, this program will save them in a new playlist.")
            else:
                print("No Favorite songs found.")
            selected_playlists = []
            selection = input("Enter playlist(s) number(s) separated by spaces, or type 'Fav' for liked songs, 'all' or 'exit': ").strip()
            while selection.lower() not in ['exit', 'fav', 'all'] and not all(i.isdigit() and 1 <= int(i) <= len(playlists) for i in selection.split()):
                selection = input("Unrecognized input, please enter playlist(s) number(s) separated by spaces, 'Fav', 'all' or 'exit': ").strip()
            
            if selection.lower() == "exit":
                break

            elif selection.lower() == 'fav':
                try:
                    check_and_delete_YTplaylists(r"Favorite songs from Spotify \(.*\)", True)
                    file_directory = get_mismatch_directory("favSongs")
                    if checkMismatch(file_directory, False) and input("Transfer mismatch list isn't empty, do you want to erase it? (y/n) ").strip().lower() == 'y': 
                        clearMismatch(file_directory)
                    if len(favTracks) > 500: 
                        print("\nThis may take a while, you can enter Ctrl+C to abort and shutdown...")
                    print("\nThis process runs in background, you may minimize this app.")
                    copyFavSongs_toYT_playlist(favTracks)
                except Exception as e:
                    print(f"\nFatal error during favorite songs transfer: {e}")
                    return None
                
            elif selection.lower() == 'all':
                tot_songs = sum([num for name, num, playlist_id in playlists] + [len(favTracks)])
                try:
                    check_and_delete_YTplaylists(r"Favorite songs from Spotify \(.*\)", True)
                    file_directory = get_mismatch_directory("favSongs")
                    if checkMismatch(file_directory, False) and input("Transfer mismatch list isn't empty, do you want to erase it? (y/n) ").strip().lower() == 'y': 
                        clearMismatch(file_directory)
                    if tot_songs > 500:
                        print("\nThis may take a while, you can enter Ctrl+C to abort and shutdown...")
                    print("\nThis process runs in background, you may minimize this app.")
                    copyFavSongs_toYT_playlist(favTracks)
                except Exception as e:
                    print(f"\nError while managing favorite songs: \n{e}")
                    return None
                try:
                    selected_playlists = playlists
                    for playlist_name, num_songs, playlist_id in selected_playlists:
                        if checkMismatch(get_mismatch_directory(playlist_name), False) and input("Transfer mismatch list isn't empty, do you want to erase it? (y/n) ").strip().lower() == 'y': 
                            clearMismatch(get_mismatch_directory(playlist_name))
                        transferPlaylist(playlist_id, playlist_name, transferFrom, transferTo)
                except Exception as e:
                    print(f"\nError while managing playlists: \n{e}")
                    return None
                
            elif all(i.isdigit() and 1 <= int(i) <= len(playlists) for i in selection.split()):
                selected_playlists = [playlists[int(i) - 1] for i in selection.split()]
                tot_songs = 0
                tot_songs = sum([num for name, num, playlist_id in selected_playlists])
                if tot_songs > 500:
                    print("\nThis may take a while, you can enter Ctrl+C to abort and shutdown...")
                print("\nThis process runs in background, you may minimize this app.")
                for playlist_name, num_songs, playlist_id in selected_playlists:
                    if checkMismatch(get_mismatch_directory(playlist_name), False) and input("Transfer mismatch list isn't empty, do you want to erase it? (y/n) ").strip().lower() == 'y': 
                        clearMismatch(get_mismatch_directory(playlist_name))
                    transferPlaylist(playlist_id, playlist_name, transferFrom, transferTo)

        elif command == "2":
            transferFrom = "YTmusic" 
            transferTo = "Spotify" 
            print("This process isn't supported yet")

    print("Program terminated.")
    return True

#if __name__ == "__musicTransfer_main__":
main()
#connectToSpotifyAPI() #CHIAMATE DI DEBUG, SERVONO PER PROVARE SOLO LA CONNESSIONE ALLE API
#connectToYTmusicAPI()

# List of all available functions in ytmusicapi:
# https://ytmusicapi.readthedocs.io/en/stable/?utm_source=chatgpt.com
