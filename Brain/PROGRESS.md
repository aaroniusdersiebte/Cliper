# Progress & State

## [Current Focus]
- Bugfixes für Filter und Marker abgeschlossen

## [Pending / Todo]
- [ ] Testen mit echten OBS Chapter-Dateien
- [ ] EDL/XML Format-Support (optional)

## [Completed]
- [x] Initiales Setup der Kontext-Dateien
- [x] Chapter-Parser für OBS streamup-chapter-manager
- [x] `load_chapters()` Funktion in clip_loader.py
- [x] `find_matching_video()` Hilfsfunktion
- [x] UI: Load-Dialog unterstützt Chapter-Dateien (.txt)
- [x] UI: Automatisches Video-Matching
- [x] Resolve: `import_media()` für Video-Import + Timeline-Erstellung
- [x] Bugfix: Filter-Bug behoben (falscher Clip wurde ausgewählt nach Filterung)
- [x] Bugfix: Marker-Diagnose verbessert (Fallback für relative Frames)
- [x] Bugfix: Export zeigt jetzt ob Custom oder Default In/Out-Points verwendet werden
- [x] Bugfix: Export verwendet jetzt Source-FPS statt Timeline-FPS für Frame-Berechnung
- [x] Feature: 60 Sekunden Lücke zwischen Clips in Export-Timeline
- [x] Feature: Marker auf MediaPoolItem (Source) statt Timeline
- [x] Feature: Marker auf Export-Timeline mit Username als Name

## [Known Issues / Blockers]
- Keine