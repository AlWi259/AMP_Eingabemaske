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

---

## Persona 4 – Lena Hartmann, Finanzen

Kooperativ, redselig, gibt viel Kontext. Deckt alle Felder inkl. der neuen Pflichtfelder ab. Ca. 10 Nachrichten.

**Nachricht 1**
```
Ich möchte den "Monatlichen Liquiditätsbericht" erfassen. Das ist ein Bericht, den wir seit 2019 jeden Monat erstellen – er zeigt die Liquiditätssituation des Konzerns aufgeteilt nach Gesellschaften, mit einem Soll-Ist-Vergleich und einer Forecast-Komponente für die nächsten 90 Tage. Den schauen sich vor allem CFO und Treasury-Leitung an.
```

**Nachricht 2**
```
Ich bin die Verantwortliche, Lena Hartmann, Abteilung Finanzen. Für technische Fragen ist Herr Zimmermann aus der IT zuständig, der betreut unsere ganzen SSRS-Strecken.
```

**Nachricht 3**
```
Wir ziehen die Daten aus SAP HANA, haben aber auch eine Excel-Tabelle die manuell gepflegt wird mit den Planwerten – das ist eigentlich eine zweite Quelle die immer mit rein muss. Das Tool ist SSRS, der Output ist ein PDF das per E-Mail an den Verteiler geht.
```

**Nachricht 4**
```
Gateway-Verbindung ja, über den On-Premises Data Gateway. Aber die Planwerte-Excel muss ich jeden Monat manuell hochladen bevor der Bericht läuft – das kostet mich ca. 2-3 Stunden. Der Rest ist dann automatisch.
```

**Nachricht 5**
```
Der Bericht läuft monatlich, immer zum 5. Werktag. Die Daten aus SAP sind tagesfrisch, die Planwerte sind natürlich Jahresplanung also älter – aber das ist so gewollt. Als Berichtstyp würde ich "Finanzbericht" sagen.
```

**Nachricht 6**
```
Nach Änderungen am Bericht brauche ich immer ein Approval vom CFO direkt, also Management-Approval. Das letzte formale Review war glaube ich März 2025, da haben wir die Forecast-Logik überarbeitet.
```

**Nachricht 7**
```
Der Bericht ist komplex – wir haben mehrstufige Konsolidierungslogik drin und die Planwert-Integration macht das fehleranfällig. Ich würde "Hoch" sagen. Den Ablageort könnte ich noch ergänzen: der liegt im SSRS-Workspace "Finance Reporting / Treasury".
```

**Nachricht 8**
```
Migration: das ist noch offen, wir haben das noch nicht angefasst. Priorität würde ich als "Kritisch" einstufen, weil das ein Bericht ist den der CFO persönlich jeden Monat anfordert. Aufwand für die Migration schätze ich auf 10-12 Personentage, allein wegen der Planwert-Anbindung.
```

**Nachricht 9**
```
Filter gibt es schon – man kann nach Gesellschaft filtern und nach Zeitraum. Das ist über Parameter in SSRS gelöst.
```

**Nachricht 10**
```
Bemerkungen: Wichtig zu wissen ist, dass die Planwert-Excel eine kritische Abhängigkeit ist – wenn die nicht rechtzeitig aktualisiert wird, stimmt der Forecast-Teil nicht. Das sollte bei der Migration unbedingt berücksichtigt werden. Ansonsten gibt es nichts weiter.
```

---

## Persona 5 – „Der Springer" (Frank Neumann, Einkauf)

Antwortet nie direkt auf die gestellte Frage. Beantwortet Vorfragen, springt zu anderen Themen, gibt nützliche Infos versteckt in irrelevanten Sätzen. Widerspricht sich. Stellt Gegenfragen. Testet ob der Assistent Informationen aus indirekten Antworten extrahiert und Widersprüche erkennt.

**Nachricht 1** *(auf "Wie heißt der Bericht?")*
```
Also das ist schon eine interessante Frage. Wir haben da eigentlich mehrere Berichte im Einkauf, das ist so gewachsen über die Jahre. Den den ich meine haben wir von einem Kollegen übernommen der 2021 in Rente gegangen ist. Der hatte das alles irgendwie in Excel gebaut, sehr komplex. Jetzt läuft das irgendwie halb automatisch. Wir nennen das intern eigentlich "die Einkaufsauswertung".
```

**Nachricht 2** *(auf "Was genau zeigt die Einkaufsauswertung?")*
```
Ja also, ich schick Ihnen da gleich mal ein Beispiel rüber... ach ne, ich hab das gerade nicht zur Hand. Im Grunde geht es um Lieferantenperformance. Bestellmengen, Lieferzeiten, Reklamationsquoten. Das geht an unseren Einkaufsleiter und manchmal auch ans Management wenn die Zahlen schlecht sind. Ich bin übrigens seit 14 Jahren im Einkauf, kenne das Thema also gut.
```

