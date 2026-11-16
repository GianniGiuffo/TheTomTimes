# Daily Briefing — Giornale personale intelligente self-hosted

## 1. Obiettivo del progetto

Voglio sviluppare un sito web personale realizzato principalmente con **Hugo**, ospitato sul mio server Debian tramite Docker.

Il sito deve essere un giornale personale intelligente, aggiornato automaticamente ogni mattina, capace di raccogliere, selezionare e organizzare notizie e contenuti multimediali sulla base dei miei interessi.

Il risultato finale dovrà comprendere:

- Articoli provenienti da fonti affidabili.
- Ricerca di notizie per argomenti di interesse.
- Selezione e riassunti tramite intelligenza artificiale.
- Video YouTube e Shorts informativi.
- Reel Instagram provenienti da account selezionati.
- Collegamenti tra notizie e video che le approfondiscono.
- Homepage quotidiana.
- Archivio delle edizioni precedenti.
- Calendario navigabile.
- Pubblicazione automatica.

### Principio fondamentale: sviluppo incrementale

**Non voglio che venga sviluppato l'intero progetto contemporaneamente.**

Il progetto deve essere suddiviso in fasi piccole, indipendenti e verificabili.

Ogni fase deve produrre un risultato concreto che sia possibile eseguire, visualizzare o testare.

Al termine di ogni fase Codex deve:

1. Completare esclusivamente le funzionalità richieste.
2. Verificare che funzionino.
3. Eseguire i test pertinenti.
4. Spiegare cosa è stato realizzato.
5. Indicare eventuali problemi o limitazioni.
6. Attendere la mia approvazione prima di passare alla fase successiva.

**Non procedere mai autonomamente alla fase seguente.**

Se viene fornito questo documento senza ulteriori indicazioni, iniziare esclusivamente dalla Fase 1.

L'obiettivo non è ottenere immediatamente un prodotto perfetto, ma costruire progressivamente un sistema funzionante, stabile ed estendibile.

---

## 2. Tecnologie e ambiente

### Infrastruttura

Il progetto sarà ospitato su un server personale con:

- Debian 13 senza interfaccia grafica.
- Docker e Docker Compose.
- n8n già disponibile.
- Nextcloud già disponibile.
- Tailscale e Cloudflare Tunnel per accessi remoti.
- Risorse hardware limitate.

Non modificare servizi, configurazioni o container già esistenti senza una richiesta esplicita.

### Stack previsto

**Frontend**
- Hugo.
- HTML e CSS.
- JavaScript leggero.
- Layout responsive e mobile-first.
- Shortcode Hugo per contenuti multimediali.

**Backend**
- Python 3.
- SQLite.
- Moduli indipendenti per la raccolta e l'elaborazione.
- Configurazioni YAML.
- API esterne quando necessarie.

**AI**
- Supporto a Ollama e provider esterni configurabili.
- Output JSON strutturati.
- Fallback in caso di indisponibilità del modello.

**Automazione**
- Pipeline Python eseguibile manualmente.
- Scheduler introdotto soltanto nelle fasi avanzate.
- Possibile integrazione con n8n.

**Deployment**
- Docker Compose.
- Server web statico Nginx o Caddy.
- Volumi persistenti.
- Variabili d'ambiente per credenziali e segreti.

Non introdurre tecnologie più complesse finché non si dimostrano necessarie.

---

## 3. Architettura finale prevista

L'architettura dovrà essere modulare.

I componenti principali saranno:

1. **Hugo Frontend** — visualizzazione del giornale.
2. **Content Publisher** — generazione delle pagine e dei dati.
3. **Content Collectors** — recupero dei contenuti.
4. **Content Discovery** — ricerca dinamica per interessi.
5. **Content Processing** — normalizzazione, deduplicazione e clustering.
6. **AI Curation** — classificazione, ranking e riassunti.
7. **Video Discovery** — ricerca YouTube e gestione Instagram.
8. **Storage** — SQLite e archivio delle pubblicazioni.
9. **Scheduler** — aggiornamento automatico.
10. **Monitoring** — log e controllo delle esecuzioni.

L'architettura deve essere progettata per accogliere questi componenti, ma **non devono essere implementati tutti nella prima fase**.

Evitare di creare anticipatamente decine di classi, moduli o servizi inutilizzati.

Realizzare ciascun componente quando viene raggiunta la fase corrispondente.

---

## 4. Gestione degli interessi personali

Il sistema finale deve supportare interessi configurabili.

Ogni interesse potrà contenere:

- Nome.
- Descrizione.
- Parole chiave.
- Sinonimi e varianti linguistiche.
- Parole escluse.
- Priorità.
- Fonti preferite.
- Lingue.
- Numero indicativo di contenuti desiderati.

