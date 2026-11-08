# Changelog

Format oparty na [Keep a Changelog](https://keepachangelog.com/pl/1.1.0/),
wersjonowanie zgodne z [SemVer](https://semver.org/lang/pl/).

## [Unreleased]

### Fixed
- Pomijanie wersji testowych (`-rc`, `-pre`, `-alpha`, `-beta`) przy wyborze aktualizacji
  (np. CarryOn `2.0.0-rc.1` był wybierany zamiast stabilnego `1.14.x`)

## [1.0.0] - 2026-11-08

### Added
- Pierwsza wersja w repozytorium: sprawdzanie i automatyczna aktualizacja modów z ModDB
- Dobór wersji kompatybilnej z wersją gry z `game_version.txt`
- Kopia zapasowa starej wersji jako `.zip_`
