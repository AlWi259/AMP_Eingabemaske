Arbeite im Workspace:

/Users/nb-j2v5jx79py/Desktop/Repos/AMP_Eingabemaske

Kontext:
Wir arbeiten an einer Berichtskatalog-/Eingabemaske-App mit statischem Frontend und kleinem lokalem Python-Backend.

Projektstruktur:
- index.html
- styles.css
- app.js
- assets/
- server.py
- data/ (runtime, ignored)

Aktueller Stand:
1. Das Frontend wurde bereits visuell angepasst.
2. Es gibt jetzt eine einfache JSON-API.
3. Berichte werden sowohl in JSON als auch in SQLite gespeichert.
4. Save/load/delete im Frontend laufen gegen die API.
5. Theme bleibt lokal im Browser gespeichert.

API:
- GET /api/health
- GET /api/reports
- POST /api/reports
- DELETE /api/reports/:id

Speicherung:
- data/reports.json
- data/reports.sqlite3

Arbeitsweise:
- arbeite pragmatisch, mit kleinen klaren Änderungen
- ändere nur die nötigen Dateien
- prüfe nach Änderungen immer kurz Syntax oder Laufweg
- bevorzuge robuste, einfache Lösungen
- Kommentare nur wenn wirklich hilfreich, in einfachem B2 English

Multi-agent workflow:
- nutze Subagents standardmäßig sinnvoll und parallel
- verwende kleine, klar abgegrenzte Helfer für:
  - Code lesen
  - gezielte Suche
  - Gegencheck
  - Review
  - Verifikation
- keine unnötige Dopplung
- integriere die Ergebnisse selbst in eine saubere finale Lösung

Wichtige nächste Ziele:
1. Starte den lokalen Server.
2. Teste die App über localhost, nicht über file://.
3. Verifiziere den echten UI-Flow:
   - speichern
   - laden
   - löschen
4. Prüfe mobile Layout-Themen erneut.
5. Prüfe Theme-Verhalten bei Reload und in Storage-Edge-Cases.

Bekannte offene Punkte:
- Mobile header layout muss in echtem Browser geprüft werden.
- Mobile action layout muss robust gegen Browser-Unterschiede sein.
- Theme hydration / persistence soll sauber geprüft werden.

Bitte starte mit:
1. Repo-Status ansehen
2. index.html, styles.css, app.js, server.py lesen
3. Server lokal starten
4. localhost smoke test machen
5. Findings beheben
6. erneut prüfen
