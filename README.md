# TheTomTimes

Giornale personale in italiano dedicato a tecnologia, scienza e cultura digitale. La homepage Hugo mostra l’edizione più recente. Nell’archivio puoi consultare le edizioni precedenti tramite il calendario o l’elenco.

## Avvio con Docker Compose

Dalla radice del repository, con Docker e il plugin Docker Compose:

```sh
docker compose up --build -d
```

Apri [http://localhost:8080/](http://localhost:8080/). Compose genera il sito con Hugo e lo serve tramite Nginx. Al primo avvio Docker scarica le immagini dei due strumenti. Il sito serve i propri asset in locale.

Di default la porta è pubblicata solo su loopback. Per provare il sito da un telefono sulla stessa rete privata, imposta `WEB_HOST` all’indirizzo IP del computer che ospita Docker in un file `.env` nella radice. Puoi impostare anche `WEB_PORT` se la porta 8080 è occupata. Ricrea il container con `docker compose up -d` e apri l’indirizzo del computer dal telefono.

### Deploy su Debian 13

Sul server servono Docker Engine e il plugin Docker Compose. Hugo gira nella fase di build del container. Il sito statico e gli asset sono inclusi nell’immagine Nginx.

Dalla radice della copia del repository sul server:

```sh
docker compose version
docker compose config --quiet
docker compose up --build -d
docker compose ps
curl --fail --silent --show-error --output /dev/null http://127.0.0.1:8080/
```

Con la porta predefinita, puoi provare il sito dal tuo computer tramite SSH, mantenendo la porta di Debian su loopback. Sostituisci `utente@server` con il tuo accesso SSH, esegui `ssh -N -L 8080:127.0.0.1:8080 utente@server` e apri [localhost:8080](http://localhost:8080/) sul tuo computer. Se hai cambiato `WEB_PORT`, usa quella porta nel controllo HTTP e come porta remota del tunnel.

Per arrestare il sito:

```sh
docker compose down
```

## Sviluppo con Hugo

Con Hugo **0.163.3**, dalla radice del repository:

```sh
hugo server --source site --renderToMemory
```

Apri [http://localhost:1313/](http://localhost:1313/). Per generare e verificare la versione statica in `site/public/`:

```sh
hugo --source site --minify --panicOnWarning
```

Le edizioni dimostrative sono in [site/content/daily/](site/content/daily/). Ogni file `YYYY-MM-DD.md` usa la stessa data nel nome e nel campo `date`. Il nome del file determina l’URL `/daily/YYYY-MM-DD/`, mentre la data determina l’ordine in homepage, archivio e calendario. Modifica l’articolo principale in [site/content/laboratorio-in-orbita.md](site/content/laboratorio-in-orbita.md).

## Generare un’edizione da JSON

Il publisher usa la libreria standard di Python 3.10 o successivo. Dalla radice del repository:

```sh
python3 backend/main.py --date 2026-11-13 --input examples/edition-2026-11-13.json
hugo --source site --minify --panicOnWarning
```

Su Windows puoi usare `python` al posto di `python3`. Modifica il [JSON di esempio](examples/edition-2026-11-13.json) e ripeti il comando per aggiornare la demo. Il publisher scrive `site/content/daily/2026-11-13.md`; a parità di input conserva il file esistente. Per un’altra giornata usa un altro file JSON e passa la stessa data nel JSON e in `--date`. Se usi Docker, esegui il publisher sulla copia del repository prima di `docker compose up --build -d`.

Lo [schema JSON](backend/schemas/edition.schema.json) descrive un oggetto per giornata:

- `date` e `title` indicano la data ISO `YYYY-MM-DD` e il titolo dell’edizione.
- `featured` è la notizia principale. `stories` contiene le altre notizie, nell’ordine in cui appaiono.
- Ogni notizia contiene `title`, `category` e `summary`. L’immagine locale `image` è facoltativa. Il campo facoltativo `slug` collega una pagina già presente in `site/content/<slug>.md`.
- Le notizie RSS aggiungono `source_name`, `original_url` e, quando disponibile, `published_at` in UTC. Le edizioni di questo tipo impostano `kind` a `rss`.
- `videos` è facoltativo. Ogni clip contiene `title`, `category`, `summary`, `image` e `source`. Le immagini si trovano in `site/static/img/` e le clip MP4 in `site/static/video/`. Nel JSON i percorsi sono relativi a `site/static/`.

Il comando controlla anche che la data esista, gli asset e gli articoli collegati siano presenti e i titoli delle notizie siano distinti. Se la validazione fallisce, restituisce un errore e lascia l’edizione esistente al suo posto. Le edizioni generate usano front matter JSON; Hugo continua a leggere quelle esistenti in TOML.

```sh
python3 -m unittest discover -s tests -p "test_*.py" -v
```

## Raccogliere notizie RSS

Le fonti dirette iniziali sono NASA, ESA e KDE. Modifica [config/sources.json](config/sources.json) oppure passa un altro file con `--sources`. Usa feed RSS 2.0 pubblici in HTTPS sulla porta 443 e inserisci l’URL finale del feed. La raccolta include anche una query Google News per ogni categoria in [config/interests.yaml](config/interests.yaml).

Per leggere gli interessi YAML, installa PyYAML nell’ambiente Python del progetto. Su Debian:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
```

Usa `.venv/bin/python` nei comandi seguenti quando lavori nel virtual environment. Su Windows puoi usare `.venv\Scripts\python.exe`. Per raccogliere con i soli feed diretti, usa `--rss-only`.

Imposta la data del briefing nel formato `YYYY-MM-DD`, quindi esegui in una shell su Debian:

```sh
giorno=$(TZ=Europe/Rome date +%F)
python3 -m backend.collectors.rss --date "$giorno" --output "output/edition-rss-$giorno.json" &&
python3 backend/main.py --date "$giorno" --input "output/edition-rss-$giorno.json" &&
docker compose up --build -d
```

Il secondo comando scrive l’edizione di quella data. Se esiste già, la rigenera. Su Windows usa `python` e passa la data esplicita a entrambi i comandi. Apri quindi `/daily/YYYY-MM-DD/` sul sito.

I feed diretti usano le 24 ore precedenti all’esecuzione, indipendentemente dalla data scelta per il briefing. Il briefing ordina le notizie con data dalla più recente e considera in coda quelle dei feed diretti senza una data valida, fino a dieci elementi. Le card riportano un estratto testuale quando il feed offre una descrizione utile. Con una fonte in errore il comando continua con le altre. Se nessuna produce risultati idonei, il JSON esistente resta disponibile e il comando termina con un errore.

### Configurare la ricerca per interessi

Ogni interesse associa una `category` a una lista di `keywords`. La query cerca le espressioni esatte in alternativa tra loro. `language` e `region` impostano l’edizione di Google News. `window_hours` imposta la finestra delle query da 1 a 168 ore e `max_results_per_query` il massimo da 1 a 100 risultati idonei, prima della deduplicazione. La ricerca richiede una data di pubblicazione valida. Passa `--interests percorso.yaml` per usare un’altra configurazione.

Il log della raccolta e `backend.database inspect` riportano le query, i conteggi per fonte e gli eventuali errori. Le notizie Google News riportano la testata dichiarata nel feed e usano il collegamento fornito dal servizio. Quando lo stesso articolo compare anche in un feed diretto durante la stessa raccolta, la deduplicazione può riconoscerlo dal dominio della testata e dal titolo, e conservare il collegamento diretto.

## Selezionare e pubblicare il briefing

Dalla radice del repository, avvia manualmente la pipeline con Docker Compose attivo e PyYAML installato. Sostituisci la data con quella dell’edizione da pubblicare.

```sh
python3 -m backend.pipeline --date 2026-11-16
```

La pipeline raccoglie i feed, legge l’intera acquisizione da SQLite, salva `output/edition-ranked-2026-11-16.json`, genera la pagina Hugo e aggiorna il servizio `web` con Compose. Apri [l’edizione del 16 novembre](http://localhost:8080/daily/2026-11-16/) o usa la data che hai passato al comando. Su Windows usa `python`. Per provare nuovi pesi su una raccolta già salvata, aggiungi `--run-id ID` con la relativa data del briefing. Il calcolo usa l’ora dell’acquisizione per riprodurre la recenza.

Modifica [config/ranking.yaml](config/ranking.yaml) per scegliere da 10 a 20 notizie, impostare la finestra di recenza, cambiare i pesi e assegnare priorità alle testate. I pesi predefiniti sono 60 per gli interessi, 30 per la recenza e 10 per la fonte. Una parola chiave distinta vale due punti nel titolo o un punto nell’estratto, fino a quattro punti per categoria. La pipeline usa la categoria con più punti e, in caso di parità, preferisce quella rilevata dal feed se coincide. La recenza decresce fino a zero lungo la finestra configurata e vale zero per le notizie senza data. Le priorità delle fonti vanno da 0 a 100.

La selezione esclude le notizie senza parole chiave corrispondenti e quelle che contengono le espressioni in `exclude_keywords`. Riserva un posto alla notizia migliore di ciascuna categoria disponibile, poi riempie i posti rimanenti seguendo il punteggio. Il briefing finale è ordinato per punteggio. Il log elenca punteggio, categoria e titolo per ogni notizia selezionata. Se le notizie pertinenti sono meno del limite configurato, l’edizione contiene solo quelle disponibili.

## Consultare SQLite e rigenerare un briefing

Il collettore crea `data/news.sqlite3` e applica le migrazioni all’apertura. Il database conserva tutte le notizie idonee e registra per ogni acquisizione l’ora, la data del briefing, le fonti, gli eventuali errori e il numero di articoli nuovi. Il file è locale ed è escluso da Git. Su Debian conserva la cartella `data/` tra un deploy e l’altro o passa un percorso persistente con `--db`.

Per identificare una notizia, il collettore normalizza dominio, porta predefinita e codifica del percorso. Rimuove il frammento e parametri di tracciamento come `utm_*`, `fbclid` e `gclid`, conservando i parametri funzionali e il link originale. Per URL diversi, confronta titoli di lunghezza da 32 a 300 caratteri sullo stesso dominio entro 48 ore. Associa una notizia esistente solo se c’è un unico titolo con almeno il 94% di somiglianza e gli stessi numeri. Il database conserva la prima versione acquisita di ciascuna notizia.

```sh
python3 -m backend.database inspect --date 2026-11-13
python3 -m backend.database inspect --run-id 1
python3 -m backend.database regenerate --date 2026-11-13 --output output/edition-rss-2026-11-13.json
```

Usa una data presente nel tuo storico. `regenerate` usa l’ultima acquisizione con notizie per quella data. Per ricostruirne una specifica, aggiungi `--run-id` con il suo ID. Passa il JSON al publisher e ricostruisci il sito con i comandi già descritti. Per un database alternativo, passa `--db /percorso/news.sqlite3` al collettore e subito prima di `inspect` o `regenerate`.

## Verifica della demo

- Dalla homepage apri **Archivio**. Nel calendario passa da novembre a ottobre 2026 e scegli il 30 ottobre. I giorni con un’edizione sono evidenziati e cliccabili.
- Apri le edizioni precedente e successiva dai link a fondo pagina. L’archivio elenca anche le categorie di ogni edizione.
- Apri la storia in primo piano e torna alla sua edizione con **Torna all’edizione**.
- Passa al tema scuro e ricarica la pagina per verificare che la preferenza venga ricordata.
- Prova le due clip e controlla che le card compaiano in una colonna a 390 px e in tre colonne a 1440 px.

Con il sito avviato, puoi verificare anche URL, calendario, collegamenti e asset via HTTP con Python 3:

```sh
python3 tests/check_site.py http://127.0.0.1:8080/
```

Se usi il server di sviluppo Hugo, passa la porta 1313.

Lo stato delle fasi è in [ROADMAP.md](ROADMAP.md).
