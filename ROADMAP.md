# Roadmap

**Fase corrente** · Valutazione dei modelli prima della Fase 8  
**Fasi approvate** · 1 — Creazione del sito Hugo, 2 — Archivio giornaliero e calendario, 3 — Primo generatore Python → Hugo, 4 — Primo collettore RSS reale, 5 — Database SQLite e deduplicazione, 6 — Ricerca dinamica per interessi, 7 — Prima selezione automatica senza AI

| Fase | Obiettivo | Stato |
| --- | --- | --- |
| 1 | Sito Hugo dimostrativo e avvio locale | Completata e approvata |
| 2 | Archivio giornaliero e calendario | Completata e approvata |
| 3 | Primo generatore Python → Hugo | Completata e approvata |
| 4 | Primo collettore RSS reale | Completata e approvata |
| 5 | Database SQLite e deduplicazione | Completata e approvata |
| 6 | Ricerca dinamica per interessi | Completata e approvata |
| 7 | Prima selezione automatica senza AI | Completata e approvata |
| 8 | Introduzione dell’intelligenza artificiale | Non iniziata. Selezione del modello in valutazione. |
| 9 | Integrazione dei video YouTube | Non iniziata |
| 10 | Ricerca YouTube per argomenti e notizie correlate | Non iniziata |
| 11 | Integrazione Instagram | Non iniziata |
| 12 | Automazione quotidiana | Non iniziata |
| 13 | Stabilizzazione e ottimizzazione | Non iniziata |
| 14 | Funzionalità avanzate future | Non iniziata |

## Decisioni della Fase 1

- Layout Hugo su misura e asset locali. I contenuti dimostrativi usano date fisse.
- Docker usa Hugo per la build e Nginx per servire il risultato statico. Compose pubblica la porta su loopback per impostazione predefinita.

## Verifiche Docker

- Con Docker Compose v5.7.0 sul motore Linux amd64 di Docker Desktop sono passati `docker compose config --quiet` e `docker compose up --build -d --wait`.
- Nginx ha restituito HTTP 200 per homepage, articolo e dieci asset con tipi MIME corretti. Entrambe le clip hanno risposto HTTP 206 alle richieste parziali.
- Le immagini di base pubblicano manifest per Linux amd64 e arm64. Il deploy sul server Debian 13 resta da effettuare seguendo il [README](README.md#deploy-su-debian-13).

## Fase 2

- Le edizioni sono pagine Hugo con data e contenuti nel front matter TOML. Homepage e pagina giornaliera condividono il layout. L’archivio genera in fase di build il calendario e i collegamenti tra le edizioni.
- Build Hugo e avvio Docker Compose verificati sul motore Linux amd64. Il test HTTP ha verificato sei pagine e dieci asset, incluse le richieste parziali alle clip.
- Verificati nel browser a 390 e 1440 px il layout responsive, i collegamenti della homepage, il calendario e la navigazione tra le edizioni.

## Fase 3

- Il publisher valida un file JSON per giornata e genera il Markdown di quella data con front matter JSON. La scrittura sostituisce il file in modo atomico. Gli input identici non richiedono una nuova scrittura e le edizioni precedenti in TOML restano consultabili.
- Il campione contiene dieci notizie e due clip per il 13 novembre 2026. In una copia temporanea è stata verificata anche la generazione di una nuova giornata e la sua inclusione nel calendario.
- I cinque test del publisher sono passati su Windows e in un container Python basato su Debian 13. Verificati anche build Hugo, avvio con Docker Compose, sei pagine e dieci asset via HTTP e l’edizione nel browser a 390 e 1440 px.

## Fase 4

- Raccolta manuale RSS 2.0 da NASA, ESA e KDE. Le notizie con data valida devono rientrare nelle 24 ore precedenti alla raccolta. Le card riportano fonte, data se disponibile, estratto e link originale.
- Il collaudo del 13 novembre 2026 ha raccolto sei notizie NASA. ESA e KDE hanno risposto senza notizie idonee nella finestra. I sei link hanno risposto HTTP 200.
- Dieci test passati su Windows e su Debian 13 in container. Build Hugo, avvio Compose e verifica nel browser a 390 e 1440 px eseguiti su una copia del sito per conservare l’edizione dimostrativa del 13 novembre.

## Fase 5

- SQLite conserva le notizie RSS distinte e lo storico per acquisizione. La prima migrazione è integrata nell’apertura del database. Il confronto usa URL normalizzati e una regola conservativa per titoli simili dello stesso dominio.
- Due raccolte reali del 13 novembre hanno registrato sei notizie nuove alla prima esecuzione e zero alla seconda. Il JSON rigenerato dalla prima acquisizione corrisponde byte per byte al risultato della seconda.
- Sedici test passati su Windows e su Debian 13 in container. Sul sito di prova servito da Compose hanno risposto HTTP 200 il briefing rigenerato, la homepage, l’archivio, entrambe le edizioni precedenti e l’articolo dimostrativo.

## Fase 6

- Il collettore combina i feed diretti con una ricerca Google News per ogni categoria configurata in `config/interests.yaml`. Finestra e limite per query sono configurabili. Lo storico SQLite registra query, conteggi ed errori.
- Il collaudo ha archiviato 106 articoli da 88 fonti, con risultati per tutte e cinque le categorie. La build Hugo di prova ha incluso dieci articoli nel briefing e reso consultabili le edizioni precedenti.
- Venti test passati su Windows e in un container Debian 13. Verificati anche migrazione dal database della Fase 5, deduplicazione tra feed diretto e Google News e recupero parziale dopo un timeout.

## Fase 7

- Il ranking usa parole chiave, recenza e priorità delle fonti con pesi configurabili. La selezione riserva un posto alla notizia migliore per ogni categoria disponibile e completa l’edizione in ordine di punteggio.
- Il 16 novembre la pipeline ha selezionato 15 notizie su 102 dalle cinque categorie in una copia di prova. Docker Compose ha servito la nuova edizione, la homepage, l’archivio e le tre edizioni precedenti.
- Ventiquattro test passati su Windows e in un container Debian 13. La corrispondenza per parole chiave può includere risultati fuori tema. Il file di ranking permette di escludere espressioni mirate.

## Valutazione prima della Fase 8

- Il confronto locale usa estratti controllati per verificare classificazione, JSON e riassunti italiani. La scelta del modello dipende dal risultato qualitativo e dalle misure sul Raspberry Pi 4. [Protocollo e risultati](docs/valutazione-modelli.md)

I requisiti di ciascuna fase sono in [CodexInstructions.md](CodexInstructions.md).