Categorie iniziali:

### Tecnologia
Linux, open source, hardware, cybersecurity, self-hosting, server e programmazione.

### Intelligenza artificiale
Nuovi modelli, AI locale, LLM, coding, ricerca e hardware dedicato.

### Gaming
Videogiochi, game development, Unity, Unreal Engine e industria videoludica.

### Scienza
Spazio, tecnologia, fisica, ambiente e divulgazione scientifica.

### Attualità
Principali eventi mondiali, geopolitica e innovazioni importanti.

Questi valori sono esempi iniziali e dovranno essere modificabili senza alterare il codice.

L'interpretazione semantica degli interessi verrà introdotta solamente nella fase dedicata all'AI.

---

## 5. Specifiche del motore di ricerca delle notizie

A regime il sistema dovrà poter raccogliere circa 100–200 contenuti candidati ogni giorno, con quantità configurabile.

Il funzionamento previsto combina:

- Feed RSS predefiniti.
- Ricerca Google News per parole chiave, quando disponibile.
- Fonti specializzate.
- Altri provider di ricerca configurabili.

Non deve limitarsi a un elenco chiuso di testate giornalistiche.

### Ricerca temporale

Privilegiare contenuti pubblicati nelle ultime 24 ore.

Prevedere eventualmente un fallback di 48–72 ore quando non vengono trovati abbastanza contenuti pertinenti.

### Metadati

Ogni contenuto dovrà avere, quando disponibili:

- Identificatore.
- Titolo.
- URL.
- Fonte.
- Data di pubblicazione.
- Data di acquisizione.
- Descrizione.
- Testo disponibile.
- Immagine.
- Lingua.
- Categoria.
- Query di provenienza.
- Stato di elaborazione.

I contenuti dovranno essere normalizzati e deduplicati.

Rispettare le condizioni d'uso delle fonti, i limiti di accesso e il copyright. Non aggirare paywall o restrizioni tecniche.

---

## 6. Specifiche YouTube

La componente YouTube deve supportare:

### Monitoraggio dei canali

Recuperare i video pubblicati da canali selezionati dall'utente.

### Ricerca per argomenti

Ricercare video recenti tramite YouTube Data API utilizzando gli interessi personali.

### Video brevi

Distinguere i video tradizionali da quelli brevi e identificare gli Shorts quando possibile.

Non presumere che qualsiasi video sotto una determinata durata sia uno Short.

### Quote API

Implementare caching, gestione delle quote, deduplicazione e limiti configurabili alle ricerche.

### Visualizzazione

Mostrare i video tramite player incorporato o collegamento esterno.

---

## 7. Specifiche Instagram

Instagram deve essere trattato come una fonte a monitoraggio selettivo.

Voglio poter inserire un elenco di account, ad esempio Geopop e altri divulgatori.

### Obiettivi

- Gestire un elenco configurabile di account.
- Recuperare i Reel pubblici mediante metodi effettivamente consentiti.
- Conservare URL e metadati.
- Visualizzare i Reel tramite shortcode Hugo o incorporamento ufficiale.
- Evitare duplicati.

### Limitazioni

Le API Instagram possono non consentire la raccolta automatica dei Reel di account pubblici terzi.

Non presumere che tali funzionalità siano disponibili.

Implementare prima l'importazione manuale degli URL, poi valutare separatamente i metodi di acquisizione automatica realmente utilizzabili.

Instagram deve essere un componente facoltativo, che non impedisca il funzionamento delle altre fonti.

---

## 8. Specifiche dell'intelligenza artificiale

Il modello AI dovrà analizzare i contenuti raccolti e decidere quali sono più rilevanti.

### Input

- Titolo.
- Descrizione.
- Data.
- Fonte.
- Testo disponibile.
- Categoria.
- Preferenze personali.

### Valutazione

Ogni contenuto dovrà ricevere un punteggio indicativo da 0 a 100.

| Criterio | Peso iniziale |
|---|---:|
| Pertinenza personale | 35% |
| Importanza della notizia | 25% |
| Attualità | 15% |
| Attendibilità | 15% |
| Originalità e valore informativo | 10% |

I pesi devono essere configurabili.

L'AI dovrà classificare i contenuti e produrre riassunti italiani di circa 60–120 parole per gli articoli selezionati.

Non deve inventare fatti, fonti, citazioni o informazioni mancanti.

### Selezione finale

Pubblicare indicativamente 10–20 elementi giornalieri, distribuendoli tra le categorie in base alle priorità e alla qualità.

L'AI non deve pubblicare automaticamente tutto ciò che riceve.

---

## 9. Collegamento tra notizie e video

