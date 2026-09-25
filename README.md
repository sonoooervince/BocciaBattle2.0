# Boccia Battle — Versione 0.6

**Boccia Battle** è un minigioco 2D di boccia paralimpica sviluppato in Python con Pygame.

La Versione 0.6 mantiene la fisica, la partita completa e l'avversario controllato dal computer, e aggiunge un vero **menu principale** e il **Torneo Settimanale giocabile**.

## Modalità disponibili

### Gioca vs Computer

Partita completa contro il computer con:

- 4 bocce per parte;
- 4 end regolamentari;
- tie-break automatico;
- collisioni boccia-boccia e boccia-jack;
- jack fisico e spostabile;
- scelta fra 5 profili di boccia;
- IA che usa lo stesso motore fisico del giocatore.

### Torneo Settimanale

Il torneo è composto da 7 partite complete consecutive.

| Round | Livello IA |
| ---: | ---: |
| 1 | 5 |
| 2 | 10 |
| 3 | 18 |
| 4 | 27 |
| 5 | 36 |
| 6 | 44 |
| 7 | 50 |

Per avanzare bisogna vincere la partita del round corrente. Una sconfitta elimina dal torneo. Vincendo il Round 7 si completa il torneo.

Il livello dell'IA cambia automaticamente tra una partita e la successiva, ma fisica e regole restano identiche per giocatore e computer.

## IA

Sono definiti **50 livelli di IA**.

La difficoltà cresce attraverso:

- precisione angolare;
- precisione della potenza;
- aggressività;
- profondità tattica.

L'IA non teletrasporta mai le bocce e non riceve vantaggi fisici. Decide angolo e potenza, poi il tiro viene eseguito dal normale motore fisico.

## Profili di boccia

Il giocatore può scegliere fra:

1. Super morbido
2. Morbide
3. Medie
4. Dura
5. Super duro

I profili modificano in modo controllato attrito, risposta alle collisioni e piccole variazioni di rotolamento.

Controlli:

- **1–5**: selezione diretta;
- **Q / E**: profilo precedente/successivo.

## Controlli di tiro

- **Mouse**: mira;
- **Rotella mouse**: potenza;
- **Click sinistro** oppure **SPAZIO/INVIO**: lancia;
- **Click destro** oppure **C**: centra la mira;
- **← / →** oppure **A / D**: direzione;
- **↑ / ↓** oppure **W / S**: potenza;
- **ESC**: torna al menu durante una partita;
- **R**: ricomincia una partita normale.

Nel Torneo Settimanale il tasto R è disabilitato per evitare di annullare liberamente un round in corso.

## Avvio su Windows

Su Windows usa il comando python.

Se pip non è installato:

    python -m ensurepip --upgrade

Poi installa le dipendenze:

    python -m pip install -r requirements.txt

Infine avvia:

    python main.py

In alternativa puoi usare:

    avvia_boccia_battle.bat

Il file BAT utilizza python e non richiede il comando py.

## Struttura principale

    BocciaBattle2.0/
    ├─ main.py
    ├─ game/
    │  ├─ ai.py
    │  ├─ boccia.py
    │  ├─ boccia_profiles.py
    │  ├─ competitive.py
    │  ├─ config.py
    │  ├─ field.py
    │  ├─ jack.py
    │  ├─ match.py
    │  ├─ physics.py
    │  ├─ player.py
    │  ├─ scoring.py
    │  └─ tournament.py
    ├─ screens/
    │  ├─ game_screen.py
    │  ├─ menu.py
    │  ├─ result_screen.py
    │  └─ tournament_screen.py
    ├─ tests/
    │  └─ test_tournament.py
    ├─ data/
    │  └─ settings.json
    └─ requirements.txt

## Versioni stabili

- v0.1-stable: fisica base;
- v0.2-stable: collisioni e turni;
- v0.3-stable: partita completa locale;
- v0.5-stable: IA, 50 livelli e profili di boccia;
- main: Versione 0.6.

## Matchmaking

game/competitive.py contiene soltanto la base logica per un futuro matchmaking.

La soglia dei 50 giocatori umani online e il fallback verso i bot **non costituiscono ancora un sistema multiplayer**. Non sono presenti server, account, lobby o connessioni online nella versione attuale.

## Controlli automatici

Ad ogni push su main, GitHub Actions esegue:

- controllo sintattico;
- test della progressione del Torneo Settimanale;
- smoke test headless di menu, partita e torneo;
- creazione dell'artefatto ZIP giocabile.

## Prossimi passi

Le aree successive da sviluppare sono:

- tattica più sofisticata per i livelli IA più alti;
- schermata impostazioni;
- modalità allenamento;
- rifinitura grafica e audio;
- salvataggio locale dei progressi;
- solo in una fase futura, eventuale multiplayer online.
