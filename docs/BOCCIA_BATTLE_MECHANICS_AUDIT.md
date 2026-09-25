# Boccia Battle 2.0 — audit delle meccaniche del gioco Wasabi

Ricerca effettuata sulle schede pubbliche di Boccia Battle di Wasabi Applications su Google Play/App Store e sui cataloghi World Boccia/produttori.

## Meccaniche osservate e nostra implementazione

| Meccanica osservata | Boccia Battle 2.0 |
| --- | --- |
| Mira semplice tramite punto bersaglio | Implementata come modalità **MIRINO**: il mouse indica il punto desiderato e il motore calcola una potenza di base usando attrito e distanza. Resta disponibile il controllo manuale. |
| Fisica della boccia | Motore fisico proprietario del progetto, con profili di durezza, collisioni, jack dinamico e regole World Boccia. |
| Più avversari IA | Il progetto mantiene **50 livelli IA**, con precisione, errore, profondità tattica e aggressività progressive. |
| Vs AI | Implementato con regolamento World Boccia Individuale. |
| 2 giocatori sullo stesso dispositivo | Implementato come **2 GIOCATORI LOCALI**, con sorteggio e alternanza automatica sullo stesso PC. |
| Rank/progressione | Implementato con XP, livelli e rank originali del progetto. |
| Rating | Implementato come rating locale del profilo. |
| Gold | Implementato come valuta guadagnata giocando; non è venduta con denaro reale. |
| Collezione/store di palle | Sostituita da uno **store esclusivamente di set di bocce reali**. |
| XP multiplier / Gold pack | Non copiati come acquisti: il progetto non richiede microtransazioni. |
| Online PvP | Non esposto nel menu finché non esiste un backend reale e testato. |
| Stanza privata/parola segreta | Prevista solo quando il multiplayer online sarà realmente operativo. |
| Ads / rimozione ads | Non adottati. |

## Principio di originalità

Vengono adottate idee funzionali comuni dei videogiochi sportivi — progressione, valuta, rank, matchmaking, mira semplificata, hot-seat — ma non vengono copiati codice, grafica, testi, nomi di rank, asset, layout o altri elementi espressivi proprietari di Wasabi Applications.

## Store: regola non negoziabile

Lo store contiene soltanto set realmente esistenti verificati da almeno una fonte attendibile:

- elenco/licensing World Boccia;
- listino ufficiale World Boccia del produttore;
- catalogo o store ufficiale del produttore.

Nessuna skin fantasy, pallone da calcio, basket, bowling, biliardo o altro oggetto estraneo alla boccia.

Il costo in **Gold** è esclusivamente un costo di sblocco virtuale del videogioco e non rappresenta il prezzo di vendita reale.

## Catalogo iniziale verificato

Produttori rappresentati:

- Apowatec
- Boccas Balls
- Bom de Bocha
- Handi Life Sport
- PolySports
- Ree Sport
- Tutti per Tutti / Prodigy Frontier
- Victory Sports

Sono presenti, tra gli altri, TOKYO, CONNECT Pro, 820R Plus, RAIJIN-R, Standard Pro, Superior Classic, Superior Supersoft, Superior Shine, LEDO Suede, Apollo, Ares, Hermes, Dionysus, Zeus, Dream, Boccas Brasil, Póvoa, T2020 ed Elite.

Bocha Brasil è un produttore World Boccia approvato 2025–2028, ma non viene aggiunto allo store finché non viene verificato un nome di set commerciale preciso da una fonte accessibile. È preferibile avere un catalogo leggermente più piccolo piuttosto che inventare un prodotto.