Quando viene trovata una notizia importante, il sistema deve cercare video che la spieghino.

Esempio: viene annunciata una nuova versione di Blender.

La pipeline dovrà:

1. Identificare la notizia.
2. Determinarne l'importanza.
3. Generare una query YouTube pertinente.
4. Cercare video recenti.
5. Valutarne la rilevanza.
6. Associare il video migliore alla notizia.

Preferire contenuti informativi e brevi, evitando clickbait e collegamenti poco pertinenti.

Non associare video se non viene trovata una corrispondenza convincente.

---

## 10. Frontend Hugo

L'interfaccia deve ricordare una rivista digitale moderna.

### Homepage

- Data corrente.
- Notizia principale.
- Notizie della giornata.
- Sezioni tematiche.
- Video e contenuti verticali.
- Collegamento all'archivio.
- Accesso al calendario.

### Archivio

Ogni giorno deve avere un URL dedicato:

`/daily/YYYY-MM-DD/`

Le edizioni precedenti devono rimanere consultabili.

### Calendario

- Vista mensile.
- Navigazione tra i mesi.
- Giorni con edizioni pubblicate evidenziati.
- Apertura dell'edizione selezionata.
- Supporto smartphone.

### Design

- Responsive.
- Mobile-first.
- Dark mode.
- Tipografia leggibile.
- Immagini e card.
- Accessibilità.
- Animazioni non invasive.
- Dipendenze ridotte.

Le informazioni devono essere facili da leggere senza costringere l'utente ad aprire sempre l'articolo originale.

---

## 11. Sistema di pubblicazione

Il backend deve produrre dati strutturati che Hugo possa utilizzare per generare il sito.

L'AI non deve generare direttamente HTML non validato.

Preferire un formato dati comune, per esempio JSON, e utilizzare il publisher per convertirlo nei contenuti Hugo.

### Requisiti

- Generazione ripetibile.
- Nessuna duplicazione delle edizioni.
- Contenuti precedenti conservati.
- URL stabili.
- Rigenerazione di una singola giornata.
- Gestione dei fallimenti.

In caso di errore, il sito già pubblicato deve rimanere accessibile.

---

## 12. Database

Utilizzare SQLite quando verrà introdotta la persistenza dei contenuti.

Entità previste:

- Sources.
- Contents.
- Content Groups.
- AI Evaluations.
- Daily Briefings.
- Pipeline Runs.

Non creare tutte le tabelle immediatamente se non sono necessarie.

Introdurre progressivamente le migrazioni, mantenendo compatibilità con i dati già salvati.

---

## 13. Automazione

La pipeline finale dovrà eseguire un aggiornamento giornaliero alle 07:00 nel fuso Europe/Rome.

Dovrà supportare:

- Avvio manuale.
- Raccolta separata.
- Valutazione AI separata.
- Rigenerazione del sito.
- Rigenerazione delle edizioni precedenti.
- Log delle esecuzioni.
- Retry limitati.
- Protezione dalle esecuzioni contemporanee.

n8n può essere utilizzato come orchestratore, ma il backend non deve dipendere da n8n per funzionare.

L'automazione sarà introdotta soltanto dopo aver verificato la pipeline manualmente.

---

## 14. Configurazione

Le impostazioni devono essere centralizzate in file YAML o JSON e variabili d'ambiente.

Prevedere configurazioni per:

- Interessi.
- Fonti.
- YouTube.
- Instagram.
- Impostazioni generali.
- Modello AI.
- Limiti delle API.
- Numero di notizie.
- Orario di aggiornamento.

Non salvare credenziali o token direttamente nel repository.

---

## 15. Struttura del repository

Organizzare progressivamente il progetto secondo una struttura simile a questa:

