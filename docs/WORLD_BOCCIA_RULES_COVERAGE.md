# World Boccia 2025–2028 — copertura in Boccia Battle 0.8

Riferimento: World Boccia International Sport Rules 2025–2028 v1.2.1 (23/04/2026).

Questa tabella distingue fra **ENFORCED** (regola applicata dal motore), **VALIDATED** (vincolo controllabile sui dati virtuali), **ENCODED** (regola registrata nel rules engine per modalità future) e **DIGITAL N/A** (procedura fisica/amministrativa che non ha un equivalente utile in una partita locale).

| Sezione | Stato | Implementazione |
| --- | --- | --- |
| 1. Definizioni | ENCODED | Terminologia di lato, end, jack, dead ball, penalty e classi usata nei moduli regolamentari. |
| 2. Event types | ENCODED / ENFORCED | Individuale giocabile; Pair BC3, Pair BC4 e Team hanno formato, box, end, palline e tempi codificati. |
| 3. Tournament setup / court | ENFORCED | Campo 12,5×6 m, 6 box, V-line, croce, target box, scoreboard/HUD e timer. |
| 4. Equipment | VALIDATED | Controlli virtuali per rampa, seduta e conformità; oggetti fisici reali non possono essere misurati dal software. |
| 5. Boccia balls | VALIDATED / ENFORCED | Produttori, peso, circonferenza e requisiti di conformità; scala fisica usata nel campo. |
| 6. Warm up area | DIGITAL N/A | La logistica della Warm Up Area 95–40 minuti prima del match appartiene all'organizzazione del torneo, non alla partita locale. |
| 7. Call room | DIGITAL N/A / ENFORCED | Registrazione e accrediti non simulati; il sorteggio colore è applicato. |
| 8. Pre-match ball check | VALIDATED | Le bocce virtuali passano controlli equivalenti per costruzione; minimo 3 bocce legali codificato. |
| 9. Roles and responsibilities | ENCODED | Ruoli e vincoli SA/RO/Coach memorizzati; la partita locale controlla direttamente il lato umano. |
| 10. Play | ENFORCED | Jack, primo tiro, ordine, timer, pass, out, dead ball, jack sulla croce, equidistanza, scoring. |
| 11. Subsequent ends | ENFORCED | Intervallo massimo 60 secondi con chiamata a 15 secondi e Time. |
| 12. Disrupted end | ENFORCED | Snapshot prima del rilascio e ripristino esatto dell'ultimo stato legittimo. |
| 13. Tie-break | ENFORCED | Extra end, jack sulla croce, sorteggio del primo lato, alternanza nei tie-break successivi, punti esclusi dal totale. |
| 14. Post-match ball check | VALIDATED | Stesso sistema di conformità disponibile; una misura fisica reale resta compito dell'arbitro. |
| 15. Communication | DIGITAL N/A | Non esiste un canale Coach/SA/RO durante l'end, quindi le comunicazioni proibite non possono verificarsi nel single player. |
| 16. Violations | ENFORCED / ENCODED | Retraction/dead ball, penalty ball, cartellini e forfait sono nel rules engine; infrazioni corporee/rampa richiedono un oggetto fisico non presente nel 2D. |
| 17. Disputes | DIGITAL N/A | Il motore calcola posizioni e distanze numericamente; la procedura formale di protesta resta una procedura arbitrale reale. |
| 18. Officials' gestures/signs | PRESENTATION | Paddle/gesti fisici sono sostituiti da HUD, colore del turno, messaggi arbitro e punteggio. |
| 19. Medical timeout | ENFORCED | M: una volta per lato, massimo 10 minuti, cronometro di gara fermo. |
| 20. Technical timeout | ENFORCED | T: una volta per lato, massimo 10 minuti, cronometro di gara fermo. |

## Individuale: regole che cambiano direttamente il gameplay

La modalità principale applica 4 end, 6 bocce per atleta, box 3/4, tempi BC1–BC4, alternanza del jack rosso/blu, jack foul, primo tiro del servitore, ordine basato sulla boccia più vicina, equidistanza, dead balls, jack riposizionato, penalty ball e tie-break.

## Pair e Team

Le strutture ufficiali sono già codificate nel rules engine, ma l'interfaccia attuale è progettata per **un atleta umano contro un atleta IA**. Rendere Pair e Team realmente giocabili richiede gestione multi-atleta, box multipli, distribuzione personale delle bocce, capitano, sostituzioni/ruoli e BC3 Ramp Operator. Questi aspetti non vengono falsamente presentati come già giocabili.

## Principio del progetto

Boccia Battle deve applicare automaticamente tutte le regole che un motore digitale può conoscere con certezza. Dove il regolamento richiede una valutazione umana o un controllo di un oggetto fisico, il software fornisce il vincolo/validator ma non inventa un risultato.
