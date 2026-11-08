#!/usr/bin/env python3
import os
import json
import zipfile
import requests
from packaging import version

def get_game_version():
    """Odczytuje wersję gry z pliku game_version.txt"""
    try:
        with open('/home/vintagestory/game_version.txt', 'r') as f:
            game_ver = f.read().strip()
            print(f"Wykryta wersja gry: {game_ver}")
            return game_ver
    except FileNotFoundError:
        print("BŁĄD: Nie znaleziono pliku game_version.txt")
        print("Utwórz plik game_version.txt z numerem wersji gry (np. 1.20.12)")
        exit(1)
    except Exception as e:
        print(f"Błąd odczytu game_version.txt: {e}")
        exit(1)

def is_version_compatible(mod_requirement, game_version):
    """Sprawdza czy wersja moda jest kompatybilna z wersją gry"""
    try:
        # Obsługa różnych formatów wymagań wersji
        if not mod_requirement:
            return True

        # Usuń prefiksy jak "1.20.0+" jeśli występują
        if mod_requirement.endswith('+'):
            min_version = mod_requirement[:-1]
            return version.parse(game_version) >= version.parse(min_version)

        # Sprawdź czy to dokładna wersja
        if '-' in mod_requirement and 'pre' in mod_requirement:
            # To wersja pre-release, sprawdź czy gra też jest pre-release
            if 'pre' not in game_version:
                return False

        # Dla wersji typu "1.20.15" sprawdź kompatybilność z rodziną wersji
        mod_parts = mod_requirement.split('.')
        game_parts = game_version.split('.')

        # Sprawdź główną wersję (1.20 vs 1.21)
        if len(mod_parts) >= 2 and len(game_parts) >= 2:
            mod_major_minor = f"{mod_parts[0]}.{mod_parts[1]}"
            game_major_minor = f"{game_parts[0]}.{game_parts[1]}"

            if mod_major_minor != game_major_minor:
                return False

        # Jeśli dotarliśmy tutaj, prawdopodobnie kompatybilne
        return version.parse(game_version) >= version.parse(mod_requirement)

    except Exception as e:
        print(f"Błąd sprawdzania kompatybilności: {e}")
        return False

