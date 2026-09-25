# Boccia Battle — Versione 0.1

Primo prototipo giocabile in Python/Pygame per **Para Amici per le Bocce**.

## Cosa contiene la 0.1

- finestra Pygame;
- campo 2D;
- jack statico;
- una boccia;
- mira con mouse o tastiera;
- potenza regolabile;
- lancio con velocità iniziale reale;
- movimento frame-independent;
- attrito/decelerazione;
- collisione e rimbalzo sui bordi;
- distanza finale dal jack;
- parametri fisici modificabili in `data/settings.json`.

> Nella 0.1 la boccia **non collide ancora con il jack**: questa funzione viene introdotta nella 0.2 insieme alle collisioni fra bocce.

## Avvio su Windows

Apri il Prompt dei comandi o PowerShell dentro la cartella `BocciaBattle_v0_1`.

### Metodo consigliato: ambiente virtuale

```bat
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
py main.py
```

### Metodo rapido

```bat
py -m pip install pygame
py main.py
```

## Controlli

- **Mouse**: muovi il puntatore per mirare.
- **Rotella mouse**: aumenta/diminuisce la potenza.
- **Click sinistro**: lancia.
- **Click destro**: centra la mira.
- **← / →** oppure **A / D**: cambia direzione.
- **↑ / ↓** oppure **W / S**: cambia potenza.
- **Spazio / Invio**: lancia.
- **R**: nuovo tiro dalla posizione iniziale.
- **Esc**: esce dal gioco.

## Struttura

```text
BocciaBattle_v0_1/
├─ main.py
├─ game/
│  ├─ boccia.py
│  ├─ config.py
│  ├─ field.py
│  ├─ jack.py
│  └─ physics.py
├─ screens/
│  └─ game_screen.py
├─ data/
│  └─ settings.json
├─ assets/
│  ├─ images/
│  ├─ sounds/
│  └─ fonts/
└─ requirements.txt
```

## Parametri da provare

In `data/settings.json`:

- `friction_deceleration`: più alto = la boccia si ferma prima;
- `border_restitution`: più alto = rimbalza di più;
- `min_launch_speed` / `max_launch_speed`: intervallo di velocità legato alla potenza;
- `stop_speed`: soglia sotto cui la boccia viene considerata ferma.

Questi parametri sono volutamente esterni al codice per permettere di tarare la sensazione di gioco senza riscrivere la fisica.

## Passo successivo: 0.2

La prossima versione aggiungerà, senza buttare via la 0.1:

- più bocce contemporaneamente;
- collisioni boccia-boccia;
- jack dinamico e spostabile;
- gestione elementare dei turni;
- misura della boccia più vicina al jack.
