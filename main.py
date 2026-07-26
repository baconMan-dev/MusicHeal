import os
import zipfile
import shutil
import flet as ft
from mutagen.flac import FLAC
from mutagen.mp3 import MP3

def main(page: ft.Page):
    page.title = "MusicHeal Engine"
    page.background_color = "#121212"
    page.padding = 20
    
    console = ft.Text(value="System ready... Tap button above to execute.", color="#00FF00", font_family="monospace")
    scroll_view = ft.Column([console], scroll=ft.ScrollMode.AUTO, height=400, width=500)
    
    def log(message):
        console.value += f"\n{message}"
        page.update()

    def button_click(e):
        console.value = "Invoking MusicHeal System...\n"
        page.update()
        
        downloads_folder = '/storage/emulated/0/Download/'
        music_library = '/storage/emulated/0/Music/'
        staging_folder = os.path.expanduser('~/unzip_stage')
        queue_file = os.path.expanduser('~/.heal_queue')

        log(">>> Launching Duplicate-Aware Extraction Engine...\n")
        total_albums_unpacked = 0
        unpacked_folders = []

        zip_groups = {}
        if os.path.exists(downloads_folder):
            for file in os.listdir(downloads_folder):
                if file.lower().endswith('.zip'):
                    clean_name = file.replace('.zip', '').replace('[E]', '').replace('[e]', '').replace('[Explicit]', '').strip()
                    base_name = clean_name.split(' (')[0].strip()
                    if base_name not in zip_groups:
                        zip_groups[base_name] = []
                    zip_groups[base_name].append(file)

        for base_album, zip_files in zip_groups.items():
            final_album_dir = os.path.join(music_library, base_album)
            os.makedirs(final_album_dir, exist_ok=True)
            log(f"Processing Album Group: {base_album} ({len(zip_files)} zip found)")
            
            songs_extracted, lrc_extracted, files_moved = 0, 0, 0
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
                    log(f"  --> {zip_file} corrupted. Extracting partial files...")

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

            total_tracks_expected = 0
            existing_audio_files = [x for x in os.listdir(final_album_dir) if x.lower().endswith(('.flac', '.mp3'))]
            for track in existing_audio_files:
                try:
                    track_path = os.path.join(final_album_dir, track)
                    if track.lower().endswith('.flac'):
                        total_tag = FLAC(track_path).get('totaltracks', FLAC(track_path).get('tracktotal', ['0']))
                    else:
                        total_tag = MP3(track_path).get('TRCK', ['0'])
                    if '/' in total_tag: total_tag = total_tag.split('/')
                    if int(total_tag) > total_tracks_expected: total_tracks_expected = int(total_tag)
                except Exception: pass

            actual_track_count = len(existing_audio_files)
            is_complete = False
            if total_tracks_expected > 0:
                if actual_track_count >= total_tracks_expected:
                    is_complete = True
                    log(f"  --> [COMPLETE] Verified via Metadata: Got {actual_track_count}/{total_tracks_expected} songs.")
                else:
                    log(f"  --> [INCOMPLETE] Expected {total_tracks_expected} songs, found {actual_track_count}. Holding zip source.")
            else:
                if actual_track_count > 0:
                    is_complete = True
                    log("  --> [SUCCESS] Moved assets safely. No total track tag found.")

            if is_complete:
                for path in successfully_processed_zips:
                    try: os.remove(path)
                    except Exception: pass
                total_albums_unpacked += 1
                unpacked_folders.append(final_album_dir)

        if os.path.exists(staging_folder): shutil.rmtree(staging_folder)
        log("\nExecution completed successfully!")

    heal_button = ft.ElevatedButton(
        text="START MUSIC HEAL",
        on_click=button_click,
        bgcolor="#00FF00",
        color="#000000",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        height=60,
        width=500
    )
    
    page.add(heal_button, ft.Container(height=10), scroll_view)

ft.app(target=main)
