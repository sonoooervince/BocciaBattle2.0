# Boccia Battle — Versione 0.9.1

Boccia Battle è un gioco 2D di boccia paralimpica in Python/Pygame, costruito attorno al regolamento World Boccia e a un sistema di progressione videoludico originale.

## Novità 0.9.1

### Collisioni complete

Tutte le bocce ancora legalmente in campo partecipano sempre alle collisioni, indipendentemente da colore, proprietario, ordine di lancio o stato di movimento. Il solver usa più iterazioni per sotto-step per propagare correttamente le collisioni a catena (A → B → C → D) e più sotto-step per impedire che un tiro veloce attraversi una boccia senza contatto. Il jack usa lo stesso sistema.

## Novità 0.9

### Store di set reali

Lo **STORE** contiene esclusivamente set di bocce realmente esistenti e verificati tramite World Boccia o cataloghi/store ufficiali dei produttori.

Il giocatore parte con **Handi Life Sport — Boccia Standard Pro** e può sbloccare altri set con il Gold ottenuto giocando.

Il Gold è esclusivamente valuta virtuale interna: non rappresenta il prezzo commerciale reale e non consente di acquistare fisicamente il prodotto.

Non sono presenti skin fantasy o palloni di altri sport.

### Progressione

Il profilo locale salva:

- XP;
- livello;
- rank;
- rating;
- Gold;
- vittorie e sconfitte;
- serie di vittorie;
- set posseduti;
- set equipaggiato;
- durezza scelta.

Vittorie e sconfitte assegnano XP e Gold. La progressione viene salvata in `data/player_profile.json`.

### Controllo MIRINO

In Impostazioni è possibile scegliere:

- **MIRINO** — si indica con il mouse il punto desiderato; il gioco calcola automaticamente direzione e potenza di base;
- **MANUALE** — direzione e potenza vengono regolate direttamente.

Entrambi usano la stessa fisica.

### 2 giocatori locali

La modalità **2 GIOCATORI LOCALI** permette a due persone di giocare sullo stesso PC, alternandosi sullo stesso mouse/tastiera.

Usa lo stesso rules engine dell'Individuale ufficiale:

- sorteggio;
- scelta rosso/blu;
- 4 end;
- 6 bocce;
- jack;
- cronometri;
- dead ball;
- penalty;
- tie-break;
- timeout.

## Regolamento World Boccia

La 0.9 mantiene il motore regolamentare introdotto nella 0.8, basato sulle World Boccia International Sport Rules 2025–2028 v1.2.1.

Vedi:

    docs/WORLD_BOCCIA_RULES_COVERAGE.md

## Ricerca sul Boccia Battle esistente

Le meccaniche pubblicamente documentate del gioco Boccia Battle di Wasabi Applications sono state analizzate come riferimento di game design. Le idee utili sono state reinterpretate senza copiare codice, asset, grafica o testi.

Vedi:

    docs/BOCCIA_BATTLE_MECHANICS_AUDIT.md

## Modalità

- Gioca vs Computer
- 2 Giocatori Locali
- Torneo Settimanale
- Allenamento
- Store
- Impostazioni

Il multiplayer online non viene mostrato come funzione finché non sarà realmente implementato con server, sincronizzazione, matchmaking e stanze private.

## Store reale — catalogo iniziale

Il catalogo include set/modelli verificati di:

- Apowatec
- Boccas Balls
- Bom de Bocha
- Handi Life Sport
- PolySports
- Ree Sport
- Tutti per Tutti / Prodigy Frontier
- Victory Sports

Bocha Brasil è riconosciuto tra i produttori World Boccia approvati 2025–2028 ma non viene inserito come prodotto nello store senza un nome di set commerciale verificato.

## Avvio Windows

Se necessario:

    python -m ensurepip --upgrade

Poi:

    python -m pip install -r requirements.txt
    python main.py

Con Python 3.14 viene usato automaticamente pygame-ce.

## Branch stabili

- v0.1-stable
- v0.2-stable
- v0.3-stable
- v0.5-stable
- v0.6-stable
- v0.7.1-stable
- v0.8-stable
- main — sviluppo 0.9

## Test

GitHub Actions esegue controllo sintattico, unit test, smoke test grafico e crea automaticamente lo ZIP giocabile.
