# Boccia Battle — Versione 0.2

Prototipo giocabile in Python/Pygame sviluppato per **Para Amici per le Bocce**.

La Versione 0.2 porta il progetto dal singolo tiro di prova a un vero **end sperimentale con due colori**, più bocce sul campo e collisioni fisiche.

## Novità della 0.2

- 4 bocce rosse e 4 bocce blu;
- tutte le bocce restano sul campo dopo il tiro;
- collisioni boccia-boccia;
- il jack è ora un corpo fisico e può essere colpito e spostato;
- trasferimento di velocità negli urti;
- correzione delle sovrapposizioni fra corpi;
- sotto-passi fisici dinamici per ridurre il tunneling ad alta velocità;
- attrito applicato a bocce e jack;
- turni automatici;
- dopo il primo tiro per parte, continua a giocare il colore con la boccia migliore più lontana dal jack;
- conteggio delle bocce rimanenti;
- indicazione provvisoria del colore più vicino;
- distanza della migliore boccia rossa e blu;
- contatori di collisione utili durante il test della fisica.

## Importante

La 0.2 **non è ancora la partita completa contro il computer**.

In questa versione Rosso e Blu vengono controllati entrambi sullo stesso PC. È intenzionale: prima verifichiamo bene fisica e turni. La 0.3 aggiungerà punteggio, end multipli e risultato partita; la 0.4 introdurrà l'avversario controllato dal computer.

La precedente Versione 0.1 resta conservata nel branch **v0.1-stable**.

## Avvio su Windows

Apri il Prompt dei comandi o PowerShell nella cartella del progetto.

### Ambiente virtuale consigliato

    py -m venv .venv
    .venv\Scripts\activate
    py -m pip install -r requirements.txt
    py main.py

### Avvio rapido

    py -m pip install pygame
    py main.py

## Controlli

- **Mouse**: muovi per mirare.
- **Rotella**: modifica la potenza.
- **Click sinistro** oppure **SPAZIO/INVIO**: lancia.
- **Click destro** oppure **C**: centra la mira.
- **← / →** oppure **A / D**: direzione.
- **↑ / ↓** oppure **W / S**: potenza.
- **R**: ricomincia l'end.
- **Esc**: esce.

## Struttura attuale

    BocciaBattle2.0/
    ├─ main.py
    ├─ game/
    │  ├─ boccia.py
    │  ├─ config.py
    │  ├─ field.py
    │  ├─ jack.py
    │  ├─ match.py
    │  ├─ physics.py
    │  └─ player.py
    ├─ screens/
    │  └─ game_screen.py
    ├─ data/
    │  └─ settings.json
    ├─ requirements.txt
    └─ .gitignore

## Parametri fisici

I valori principali sono in data/settings.json.

- friction_deceleration: resistenza del campo;
- border_restitution: energia mantenuta negli urti col bordo;
- collision_restitution: elasticità negli urti fra bocce e jack;
- stop_speed: soglia sotto la quale un corpo viene fermato;
- max_substeps: precisione massima della simulazione negli urti veloci;
- boccia_mass / jack_mass: rapporto di massa fra boccia e pallino.

Questi valori sono volutamente esterni al codice per poter tarare la sensazione di gioco.

## Prossimo obiettivo: Versione 0.3

La 0.3 costruirà sopra questa base:

- calcolo dei punti a fine end;
- più end;
- punteggio totale;
- schermata di risultato;
- vittoria/sconfitta;
- struttura della partita pronta per l'IA della 0.4.
