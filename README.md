# Boccia Battle — Versione 0.3

**Boccia Battle** è un minigioco 2D di boccia paralimpica sviluppato in Python con Pygame.

La Versione 0.3 trasforma il prototipo fisico in una **partita completa locale**, mantenendo la struttura modulare costruita nelle versioni precedenti.

## Cosa contiene la 0.3

- 4 bocce rosse e 4 bocce blu per ogni end;
- collisioni boccia-boccia;
- jack fisico e spostabile;
- attrito, velocità, massa e trasferimento dell'impulso;
- turni automatici in base alla distanza dal jack;
- calcolo reale del punteggio a fine end;
- 4 end regolamentari nella partita prototipo;
- punteggio totale;
- schermata riepilogo dopo ogni end;
- schermata risultato finale;
- tie-break automatico se il punteggio è pari dopo il quarto end;
- il colore che segna apre l'end successivo;
- configurazione separata in data/settings.json.

## Punteggio

A fine end:

1. viene individuato il colore con la boccia più vicina al jack;
2. viene trovata la migliore boccia dell'avversario;
3. il colore vincente ottiene un punto per ogni propria boccia che si trova più vicina al jack rispetto alla migliore boccia avversaria;
4. i punti vengono aggiunti al totale della partita.

Se le due migliori bocce risultano praticamente alla stessa distanza entro la tolleranza configurata, l'end assegna 0 punti.

## Partita

La configurazione predefinita usa **4 end**.

Se al termine del quarto end il totale è in parità, Boccia Battle avvia uno o più **tie-break** fino a quando un end produce un vantaggio nel punteggio totale.

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

- **Mouse**: mira;
- **Rotella mouse**: modifica la potenza;
- **Click sinistro** oppure **SPAZIO/INVIO**: lancia;
- **Click destro** oppure **C**: centra la mira;
- **← / →** oppure **A / D**: cambia direzione;
- **↑ / ↓** oppure **W / S**: cambia potenza;
- **N / SPAZIO / INVIO**: passa all'end successivo dalla schermata risultato;
- **R**: ricomincia la partita;
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
    │  ├─ player.py
    │  └─ scoring.py
    ├─ screens/
    │  ├─ game_screen.py
    │  └─ result_screen.py
    ├─ data/
    │  └─ settings.json
    ├─ requirements.txt
    └─ .gitignore

## Parametri principali

In data/settings.json puoi modificare:

- balls_per_player: numero di bocce per colore;
- ends: numero di end regolamentari;
- friction_deceleration: resistenza del campo;
- collision_restitution: elasticità degli urti;
- border_restitution: energia mantenuta negli urti con il bordo;
- boccia_mass e jack_mass: rapporto tra le masse;
- max_substeps: precisione della simulazione;
- tie_tolerance_px: tolleranza usata per considerare due migliori bocce praticamente equidistanti.

## Versioni stabili

- **v0.1-stable**: singolo tiro e fisica base;
- **v0.2-stable**: più bocce, collisioni e turni;
- **main**: sviluppo corrente.

## Prossimo obiettivo: Versione 0.4

La prossima fase introdurrà l'avversario controllato dal computer:

- analisi della situazione sul campo;
- scelta tra avvicinamento e bocciata;
- stima di direzione e potenza;
- errore controllato;
- livelli di difficoltà progressivi.

L'obiettivo è mantenere l'IA comprensibile e credibile, senza introdurre sistemi inutilmente complessi.