**Nachricht 3** *(auf "Wer ist fachlich verantwortlich?")*
```
Da müssten Sie eigentlich Frau Köster fragen, die macht das eigentlich. Aber die ist gerade im Urlaub bis Ende des Monats. Ich mache das in der Zwischenzeit, und Herr Dallmann aus der IT hat auch immer mal was dran gemacht. Eigentlich sind wir das alle drei irgendwie, je nachdem was anfällt.
```

**Nachricht 4** *(auf "Welches Tool wird verwendet?")*
```
Also früher war das Excel, ganz klar. Dann haben wir mal probiert das in Power BI zu machen, das war so 2022 glaube ich. Aber dann haben wir das wieder zurückgebaut weil die Verbindung nicht funktioniert hat. Jetzt ist das wieder Excel, aber ein bisschen anders aufgebaut als vorher. Haben Sie eigentlich auch die Möglichkeit, direkt Daten zu importieren hier?
```

**Nachricht 5** *(auf "Woher kommen die Daten?")*
```
Das kommt aus SAP, soweit ich weiß. Oder war das SQL Server? Ich glaube Herr Dallmann hat da mal was umgestellt. Auf jeden Fall irgendwas aus der IT-Infrastruktur. Die Zahlen stimmen meistens, also irgendwie kommt das schon richtig an. Ach so und der Output – das ist eine Excel-Datei die ich dann per Mail rausschicke, jeden Monat.
```

**Nachricht 6** *(auf "Gibt es eine Gateway-Verbindung?")*
```
Keine Ahnung was das ist ehrlich gesagt. Ich drück immer auf "Aktualisieren" und dann lädt das. Manchmal kommt eine Fehlermeldung dann ruf ich Herrn Dallmann an. Wir haben übrigens auch noch einen zweiten Bericht den wir für die Geschäftsführung machen, der ist aber ganz anders. Den sollten wir vielleicht auch noch erfassen?
```

**Nachricht 7** *(auf "Wie viel manueller Aufwand steckt drin?")*
```
Also ich würde sagen, das kostet mich so einen halben Tag im Monat. Ich muss die Rohdaten aus SAP rausziehen – das geht nicht automatisch – dann in die Excel einfügen, ein paar Formeln überprüfen und dann noch die Grafiken anpassen die sich manchmal komisch verhalten. Ach ja, und Frau Köster hat eigentlich immer noch ein Approval gemacht bevor wir das rausschicken. Das machen wir aber nicht immer, kommt drauf an wer Zeit hat.
```

**Nachricht 8** *(auf "Wann war das letzte formale Review?")*
```
Review? Wir schauen eigentlich jedes Mal drauf wenn wir es fertig haben. Ob Sie ein formales meinen... da bin ich mir nicht sicher. Ich glaube 2024 haben wir mal was geändert, irgendwann im Sommer. Oder war das 2023? Ich find das nicht mehr. Eigentlich passiert da nie was, der läuft schon immer so.
```

**Nachricht 9** *(auf "Wie komplex ist der Bericht?")*
```
Der ist gar nicht so schwer zu verstehen, also inhaltlich. Aber technisch... die Formeln sind schon wild. Mein Vorgänger hat da irgendwelche verschachtelten INDEX-MATCH gebaut die ich ehrlich gesagt nicht ganz durchblicke. Wenn was kaputtgeht ruf ich die IT an. Ich würde sagen mittel? Oder hoch? Kommt drauf an wen Sie fragen.
```

**Nachricht 10** *(auf "Wie ist der Migrationsstatus und was ist die Priorität?")*
```
Migration wäre schön, ich würde das gerne in Power BI haben. Das haben wir vor zwei Jahren schon mal probiert aber dann aufgehört. Jetzt wäre eigentlich ein guter Zeitpunkt. Priorität – ich würde sagen wichtig, aber nicht super dringend. Wir kommen ja irgendwie durch damit. Achso und ich wollte noch sagen: der IT-Ansprechpartner ist offiziell Herr Dallmann, Thomas Dallmann, der kennt den Bericht am besten von der Technikseite.
```

**Was getestet wird:**
- Extrahiert der Assistent "die Einkaufsauswertung" als Berichtsname obwohl nie direkt gefragt?
- Erkennt er den Widerspruch Excel → Power BI → Excel und fragt nach?
- Löst er die "wir sind alle drei zuständig"-Situation auf und pinnt einen Besitzer fest?
- Klassifiziert er "Gateway-Verbindung: Unbekannt" aus der Fehlermeldungs-Antwort?
- Nimmt er den IT-Ansprechpartner aus Nachricht 10 mit, obwohl er beiläufig am Ende kommt?
- Bleibt er beim zweiten-Bericht-Ablenkungsmanöver (Nachricht 6) fokussiert?
- Erkennt er "Fachbereich" als Approval-Typ aus "Frau Köster macht das Approval, aber nicht immer"?