```text
daily-briefing/
├── backend/
│   ├── collectors/
│   ├── discovery/
│   ├── processing/
│   ├── ai/
│   ├── video_matching/
│   ├── publishing/
│   ├── database/
│   ├── pipeline/
│   ├── utils/
│   └── main.py
├── site/
│   ├── content/
│   ├── layouts/
│   ├── assets/
│   ├── static/
│   ├── data/
│   └── hugo.toml
├── config/
│   ├── interests.yaml
│   ├── sources.yaml
│   ├── youtube.yaml
│   ├── instagram.yaml
│   └── settings.yaml
├── docker/
├── scripts/
├── tests/
├── docs/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

Questa è la struttura finale indicativa, non l'elenco delle cartelle da creare nella prima fase.

**Creare soltanto i moduli effettivamente utilizzati dalla fase corrente**, mantenendo una struttura coerente con le estensioni future.

---

## 16. Sicurezza

Il sito sarà inizialmente personale, accessibile attraverso la rete privata o Tailscale.

Non esporre endpoint amministrativi pubblici.

Requisiti:

- Nessun segreto nel codice.
- Validazione dei dati esterni.
- Protezione dai contenuti HTML non affidabili.
- Prevenzione di richieste verso indirizzi interni non autorizzati.
- Limitazione delle richieste esterne.
- Gestione di timeout.
- Log degli errori.
- Protezione contro prompt injection nei contenuti analizzati.
- Backup del database.
- Build riproducibili.

Evitare modifiche automatiche alle configurazioni del server ospitante.

---

## 17. Deployment

Il deployment finale deve usare Docker Compose.

Distinguere principalmente:

- Servizio web statico.
- Servizio backend per raccolta e pubblicazione.
- Volumi persistenti.

Non è necessario un container per ogni modulo Python.

La configurazione dovrà poter essere modificata senza ricostruire tutto il sistema.

Il sito deve continuare a funzionare anche quando la pipeline di raccolta è inattiva.

---

## 18. Qualità del codice

Il codice deve essere:

- Semplice.
- Modulare.
- Documentato.
- Testabile.
- Mantenibile.
- Privo di dipendenze superflue.

Evitare astrazioni premature e progettazioni eccessivamente generiche.

Prediligere funzioni semplici e componenti facilmente sostituibili.

Implementare test pertinenti per ciascuna fase, senza introdurre test di funzionalità non ancora esistenti.

---

## 19. Funzionalità future

Le seguenti funzionalità sono desiderabili ma non devono essere implementate nelle prime versioni:

- Feedback personale sui contenuti.
- Personalizzazione progressiva del ranking.
- Ricerca completa nello storico.
- Integrazione calendario Nextcloud.
- Notifiche quotidiane.
- Aggiornamenti straordinari durante la giornata.
- Embeddings e ricerca semantica avanzata.
- Pannello amministrativo.
- Gestione di più utenti.
- Supporto PWA e modalità offline.

Devono essere considerate possibili estensioni, non requisiti immediati.

---

# 20. ROADMAP DI IMPLEMENTAZIONE INCREMENTALE

**Questa sezione definisce l'ordine obbligatorio di sviluppo.**

Codex deve procedere una fase alla volta.

Una fase può essere avviata soltanto quando quella precedente è stata completata e approvata.

Se una modifica richiede interventi che appartengono a una fase successiva, Codex deve segnalarli senza implementarli automaticamente.

## FASE 1 — Creazione del sito Hugo

**Obiettivo:** ottenere un primo sito web funzionante e visualizzabile, anche se composto esclusivamente da contenuti dimostrativi.

### Implementare

- Inizializzare il progetto Hugo.
- Configurare il tema e i layout essenziali.
- Realizzare una homepage.
- Implementare intestazione e navigazione.
- Realizzare il layout delle card.
- Inserire una notizia principale.
- Inserire alcune notizie di esempio.
- Creare una sezione video dimostrativa.
- Aggiungere dark mode.
- Rendere il sito responsive.
- Configurare Docker Compose per l'avvio locale.
- Scrivere un README minimo.

### Contenuti

Utilizzare esclusivamente contenuti dimostrativi chiaramente riconoscibili come tali.

Non effettuare richieste reali a siti o API.

### Risultato atteso

Devo poter avviare Hugo e vedere un sito dall'aspetto curato, navigabile sia da computer sia da telefono.

### Criteri di completamento

- Docker Compose avvia correttamente il sito.
- Homepage funzionante.
- Layout responsive.
- Nessun errore di build Hugo.
- Documentazione di avvio disponibile.

### NON implementare

- Backend Python.
- Database.
- Raccolta RSS.
- Intelligenza artificiale.
- API YouTube.
- Instagram automatico.
- Scheduler.

**Fermarsi qui e attendere approvazione.**

---

## FASE 2 — Archivio giornaliero e calendario

**Obiettivo:** trasformare la homepage in un vero giornale organizzato per data.

### Implementare

- Pagine giornaliere con URL `/daily/YYYY-MM-DD/`.
- Archivio delle edizioni.
- Calendario mensile navigabile.
- Collegamenti tra homepage e archivio.
- Navigazione tra giorni precedenti e successivi, se disponibili.
- Visualizzazione delle categorie.
- Homepage che mostra l'edizione più recente.

### Contenuti

Creare alcune edizioni dimostrative relative a date differenti.

### Risultato atteso

Devo poter entrare nel sito, visualizzare l'edizione più recente, aprire il calendario e consultare una giornata precedente.

### Criteri di completamento

- Calendario funzionante su desktop e mobile.
- URL giornalieri stabili.
- Navigazione funzionante.
- Nessuna regressione alla homepage.

### NON implementare

- Raccolta automatica di notizie.
- Database.
- AI.

**Fermarsi qui e attendere approvazione.**

---

## FASE 3 — Primo generatore Python → Hugo

**Obiettivo:** creare il collegamento tra un programma Python e il sito Hugo.

Questa fase è fondamentale perché definisce il formato dei dati utilizzato dai moduli successivi.

### Implementare

- Un piccolo progetto Python.
- Uno schema JSON per i contenuti.
- Validazione dei dati in ingresso.
- Generazione automatica delle pagine Hugo.
- Comando per generare una specifica giornata.
- Possibilità di rigenerare una giornata senza duplicarla.
- Test del publisher.

### Procedura

1. Preparare un JSON con circa dieci notizie dimostrative.
2. Far leggere il file a Python.
3. Generare i contenuti Hugo.
4. Eseguire la build Hugo.
5. Verificare il risultato nel browser.

### Risultato atteso

Modificando il file JSON ed eseguendo uno script, il sito deve aggiornarsi senza dover editare manualmente i file Markdown.

### Criteri di completamento

- Comando manuale funzionante.
- Schema documentato.
- Generazione ripetibile.
- Collegamenti e metadati corretti.
- Nessun contenuto duplicato alla seconda esecuzione.

### NON implementare

- Raccolta RSS reale.
- AI.
- Scheduler.
- Database complesso.

**Fermarsi qui e attendere approvazione.**

---

## FASE 4 — Primo collettore RSS reale

**Obiettivo:** ottenere le prime notizie reali sul sito.

### Implementare

- Un collettore RSS Python.
- Configurazione iniziale di 2–3 fonti.
- Recupero di titolo, URL, data e descrizione.
- Gestione dei campi mancanti.
- Filtro sulle ultime 24 ore, quando le date sono disponibili.
- Trasformazione dei risultati nello schema JSON.
- Collegamento al publisher sviluppato nella Fase 3.
- Gestione di errori e timeout.

### Procedura

1. Eseguire il collettore.
2. Recuperare notizie reali.
3. Generare il file strutturato.
4. Pubblicare un briefing di prova.
5. Visualizzare le notizie su Hugo.

### Risultato atteso

Il giornale deve poter mostrare notizie vere provenienti da feed RSS.

La selezione può essere ancora elementare.

### Criteri di completamento

- Recupero reale da almeno una fonte funzionante.
- Metadati corretti.
- Link originali funzionanti.
- Gestione degli errori verificata.
- Sito generato correttamente.

### NON implementare

- AI.
- Google News dinamico.
- YouTube.
- Instagram.

**Fermarsi qui e attendere approvazione.**

---

## FASE 5 — Database SQLite e deduplicazione

**Obiettivo:** memorizzare i contenuti recuperati ed evitare duplicazioni.

### Implementare

- Database SQLite.
- Tabelle iniziali necessarie.
- Migrazioni.
- Salvataggio dei contenuti RSS.
- Normalizzazione degli URL.
- Eliminazione dei parametri di tracciamento più comuni.
- Identificazione dei duplicati per URL.
- Gestione di titoli quasi identici tramite regole semplici.
- Storico delle acquisizioni.
- Comandi per ispezionare e rigenerare i contenuti.

### Risultato atteso

Ripetendo due volte la stessa raccolta, le notizie già esistenti non devono essere inserite nuovamente.

### Criteri di completamento

- Database persistente.
- Duplicati esatti riconosciuti.
- Test di idempotenza superati.
- Le pagine già pubblicate rimangono consultabili.

### NON implementare

- Clustering semantico avanzato.
- AI.
- Nuove fonti video.

**Fermarsi qui e attendere approvazione.**

---

## FASE 6 — Ricerca dinamica per interessi

**Obiettivo:** superare il limite dei feed RSS predefiniti.

### Implementare

- File `interests.yaml`.
- Configurazione delle categorie e delle parole chiave.
- Ricerca per argomenti tramite feed Google News o altra sorgente appropriata.
- Combinazione di risultati da RSS predefiniti e ricerca dinamica.
- Deduplicazione tra sorgenti.
- Filtri temporali.
- Limiti configurabili sul numero di risultati.
- Log delle query utilizzate.

### Procedura

Per ogni interesse il sistema deve:

1. Leggere le parole chiave.
2. Costruire query pertinenti.
3. Recuperare i risultati.
4. Normalizzarli.
5. Eliminare i duplicati.
6. Salvarli in SQLite.

### Risultato atteso

Non devo più essere vincolato esclusivamente alle fonti impostate manualmente.

Il sistema deve trovare contenuti anche da testate non inserite in precedenza.

### Criteri di completamento

- Interessi modificabili da YAML.
- Query effettivamente eseguite.
- Risultati archiviati.
- Nessun duplicato evidente.
- Gestione dei feed non disponibili.

### NON implementare

- Ranking AI.
- YouTube.
- Instagram.

**Fermarsi qui e attendere approvazione.**

---

## FASE 7 — Prima selezione automatica senza AI

**Obiettivo:** creare un primo algoritmo di ranking affidabile e facilmente verificabile.

Prima di utilizzare un modello AI, voglio avere una baseline funzionante.

### Implementare

- Punteggio basato sulla corrispondenza con gli interessi.
- Peso della recenza.
- Priorità delle fonti.
- Esclusione dei contenuti irrilevanti.
- Ordinamento per punteggio.
- Bilanciamento minimo tra categorie.
- Selezione delle 10–20 notizie migliori.
- Pubblicazione del risultato.

### Risultato atteso

Il sistema deve essere già capace di produrre un briefing ragionevolmente personalizzato senza utilizzare AI.

### Criteri di completamento

- Ranking deterministico.
- Pesi configurabili.
- Test del calcolo del punteggio.
- Briefing pubblicato automaticamente dopo un'esecuzione manuale della pipeline.

### NON implementare

- LLM.
- Embeddings.
- Classificazione semantica complessa.

**Fermarsi qui e attendere approvazione.**

---

## FASE 8 — Introduzione dell'intelligenza artificiale

**Obiettivo:** migliorare la qualità della selezione e dei riassunti.

### Implementare

- Interfaccia astratta per i provider AI.
- Supporto a un primo provider configurabile.
- Possibilità di utilizzare Ollama.
- Timeout.
- Validazione delle risposte JSON.
- Valutazione semantica dei contenuti.
- Classificazione per categorie.
- Punteggio di rilevanza.
- Riassunti in italiano.
- Selezione finale.
- Fallback al ranking della Fase 7.

### Strategia

Non inviare necessariamente tutti i contenuti integrali al modello.

Utilizzare inizialmente titolo, descrizione e metadati; recuperare o analizzare testo aggiuntivo soltanto quando utile e disponibile.

Evitare sprechi di token e risorse.

### Risultato atteso

Le notizie pubblicate devono essere più pertinenti, meglio organizzate e accompagnate da riassunti sintetici.

### Criteri di completamento

- Classificazione AI funzionante.
- JSON validati.
- Riassunti coerenti con le fonti.
- Fallback verificato.
- Versione del modello e valutazioni registrate.

### NON implementare

- Ricerca YouTube automatica.
- Instagram.
- Apprendimento dai feedback personali.

**Fermarsi qui e attendere approvazione.**

---

## FASE 9 — Integrazione dei video YouTube

**Obiettivo:** aggiungere contenuti multimediali provenienti da canali selezionati.

### Implementare

- Configurazione `youtube.yaml`.
- Monitoraggio dei canali.
- Recupero dei metadati tramite metodi ufficiali disponibili.
- Gestione delle quote API.
- Caching degli ID già elaborati.
- Distinzione tra video lunghi e brevi.
- Identificazione prudente degli Shorts.
- Valutazione dei contenuti tramite il sistema di ranking esistente.
- Sezione video funzionante nel sito.
- Embed YouTube o anteprime con collegamento.

### Risultato atteso

Il sito deve mostrare video recenti e pertinenti provenienti da canali YouTube selezionati.

### Criteri di completamento

- Recupero reale verificato.
- Embed funzionanti.
- Nessun ID duplicato.
- Quote monitorate.
- Il sito funziona anche se l'API non risponde.

### NON implementare

- Ricerca dinamica di video collegati alle notizie.
- Instagram.

**Fermarsi qui e attendere approvazione.**

---

## FASE 10 — Ricerca YouTube per argomenti e notizie correlate

**Obiettivo:** trovare video informativi anche al di fuori dei canali predefiniti.

### Implementare

- Ricerca YouTube per parole chiave.
- Generazione di query dagli interessi.
- Generazione di query dalle notizie selezionate.
- Associazione tra video e notizie.
- Ranking dei video candidati.
- Verifica della pertinenza.
- Preferenza per contenuti brevi.
- Filtro contro associazioni deboli.
- Limiti configurabili sul consumo delle quote.

### Esempio

Il sistema scopre una notizia importante sul rilascio di un modello AI.

Genera una ricerca YouTube specifica, confronta i risultati e, se individua un video coerente, lo presenta accanto all'articolo.

### Risultato atteso

La pagina giornaliera deve contenere non soltanto video generici, ma anche approfondimenti pertinenti alle notizie.

### Criteri di completamento

- Query dinamiche funzionanti.
- Associazioni motivate.
- Nessun video obbligatorio quando mancano corrispondenze.
- Controllo del consumo delle quote.

**Fermarsi qui e attendere approvazione.**

---

## FASE 11 — Integrazione Instagram

**Obiettivo:** incorporare Reel informativi da account selezionati.

### Primo incremento

- Creare `instagram.yaml`.
- Definire gli account desiderati.
- Permettere l'inserimento manuale di URL Reel.
- Validare i collegamenti.
- Salvare i metadati disponibili.
- Realizzare lo shortcode Hugo.
- Mostrare i Reel nella sezione video.

### Secondo incremento, da autorizzare separatamente

Analizzare le possibilità concrete di monitoraggio automatico degli account configurati.

Verificare API, autorizzazioni e limitazioni reali.

Implementare soltanto una soluzione consentita e documentata.

### Risultato atteso

Devo poter visualizzare Reel Instagram nel sito.

Il recupero automatico è un obiettivo desiderato, ma non deve essere simulato se tecnicamente indisponibile.

### Criteri di completamento

- Importazione manuale funzionante.
- URL validati.
- Embed o fallback con collegamento esterno.
- Nessuna dipendenza obbligatoria da Instagram.
- Limitazioni documentate.

**Fermarsi qui e attendere approvazione.**

---

## FASE 12 — Automazione quotidiana

**Obiettivo:** trasformare la pipeline, fino a questo momento eseguibile manualmente, in un processo automatico.

### Implementare

- Avvio programmato alle 07:00.
- Fuso Europe/Rome.
- Una sola istanza attiva per esecuzione.
- Comando manuale di aggiornamento.
- Logging delle esecuzioni.
- Retry limitati.
- Pubblicazione soltanto dopo una build valida.
- Mantenimento della versione precedente in caso di errore.
- Possibilità di eseguire le singole fasi separatamente.

### Orchestrazione

Valutare n8n rispetto a uno scheduler più leggero.

La pipeline deve comunque rimanere utilizzabile dalla CLI.

### Risultato atteso

Ogni mattina il sito deve aggiornarsi senza interventi manuali.

### Criteri di completamento

- Esecuzione programmata verificata.
- Avvio manuale funzionante.
- Nessuna esecuzione concorrente.
- Stato dell'ultima esecuzione consultabile.
- Il sito rimane accessibile se l'aggiornamento fallisce.

**Fermarsi qui e attendere approvazione.**

---

## FASE 13 — Stabilizzazione e ottimizzazione

**Obiettivo:** rendere il progetto affidabile nell'utilizzo quotidiano.

### Implementare

- Revisione della gestione degli errori.
- Miglioramento dei log.
- Gestione dei timeout.
- Ottimizzazione delle richieste.
- Caching.
- Gestione delle quote API.
- Controllo delle risorse.
- Backup SQLite.
- Istruzioni di ripristino.
- Verifiche di sicurezza.
- Miglioramento del deployment Docker.
- Test end-to-end.
- Controlli di accessibilità.
- Ottimizzazione mobile.

### Risultato atteso

Il sistema deve poter funzionare continuativamente sul server con manutenzione minima.

### Criteri di completamento

- Test automatici superati.
- Risorse utilizzate misurate.
- Backup verificato.
- Nessun segreto esposto.
- Documentazione aggiornata.
- Procedure di avvio e ripristino riproducibili.

**Fermarsi qui e attendere approvazione.**

---

## FASE 14 — Funzionalità avanzate future

Questa fase non deve essere avviata automaticamente.

Le funzionalità possono essere implementate in incrementi separati, secondo necessità:

### A. Feedback personale

Aggiungere:
- Mi interessa.
- Non mi interessa.
- Salva per dopo.
- Mostrami meno contenuti simili.

Poiché Hugo è statico, introdurre un piccolo backend soltanto se necessario per memorizzare le interazioni.

### B. Personalizzazione avanzata

Utilizzare le valutazioni personali per modificare progressivamente il ranking.

Valutare embeddings e ricerca semantica soltanto se apportano un vantaggio concreto.

### C. Integrazione Nextcloud

Integrare il calendario personale Nextcloud in una sezione separata dalle notizie.

### D. Notifiche

Inviare notifiche quando il briefing è pronto.

### E. Ricerca nello storico

Permettere di cercare notizie e argomenti delle edizioni precedenti.

### F. Pannello amministrativo

Gestire interessi, fonti e impostazioni direttamente dal browser, con autenticazione.

### G. PWA

Valutare installazione su smartphone e consultazione offline.

Ogni funzionalità avanzata deve essere trattata come una nuova fase autonoma e approvata separatamente.

---

# 21. Test e criteri di avanzamento

## Regole generali

Ogni fase deve mantenere funzionanti le caratteristiche implementate precedentemente.

Prima di richiedere l'approvazione, Codex deve:

1. Eseguire i test pertinenti.
2. Verificare la build Hugo, se coinvolta.
3. Controllare che il progetto si avvii.
4. Documentare eventuali dipendenze.
5. Aggiornare il README.
6. Indicare eventuali regressioni.
7. Dichiarare cosa non è ancora stato realizzato.

Non è necessario implementare tutti i test previsti dal progetto finale fin dall'inizio.

### Test da introdurre progressivamente

- Generazione Hugo.
- Validazione del JSON.
- Deduplicazione.
- Filtri temporali.
- Persistenza SQLite.
- Ranking.
- Validazione delle risposte AI.
- Associazione video-notizia.
- Gestione errori API.
- Idempotenza della pipeline.
- Build e pubblicazione.
- Avvio Docker.

### Condizioni per passare alla fase successiva

Una fase può essere considerata completata soltanto quando:

- Le funzionalità richieste sono effettivamente implementate.
- I test disponibili sono stati eseguiti.
- Eventuali limitazioni sono dichiarate.
- Non sono state introdotte regressioni note non accettate.
- Il risultato è verificabile.
- Ho approvato esplicitamente il passaggio.

Se una fase presenta problemi, correggerli prima di iniziare la successiva.

---

# 22. ISTRUZIONI OPERATIVE OBBLIGATORIE PER CODEX

## Regola principale

**Devi lavorare esclusivamente sulla fase che ti viene assegnata.**

Questo documento rappresenta la visione completa del progetto, non una richiesta di implementare tutte le funzionalità immediatamente.

Se non viene indicata una fase specifica, considera attiva soltanto la **Fase 1**.

Non iniziare la Fase 2 o successive senza autorizzazione esplicita.

## All'inizio di ogni fase

1. Esamina lo stato attuale del repository.
2. Leggi il README e la roadmap.
3. Individua le funzionalità già presenti.
4. Verifica le dipendenze necessarie.
5. Identifica i file che prevedi di modificare.
6. Presenta un breve piano per la fase corrente.
7. Procedi all'implementazione senza estendere autonomamente l'ambito.

Non ricreare componenti già funzionanti.

Non riscrivere parti del progetto senza una necessità concreta.

## Durante lo sviluppo

- Implementa codice reale.
- Mantieni il progetto funzionante.
- Preferisci soluzioni semplici.
- Non introdurre dipendenze non necessarie.
- Non implementare moduli delle fasi successive.
- Non aggiungere funzionalità speculative.
- Non modificare altri servizi sul server.
- Documenta le scelte architetturali importanti.
- Esegui i test relativi al codice modificato.

Se emerge un problema che richiede una scelta sostanziale o una modifica fuori ambito, segnalalo prima di procedere.

## Al termine di ogni fase

Fornisci un rapporto strutturato contenente:

**1. Fase completata**

Numero e nome.

**2. Funzionalità implementate**

Elenco delle modifiche realmente funzionanti.

**3. File principali modificati**

Breve descrizione del loro ruolo.

**4. Test eseguiti**

Comandi utilizzati ed esito dei test.

**5. Come verificare il risultato**

Istruzioni precise per eseguire e provare ciò che è stato sviluppato.

**6. Problemi e limitazioni**

Eventuali aspetti incompleti o non verificati.

**7. Prossima fase prevista**

Breve descrizione della fase successiva, senza implementarla.

## Gestione della roadmap

Mantenere un file `ROADMAP.md` nel repository.

Il file deve indicare:

- Fase corrente.
- Fasi completate.
- Fasi da implementare.
- Stato di avanzamento.
- Problemi conosciuti.
- Eventuali decisioni tecniche importanti.

Aggiornarlo al termine di ogni incremento.

Utilizzare stati come:

- Non iniziata.
- In corso.
- Implementata, da verificare.
- Completata e approvata.
- Bloccata.

Non segnare una fase come approvata senza conferma dell'utente.

## Obiettivo iniziale

**Inizia esclusivamente con la Fase 1: sito Hugo e interfaccia grafica dimostrativa.**

Non implementare ancora il motore di raccolta, il database, l'AI o le automazioni.

Voglio prima avere un sito visivamente gradevole, responsive e funzionante, sul quale costruire successivamente tutte le altre funzionalità.

Quando la Fase 1 sarà pronta, fermati, mostrami come provarla e attendi le mie indicazioni.

**La priorità del progetto è progredire in modo controllato, un incremento funzionante alla volta, mantenendo la possibilità di verificare, modificare o ripensare le scelte prima di aggiungere ulteriore complessità.**