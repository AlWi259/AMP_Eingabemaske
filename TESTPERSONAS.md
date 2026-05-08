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

---

## Anti-Pattern-Tests

Diese Szenarien testen, wie der Assistent mit schwierigen Gesprächsverläufen umgeht. Jeweils eine Nachricht abschicken, Reaktion beobachten, dann nächste.

---

### Anti-Pattern 1 – Der Ausweicher
*Beantwortet Fragen nie direkt. Schweift ab oder antwortet am Thema vorbei. Testet ob der Assistent sanft aber konsequent zurücklenkt.*

**Nachricht 1**
```
Wir haben da so einen Bericht, den braucht irgendwie jeder, aber keiner weiß so genau warum.
```

**Nachricht 2** *(wenn nach Name/Beschreibung gefragt wird)*
```
Das läuft schon ewig so, ich glaube seit 2019 oder so. Vorher hat das ein Kollege gemacht, der ist aber weg.
```

**Nachricht 3** *(wenn nochmal nach Inhalt gefragt wird)*
```
Ich schicke das halt jeden Monat rum. Die meisten lesen es eh nicht.
```

**Nachricht 4** *(wenn nach Technik gefragt wird)*
```
Excel, glaube ich. Oder war das Access? Nein, Excel. Irgendwas halt.
```

**Nachricht 5** *(wenn nach Verantwortung gefragt wird)*
```
Eigentlich ist das Frau Hoffmann, aber die ist in Eltern­zeit. Und Herr Werner macht das manchmal auch. Also, wir teilen uns das.
```

**Was getestet wird:** Holt der Assistent konkrete Werte heraus, ohne unhöflich zu werden? Bleibt er geduldig oder wird er fordernd?

---

### Anti-Pattern 2 – Der Daten-Dumper
*Schüttet alles auf einmal aus – oft unstrukturiert, manchmal widersprüchlich. Testet ob der Assistent Widersprüche erkennt und die richtigen Werte extrahiert.*

**Nachricht 1**
```
Okay ich mach das kurz: Quartalsabschluss-Report, Finanzen, ich bin zuständig (Markus Lehner), läuft in SSRS, Daten aus Oracle, Output PDF, geht an CFO und Board, quarterly, vollautomatisiert, keine Gateway-Verbindung, kein Approval, Komplexität hoch, Migration offen, Priorität mittel, Aufwand schätze ich 8 PT.
```

**Nachricht 2** *(wenn der Assistent nachfragt oder zusammenfasst)*
```
Ach so, Ausgabe ist eigentlich PowerPoint, nicht PDF. Und eigentlich brauchen wir doch ein Management-Approval, das hatte ich vergessen. Und die Daten sind manchmal 2–3 Tage alt, also nicht wirklich aktuell.
```

**Was getestet wird:** Erkennt der Assistent die Korrekturen und überschreibt die alten Werte? Fragt er nach der Beschreibung, die komplett fehlt?

---

### Anti-Pattern 3 – Der Verweigerer
*Kurze, unwillige Antworten. Findet das Interview lästig. Testet Geduld und ob der Assistent das Gespräch trotzdem zu Ende bringt.*

**Nachricht 1**
```
Vertriebsreport. Muss ich das wirklich ausfüllen?
```

**Nachricht 2** *(nach jeder Folgefrage)*
```
k.A.
```

**Nachricht 3**
```
Fragen Sie doch Frau Schmidt, die weiß das alles.
```

**Nachricht 4**
```
Excel. Keine Ahnung wer das macht. Geht irgendwie automatisch raus, glaube ich.
```

**Nachricht 5** *(wenn nach Komplexität/Migration gefragt wird)*
```
Niedrig. Offen. Niedrig. Fertig jetzt?
```

**Was getestet wird:** Bleibt der Assistent professionell ohne unterwürfig zu sein? Holt er trotzdem alle Pflichtfelder raus? Fordert er nicht nach Feldern, die wirklich nicht rausgehen?

---

### Anti-Pattern 4 – Der Themen-Wechsler
*Stellt mittendrin eigene Fragen ans System oder redet über etwas komplett anderes. Testet ob der Assistent das ruhig ignoriert und weitermacht.*

**Nachricht 1**
```
HR-Bericht, monatlich, geht an Personalleitung. Sagen Sie mal – wird das hier eigentlich gespeichert? Wer hat Zugriff auf diese Daten?
```

**Nachricht 2**
```
Ich bin Maria Fuchs, HR. Können Sie mir eigentlich auch sagen, wie lange das Projekt noch geht?
```

**Nachricht 3**
```
Daten kommen aus SAP HANA. Ich finde übrigens, solche Interviews sollte man persönlich machen, nicht per Chat.
```

**Nachricht 4**
```
Excel, Output ist eine Excel-Datei per E-Mail. Manuell, ich brauch so 2 Stunden im Monat. Achso und gibt es hier eigentlich auch eine Möglichkeit, einen Bericht zu bearbeiten nachdem er gespeichert ist?
```

**Nachricht 5**
```
Kein Approval, monatlich, Daten aktuell, Komplexität niedrig, Migration offen, Priorität niedrig.
```

**Was getestet wird:** Geht der Assistent auf system-fremde Fragen ein oder bleibt er fokussiert? Antwortet er sachlich auf die Meta-Fragen ohne abgelenkt zu werden?
