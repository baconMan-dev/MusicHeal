import os
import zipfile
import shutil
from mutagen.flac import FLAC
from mutagen.mp3 import MP3

BLUE, GREEN, YELLOW, RED, RESET = "\033[1;34m", "\033[1;32m", "\033[1;33m", "\033[1;31m", "\033[0m"
downloads_folder = '/storage/emulated/0/Download/'
music_library = '/storage/emulated/0/Music/'
staging_folder = os.path.expanduser('~/unzip_stage')
queue_file = os.path.expanduser('~/.heal_queue')

print(f"{BLUE}>>> Launching Duplicate-Aware Extraction Engine...{RESET}\n")
total_albums_unpacked = 0
unpacked_folders = []

# Group zip files by their cleaned album names to detect duplicates
zip_groups = {}
for file in os.listdir(downloads_folder):
    if file.lower().endswith('.zip'):
        clean_name = file.replace('.zip', '').replace('[E]', '').replace('[e]', '').replace('[Explicit]', '').strip()
        # Strip trailing duplicate indicators like (1), (2) added by Android downloaders
        base_name = clean_name.split(' (')[0].strip()
        if base_name not in zip_groups:
            zip_groups[base_name] = []
        zip_groups[base_name].append(file)

for base_album, zip_files in zip_groups.items():
    final_album_dir = os.path.join(music_library, base_album)
    os.makedirs(final_album_dir, exist_ok=True)
    
    print(f"\033[K{BLUE}Processing Album Group: {base_album} ({len(zip_files)} zip found){RESET}")
    
    songs_extracted = 0
    lrc_extracted = 0
    files_moved = 0
    successfully_processed_zips = []

    for zip_file in zip_files:
        zip_path = os.path.join(downloads_folder, zip_file)
        if os.path.exists(staging_folder): shutil.rmtree(staging_folder)
        os.makedirs(staging_folder, exist_ok=True)
        
        unpack_success = False
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(staging_folder)
            unpack_success = True
        except Exception:
            print(f"{YELLOW}  --> {zip_file} corrupted. Extracting partial files...{RESET}")

        # Move files from staging to the main music library
        for root, _, walk_files in os.walk(staging_folder):
            for f in walk_files:
                f_lower = f.lower()
                if f_lower.endswith(('.flac', '.mp3', '.jpg', '.jpeg', '.png', '.lrc')):
                    src, dst = os.path.join(root, f), os.path.join(final_album_dir, f)
                    if not os.path.exists(dst):
                        shutil.move(src, dst)
                        files_moved += 1
                        if f_lower.endswith(('.flac', '.mp3')): songs_extracted += 1
                        elif f_lower.endswith('.lrc'): lrc_extracted += 1
        
        if unpack_success or (os.path.exists(staging_folder) and os.listdir(staging_folder)):
            successfully_processed_zips.append(zip_path)

    # --- METADATA COMPLETION VERIFICATION ---
    total_tracks_expected = 0
    existing_audio_files = [x for x in os.listdir(final_album_dir) if x.lower().endswith(('.flac', '.mp3'))]
    
    # Read metadata tags to discover the absolute album track total
    for track in existing_audio_files:
        try:
            track_path = os.path.join(final_album_dir, track)
            if track.lower().endswith('.flac'):
                meta = FLAC(track_path)
                total_tag = meta.get('totaltracks', meta.get('tracktotal', ['0']))[0]
            else:
                meta = MP3(track_path)
                total_tag = meta.get('TRCK', ['0'])[0]
            
            if '/' in total_tag:  # Handles "track_num/total_tracks" formatting strings
                total_tag = total_tag.split('/')[1]
            
            if int(total_tag) > total_tracks_expected:
                total_tracks_expected = int(total_tag)
        except Exception:
            pass

    actual_track_count = len(existing_audio_files)
    
    # Determine completion status based on metadata findings
    is_complete = False
    if total_tracks_expected > 0:
        if actual_track_count >= total_tracks_expected:
            is_complete = True
            print(f"{GREEN}  --> [COMPLETE] Verified via Metadata: Got {actual_track_count}/{total_tracks_expected} songs.{RESET}")
        else:
            print(f"{YELLOW}  --> [INCOMPLETE] Metadata expects {total_tracks_expected} songs, but only found {actual_track_count}. Holding zip files.{RESET}")
    else:
        # Fallback if audio files entirely lack completion tags
        if actual_track_count > 0:
            is_complete = True 
            print(f"{GREEN}  --> [SUCCESS] Moved assets safely. No explicit total track tags found to verify completion.{RESET}")

    # Safe Cleanup Handling
    if is_complete:
        for path in successfully_processed_zips:
            try: os.remove(path)
            except Exception: pass
        total_albums_unpacked += 1
        unpacked_folders.append(final_album_dir)

if os.path.exists(staging_folder): shutil.rmtree(staging_folder)