def get_mod_info(zip_path):
    """Pobiera informacje o modzie z pliku zip"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file in zip_ref.namelist():
                if file.endswith('modinfo.json'):
                    with zip_ref.open(file) as json_file:
                        content = json_file.read().decode('utf-8-sig')
                        return json.loads(content)
                        #return json.load(json_file)
    except Exception as e:
        print(f"Błąd odczytu {zip_path}: {e}")
    return None

def check_online_version(modid, game_version):
    """Sprawdza najnowszą kompatybilną wersję moda używając API"""
    api_url = f"https://mods.vintagestory.at/api/mod/{modid}"
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            mod_data = response.json()
            if 'mod' in mod_data and 'releases' in mod_data['mod'] and mod_data['mod']['releases']:

                verified_compatible = []  # Rzeczywiście kompatybilne (z dependencies)
                assumed_compatible = []   # Założone kompatybilne (bez dependencies)

                # Przejdź przez wszystkie releasy i zbierz kompatybilne
                for release in mod_data['mod']['releases']:
                    # Sprawdź czy release ma wymagania gry w tagach
                    game_req = None
                    supported_versions = []

                    if 'tags' in release and release['tags']:
                        # Tagi zawierają bezpośrednio numery wersji gry
                        supported_versions = release['tags']
                        # Dla wyświetlenia weź pierwszą wersję jako reprezentatywną
                        game_req = supported_versions[0] if supported_versions else None

                    # Jeśli nie ma tagów, sprawdź modinfo w API
                    if not game_req and 'modinfo' in release:
                        deps = release.get('modinfo', {}).get('dependencies', {})
                        game_req = deps.get('game')
                        if game_req:
                            supported_versions = [game_req]

                    # Jeśli brak wymagań - dodaj do założonych
                    if not supported_versions:
                        print(f"  Wersja {release['modversion']} - brak wymagań gry, dodaję do założonych")
                        assumed_compatible.append({
                            'release': release,
                            'game_requirement': 'brak (założono kompatybilność)'
                        })
                    else:
                        # Sprawdź czy którakolwiek z obsługiwanych wersji jest kompatybilna
                        is_compatible = False
                        for supported_version in supported_versions:
                            if is_version_compatible(supported_version, game_version):
                                is_compatible = True
                                break

                        if is_compatible:
                            version_range = f"{supported_versions[0]}" + (f"-{supported_versions[-1]}" if len(supported_versions) > 1 else "")
                            print(f"  Wersja {release['modversion']} - ✓ kompatybilna (obsługuje: {version_range})")
                            verified_compatible.append({
                                'release': release,
                                'game_requirement': version_range
                            })
                        else:
                            version_range = f"{supported_versions[0]}" + (f"-{supported_versions[-1]}" if len(supported_versions) > 1 else "")
                            print(f"  Wersja {release['modversion']} - ✗ niekompatybilna (obsługuje: {version_range})")

                # Wybierz najlepszą wersję: priorytet dla zweryfikowanych
                best_release = None
                if verified_compatible:
                    best_release = verified_compatible[0]
                    print(f"  ✓ Wybrano najnowszą zweryfikowaną: {best_release['release']['modversion']}")
                elif assumed_compatible:
                    best_release = assumed_compatible[0]
                    print(f"  ⚠ Wybrano najnowszą założoną: {best_release['release']['modversion']}")

                if best_release:
                    release = best_release['release']

                    main_file = release['mainfile']
                    if not main_file.startswith('https://'):
                        main_file = f"https://mods.vintagestory.at{main_file}"

                    return {
                        'version': release['modversion'],
                        'download_url': main_file,
                        'game_requirement': best_release['game_requirement']
                    }
                else:
                    print(f"  Brak kompatybilnej wersji dla gry {game_version}")
                    return None

    except Exception as e:
        print(f"Błąd API dla {modid}: {e}")
    return None

def download_mod(url, filename):
    """Pobiera mod z podanego URL"""
    try:
        print(f"Pobieram z: {url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0

        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = int(downloaded * 100 / total_size)
                        print(f"\rPostęp: {percent}%", end='', flush=True)
        print()
        return True
    except Exception as e:
        print(f"Błąd podczas pobierania: {e}")
        return False

def update_mod(mod_info):
    """Aktualizuje mod - zmienia nazwę starej wersji i pobiera nową"""
    old_file = mod_info['filename']
    modid = mod_info['modid']

    # Tworzenie nazw plików z uwzględnieniem wersji
    new_filename = f"{modid}_v{mod_info['available']}.zip"

    print(f"\nAktualizuję {mod_info['name']}:")
    print(f"- Pobieram nową wersję jako: {new_filename}")
    if download_mod(mod_info['download_url'], new_filename):
        print(f"✓ Aktualizacja zakończona pomyślnie!")
        print(f"- Zapisuję starą wersję jako: {old_file}_")
        try:
            os.rename(old_file, f"{old_file}_")
            return True
        except Exception as e:
            print(f"Błąd podczas tworzenia kopii: {e}")
            return False
    else:
        # Jeśli pobieranie nie powiodło się, przywracamy starą wersję
        try:
            os.rename(f"{old_file}_", old_file)
            print("Przywrócono poprzednią wersję")
        except Exception as e:
            print(f"Błąd podczas przywracania poprzedniej wersji: {e}")
        return False

def main():
    # Wczytaj wersję gry
    game_version = get_game_version()

    updates_available = []
    no_compatible_updates = []

    print(f"Sprawdzam aktualizacje modów dla gry wersji {game_version}...")

    # Sprawdź każdy plik zip w bieżącym katalogu
    for filename in os.listdir('.'):
        if not filename.endswith('.zip') or filename.endswith('.zip_'):
            continue

        mod_info = get_mod_info(filename)
        if not mod_info:
            print(f"Pominięto {filename} - nie znaleziono modinfo.json")
            continue

        local_version = mod_info.get('version') or mod_info.get('Version')
        modid = mod_info.get('modid')
        name = mod_info.get('name')

        if not all([local_version, modid, name]):
            print(f"Pominięto {filename} - brak wymaganych informacji")
            continue

        print(f"\nSprawdzam {name} (aktualna: {local_version})...")
        online_data = check_online_version(modid, game_version)

        if online_data:
            try:
                if version.parse(online_data['version']) > version.parse(local_version):
                    updates_available.append({
                        'name': name,
                        'modid': modid,
                        'current': local_version,
                        'available': online_data['version'],
                        'download_url': online_data['download_url'],
                        'game_requirement': online_data['game_requirement'],
                        'filename': filename
                    })
                    print(f"✓ Znaleziono kompatybilną aktualizację: {online_data['version']}")
                else:
                    print(f"✓ Mod jest aktualny")
            except version.InvalidVersion:
                print(f"Nieprawidłowy format wersji dla {name}")
        else:
            no_compatible_updates.append(name)

    # Podsumowanie
    if updates_available:
        print(f"\n{'='*60}")
        print(f"ZNALEZIONO {len(updates_available)} KOMPATYBILNYCH AKTUALIZACJI:")
        print(f"{'='*60}")

        for mod in updates_available:
            print(f"\n- {mod['name']}")
            print(f"  Aktualna wersja: {mod['current']}")
            print(f"  Dostępna wersja: {mod['available']}")
            print(f"  Wymagana gra: {mod['game_requirement']}")

            # Automatycznie aktualizuj każdy mod
            update_mod(mod)
    else:
        print(f"\n{'='*40}")
        print("WSZYSTKIE MODY SĄ AKTUALNE!")
        print(f"{'='*40}")

    if no_compatible_updates:
        print(f"\n{'='*60}")
        print(f"MODY BEZ KOMPATYBILNYCH AKTUALIZACJI ({len(no_compatible_updates)}):")
        print(f"{'='*60}")
        for mod_name in no_compatible_updates:
            print(f"- {mod_name}")

if __name__ == "__main__":
    main()
