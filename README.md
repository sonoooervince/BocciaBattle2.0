# Boccia Battle — Versione 0.8

**Boccia Battle** è un gioco 2D di boccia paralimpica in Python/Pygame.

La Versione 0.8 introduce un motore regolamentare basato sulle **World Boccia International Sport Rules 2025–2028 v1.2.1**, aggiornate il 23 aprile 2026.

## Partita ufficiale Individuale

La modalità **Gioca vs Computer** applica il formato Individuale:

- 4 end regolamentari;
- 6 bocce colorate per atleta;
- rosso nel box 3 e blu nel box 4;
- sorteggio iniziale: chi vince sceglie rosso o blu;
- rosso serve il jack negli end dispari, blu negli end pari;
- jack lanciato fisicamente;
- jack non valido passato al lato successivo della sequenza;
- primo tiro colorato al lato che ha lanciato un jack valido;
- lato senza la boccia più vicina continua a giocare;
- gestione delle bocce equidistanti;
- possibilità di rinunciare alle bocce rimanenti;
- dead ball per bocce fuori o che non entrano nell'area di gioco;
- jack uscito/non valido durante l'end riposizionato sulla croce;
- punteggio ufficiale, compresa l'equidistanza;
- tie-break con jack sulla croce;
- punti del tie-break esclusi dal totale regolamentare;
- intervallo massimo di un minuto tra gli end;
- penalty ball verso il target box 35 × 35 cm;
- medical e technical timeout;
- gestione di cartellini e forfait nel rules engine;
- snapshot esatto per il ripristino di un disrupted end.

## Tempi ufficiali

Il tempo è per lato e per end, compreso il lancio del jack:

- **BC1:** 4:30
- **BC2:** 3:30
- **BC3:** 6:00
- **BC4:** 3:30

Il gioco annuncia le soglie di 1 minuto, 30 secondi, 10 secondi e Time.

## Campo

Il campo è scalato sulle misure ufficiali:

- 6 m × 12,5 m;
- 6 box da 1 m × 2,5 m;
- area di gioco da 10 m;
- V-line;
- croce;
- target box interno da 35 × 35 cm.

Le bocce usano una scala fisica compatibile con le dimensioni regolamentari; a video vengono disegnate leggermente più grandi per restare leggibili.

## Penalty ball

Quando il rules engine assegna una penalty ball:

1. il punteggio delle bocce sul campo viene memorizzato;
2. il campo viene liberato;
3. ogni penalty ball viene giocata separatamente;
4. il tempo viene impostato a 1 minuto;
5. la boccia deve fermarsi interamente nel target box senza toccarne il bordo esterno;
6. ogni penalty riuscita aggiunge un punto;
7. se entrambi i lati hanno penalty ball, l'ordine alterna a partire dal lato che ha ricevuto la prima penalità.

## Timeout

Durante una partita:

- **M** richiama un medical timeout;
- **T** richiama un technical timeout;
- ciascun tipo è disponibile una sola volta per lato;
- il limite è 10 minuti;
- il cronometro di gara resta fermo;
- **INVIO** riprende prima dello scadere;
- **F** durante il timeout dichiara l'impossibilità a proseguire e applica il forfait.

## Classi

In **Impostazioni** è possibile selezionare BC1, BC2, BC3 o BC4. La classe imposta il tempo ufficiale dell'Individuale.

Le regole fisiche di attrezzature specifiche (per esempio la rampa BC3, la posizione dell'operatore o l'altezza reale della seduta) sono memorizzate nel modulo di conformità ma non vengono simulate come oggetti corporei nel gioco 2D.

## Conformità di bocce e attrezzature

Il rules engine contiene controlli per:

- produttore autorizzato;
- peso nominale 275 g ± 12 g;
- circonferenza 270 mm ± 8 mm;
- colore, forma e materiali;
- condizioni e manomissioni;
- requisiti principali delle rampe;
- altezza della seduta per le classi interessate;
- numero minimo di bocce approvate necessario per iniziare una partita.

Nel gioco le bocce virtuali vengono create conformi per costruzione. Il software non pretende di sostituire una vera verifica arbitrale di un oggetto fisico.

## Marche

Il catalogo usa i produttori approvati World Boccia 2025–2028:

- Apowatec
- Boccas Balls
- Bocha Brasil
- Bom de Bocha Esportes
- Handi Life Sport
- PolySports
- Ree Sport
- Tutti per Tutti / Prodigy Frontier
- Victory Sports

I nomi sono riferimenti testuali. Non vengono utilizzati loghi proprietari e non vengono attribuite caratteristiche fisiche specifiche a una marca senza dati tecnici verificati.

## Altre modalità

### Torneo Settimanale

7 round contro IA progressivamente più forti: livelli 5, 10, 18, 27, 36, 44 e 50. Ogni round usa la partita ufficiale Individuale.

### Allenamento

Modalità libera per:

- tiri ripetuti;
- collisioni;
- confronto tra profili di boccia;
- riposizionamento del jack;
- misura dell'ultimo tiro e del miglior tiro.

### Impostazioni

Permette di scegliere:

- marca;
- profilo della boccia;
- livello IA 1–50;
- classe BC1–BC4;
- tempo visivo di pensiero IA;
- linee di distanza.

## Copertura del regolamento

La mappatura dettagliata di tutte le sezioni del regolamento si trova in:

    docs/WORLD_BOCCIA_RULES_COVERAGE.md

Le regole che determinano l'esito della partita sono applicate dal motore. Le procedure puramente reali/organizzative — accrediti, personale di call room, controllo fisico con bilancia/calibro, presenza del medico, firme e proteste formali — sono rappresentate come validazioni o metadati e non come attese artificiali nel videogioco.

## Avvio su Windows

Se pip non è installato:

    python -m ensurepip --upgrade

Installa le dipendenze:

    python -m pip install -r requirements.txt

Con Python 3.14 o superiore viene usato automaticamente **pygame-ce**, mantenendo lo stesso import `pygame`.

Avvia:

    python main.py

Oppure:

    avvia_boccia_battle.bat

## Versioni stabili

- v0.1-stable — fisica base
- v0.2-stable — collisioni e turni
- v0.3-stable — partita locale completa
- v0.5-stable — IA e profili
- v0.6-stable — menu e torneo
- v0.7.1-stable — campo ufficiale, prima del rules engine
- main — Versione 0.8

## Test automatici

GitHub Actions controlla:

- sintassi;
- compatibilità Python 3.14;
- formati Individuale/Pair/Team;
- tempi per classe;
- jack e V-line;
- dead ball e fuori campo;
- equidistanza;
- scoring e tie-break;
- penalty ball;
- target box;
- scala delle bocce;
- timeout;
- conformità attrezzature;
- disrupted end;
- menu, partita, torneo, allenamento e impostazioni;
- creazione dello ZIP giocabile.

## Fonte regolamentare

World Boccia — **International Sport Rules 2025–2028 v1.2.1**, updated 23 April 2026.
