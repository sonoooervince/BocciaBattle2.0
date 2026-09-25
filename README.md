# Boccia Battle — Versione 0.7

Boccia Battle è un minigioco 2D di boccia paralimpica sviluppato in Python con Pygame.

La Versione 0.7 rende operative tutte le voci principali del menu: partita contro il computer, torneo, allenamento e impostazioni.

## Modalità

### Gioca vs Computer

Partita completa contro l'IA con fisica condivisa, collisioni, jack dinamico, 4 bocce per parte, end, punteggio e tie-break.

### Torneo Settimanale

Sette partite consecutive contro livelli IA 5, 10, 18, 27, 36, 44 e 50. Si avanza soltanto vincendo.

### Allenamento

La modalità Allenamento permette di:

- effettuare tiri illimitati;
- mantenere più bocce sul campo e provare collisioni;
- cambiare liberamente profilo di boccia;
- spostare il jack in una posizione casuale con J;
- pulire le bocce con X;
- azzerare la sessione con R;
- vedere distanza dell'ultimo tiro e miglior distanza;
- confrontare i cinque profili fisici di boccia.

### Impostazioni

Le impostazioni sono salvate localmente in data/user_settings.json e permettono di scegliere:

- produttore/marca;
- profilo di boccia predefinito;
- livello IA da 1 a 50;
- numero di end da 1 a 8;
- tempo di pensiero dell'IA;
- visualizzazione delle linee di distanza.

## Marche reali

Il catalogo usa i nomi dei produttori indicati da World Boccia come Approved Ball Suppliers per il periodo 2025–2028:

- Apowatec
- Boccas Balls
- Bocha Brasil
- Bom de Bocha Esportes
- Handi Life Sport
- PolySports
- Ree Sport
- Tutti per Tutti / Prodigy Frontier
- Victory Sports

I nomi delle marche sono riferimenti testuali. Il progetto non include loghi proprietari e non attribuisce automaticamente caratteristiche fisiche diverse a un produttore senza dati tecnici verificati.

La marca e il profilo fisico sono quindi due scelte separate. Il profilo determina il comportamento nella simulazione; la marca identifica il produttore scelto dal giocatore.

Fonte di riferimento per i produttori: World Boccia, Approved Ball Suppliers 2025–2028.

## Profili fisici

Sono disponibili:

1. Super morbido
2. Morbide
3. Medie
4. Dura
5. Super duro

I profili modificano attrito, risposta agli urti e piccole variazioni di rotolamento.

## Avvio su Windows

Se pip non è installato:

    python -m ensurepip --upgrade

Installa le dipendenze:

    python -m pip install -r requirements.txt

Con Python 3.14 o superiore il progetto usa automaticamente pygame-ce, compatibile con lo stesso import `pygame`. Con Python fino alla 3.13 usa pygame classico.

Avvia il gioco:

    python main.py

Oppure usa avvia_boccia_battle.bat.

## Versioni stabili

- v0.1-stable: fisica base
- v0.2-stable: collisioni e turni
- v0.3-stable: partita locale completa
- v0.5-stable: IA e profili di boccia
- v0.6-stable: menu e Torneo Settimanale
- main: sviluppo corrente 0.7

## Nota sul matchmaking

game/competitive.py resta una struttura preparatoria. Il multiplayer online non è ancora implementato: non sono presenti server, account o lobby.

## Controlli automatici

Ogni push su main esegue:

- controllo sintattico;
- unit test;
- smoke test di menu, partita, torneo, allenamento e impostazioni;
- creazione dello ZIP giocabile.
