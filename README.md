# VS Mod Updater

Skrypt w Pythonie do automatycznej aktualizacji modów na serwerze **Vintage Story**.
Sprawdza mody (`.zip`) w bieżącym katalogu, porównuje ich wersje z [ModDB](https://mods.vintagestory.at)
i pobiera najnowsze wydania kompatybilne z wersją gry.

## Funkcje

- Odczyt `modinfo.json` z każdego pliku `.zip` moda
- Sprawdzanie dostępnych wydań przez API ModDB (`/api/mod/<modid>`)
- Dobór wersji kompatybilnej z wersją gry (na podstawie tagów wydania)
- Pomijanie wersji testowych (`-rc`, `-pre`, `-alpha`, `-beta`)
- Kopia zapasowa starej wersji jako `<nazwa>.zip_` (serwer jej nie ładuje)

## Wymagania

- Python 3.8+
- Biblioteki z `requirements.txt`

```bash
pip install -r requirements.txt
```

## Konfiguracja

Utwórz plik `/home/vintagestory/game_version.txt` z numerem wersji gry, np.:

```
1.22.0
```

## Użycie

Uruchom skrypt **w katalogu z modami** serwera:

```bash
cd /home/vintagestory/data/Mods
python3 update_mods.py
```

Po aktualizacji zrestartuj serwer.

### Przywracanie starej wersji

1. Usuń nowy plik moda (`<modid>_v<wersja>.zip`)
2. Zmień nazwę kopii z `.zip_` na `.zip`

## Planowane

- Plik wykluczeń / przypinania wersji (`mod_exclusions.txt`)
- Pobieranie do pliku tymczasowego i bezpieczna podmiana
- Timeout zapytań HTTP
- Ścieżka do katalogu modów jako argument
- Tryb `--dry-run` (tylko sprawdzenie, bez pobierania)

## Licencja

MIT
