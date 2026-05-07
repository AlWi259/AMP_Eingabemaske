# Test-Personas

Jede Persona hat eine Sequenz von Nachrichten. Einfach eine nach der anderen abschicken, abwarten, dann die nächste.

---

## Persona 1 – Carolin Maier, Controlling

Ruhige, präzise Antworten. Kennt ihre Daten gut.

**Nachricht 1**
```
Der Bericht heißt "Monatliches Kostenstellenreporting". Es ist eine Excel-Auswertung, die jeden Monat manuell aus SAP HANA gezogen wird und die Kosten pro Kostenstelle für das Management aufbereitet.
```

**Nachricht 2**
```
Ich bin die Besitzerin, Carolin Maier, Fachabteilung Controlling. IT-Ansprechpartner ist Herr Becker aus der IT.
```

**Nachricht 3**
```
Wir nutzen aktuell Excel, die Daten kommen aus SAP HANA. Output ist eine Excel-Datei, die per E-Mail an das Management geschickt wird. Zielgruppe ist die Geschäftsführung.
```

**Nachricht 4**
```
Der Bericht ist manuell – ich brauche etwa einen halben Tag, um die Daten rauszuziehen, zu bereinigen und das Template zu befüllen. Es gibt keine Gateway-Verbindung, alles läuft über einen manuellen Export. Aktualisierung monatlich, Daten sind immer aktuell.
```

**Nachricht 5**
```
Vor jeder Verteilung braucht der Bericht ein Approval vom Management. Letztes Review war 11.2024. Komplexität würde ich als mittel einschätzen – die Logik ist überschaubar, aber der manuelle Aufwand ist hoch. Migration ist noch offen, Priorität hoch.
```

---

## Persona 2 – Thomas Brandt, Vertrieb

Kurze, schnelle Antworten. Denkt in Business-Begriffen, nicht in IT-Begriffen.

**Nachricht 1**
```
Vertriebsdashboard DACH – zeigt Umsatz, Pipeline und Forecast für Deutschland, Österreich und Schweiz. Läuft in Power BI.
```

**Nachricht 2**
```
Ich bin Thomas Brandt, Vertrieb. Das ist ein Dashboard für unser Sales-Management, also für die Führungsebene im Vertrieb.
```

**Nachricht 3**
```
Daten kommen aus dem SQL Server, wir haben eine Gateway-Verbindung. Der Bericht refresht täglich automatisch, keine manuellen Schritte nötig.
```

**Nachricht 4**
```
Ausgabe ist ein Power BI Report, direkt im Browser. Datenqualität ist aktuell. Nach Änderungen muss der Fachbereich freigeben.
```

**Nachricht 5**
```
Komplexität ist hoch, da viele DAX-Measures und Row-Level Security drin sind. Migration läuft gerade, wir sind in Entwicklung. Priorität ist kritisch, das ist unser wichtigstes Dashboard.
```

---

## Persona 3 – Stefan Köhler, IT

Technisch präzise. Gibt Details, die über das nötigste hinausgehen.

**Nachricht 1**
```
Der Bericht heißt "ERP-Datenqualitätsbericht". Es ist ein operativer Bericht, der täglich automatisch prüft, ob die Stammdaten aus SAP korrekt und vollständig ins Data Warehouse übertragen wurden. Zuständig bin ich, Stefan Köhler, IT-Abteilung.
```

**Nachricht 2**
```
Primäre Quelle ist SAP BW, zusätzlich zieht der Bericht noch Vergleichsdaten aus einem PostgreSQL-Staging-System. Aktuelles Tool ist SSRS, Output ist eine PDF-Datei die täglich per E-Mail an das IT-Team und Qualitätssicherung geht.
```

**Nachricht 3**
```
Gateway-Verbindungen: ja, über den On-Premises Data Gateway. Vollautomatisiert, kein manueller Aufwand vor dem Reporting. Daten sind immer tagesfrisch, also aktuell.
```

**Nachricht 4**
```
Nach Änderungen kein formales Approval nötig, das liegt in meiner Verantwortung als IT. Letztes Review: 03.2025. Zielgruppe sind die IT-Analysten und die Qualitätssicherung.
```

**Nachricht 5**
```
Komplexität ist sehr hoch wegen der mehrstufigen Datenvalidierungslogik. Migration ist zurückgestellt, weil wir erst das Staging-System modernisieren müssen. Priorität: mittel. Aufwand für Migration schätze ich auf ca. 12 Personentage.
```
