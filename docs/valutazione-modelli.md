# Valutazione dei modelli locali per TheTomTimes

16 novembre 2026

Il carico previsto comprende classificazione nelle categorie del giornale, stima della rilevanza e riassunti brevi in italiano a partire da titolo ed estratto RSS. Il Raspberry Pi 4 ha 4 GB nominali e un’occupazione a riposo indicata del 24%. Il 76% residuo corrisponde a circa 3 GB sulla carta. La metrica da rilevare sul Pi è `MemAvailable` con i servizi abituali attivi. Il file GGUF indica lo spazio dei pesi. Il processo usa memoria anche per il contesto e per i buffer di calcolo. [Raspberry Pi OS a 64 bit](https://www.raspberrypi.com/news/raspberry-pi-os-64-bit/) · [Documentazione Linux su MemAvailable](https://docs.kernel.org/filesystems/proc.html)

## Metodo

Ho eseguito i modelli su CPU x86-64 con llama.cpp b12429, commit `9fba51d2c`, contesto 2048, quattro thread e uno slot per server. Ho usato gli stessi otto casi sintetici per ciascuna configurazione, temperatura zero, al massimo 150 token in uscita e decodifica vincolata da schema JSON. I casi coprono le cinque categorie, due estratti in inglese, un falso positivo per «psico-fisico», un titolo senza estratto e un articolo sui videogiochi con lessico scientifico.

Il prompt diretto chiede categoria, rilevanza e riassunto. Il prompt guidato usa identificativi numerici per le categorie e due esempi. La prova del solo riassunto chiede una frase in italiano. Ho verificato forma del JSON e categoria attesa separatamente e letto i risultati per individuare perdite o aggiunte di fatti. Otto casi sintetici danno un’indicazione qualitativa. La prova sul Pi richiede estratti RSS reali e misure di memoria e durata.

Lo script e i risultati grezzi sono nella cartella locale `output/model-evaluation/`. Per ripetere la prova su un server llama.cpp già avviato su loopback, esegui `python3 pilot.py PORTA NOME guided`. Ometti `guided` per il prompt diretto o usa `summary` per il solo riassunto. Ogni variante salva un JSON con risultati e tempi. [API e schema JSON di llama.cpp](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)

## Risultati su CPU x86-64

| Modello | File GGUF | Categoria corretta con prompt diretto | Categoria corretta con prompt guidato |
| --- | ---: | ---: | ---: |
| [Granite 4.0 350M](https://huggingface.co/ibm-granite/granite-4.0-350m-GGUF/tree/main) | 237 MB, Q4_K_M | 4/8 | — |
| [Granite 4.0 H 350M](https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF/tree/main) | 366 MB, Q8_0 | — | 1/8 |
| [Gemma 3 270M IT](https://huggingface.co/ggml-org/gemma-3-270m-it-GGUF/tree/main) | 292 MB, Q8_0 | — | 2/8 |
| [LFM2.5 1.2B Instruct](https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct-GGUF/tree/main) | 731 MB, Q4_K_M | — | 1/8 |
| [Gemma 3 1B IT](https://huggingface.co/ggml-org/gemma-3-1b-it-GGUF/tree/main) | 806 MB, Q4_K_M | 2/8 | 1/8 |
| [Granite 4.0 1B](https://huggingface.co/ibm-granite/granite-4.0-1b-GGUF/tree/main) | 1,02 GB, Q4_K_M | 5/8 | 3/8 |
| [LFM2.5 2.6B](https://huggingface.co/LiquidAI/LFM2.5-2.6B-GGUF/tree/main) | 1,67 GB, Q4_K_M | — | 7/8 con budget di ragionamento a zero |

I trattini indicano combinazioni non eseguite. Con il ragionamento predefinito, LFM2.5 2.6B ha esaurito i 150 token prima di produrre il JSON. Con `--reasoning-budget 0` ha prodotto 8/8 JSON validi, riconosciuto il falso positivo «psico-fisico» e classificato il rinvio di un videogioco come Attualità. Nel riassunto dell’estratto inglese su Marte ha trasformato «vicino alla superficie» in «sulla superficie». Per ripetere questa variante, usa il flag sul server e passa `guided-no-thinking` a `pilot.py`. [Template Liquid AI](https://huggingface.co/LiquidAI/LFM2.5-2.6B/blob/main/chat_template.jinja) · [Flag di llama.cpp](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)

Le altre configurazioni della tabella hanno prodotto 8/8 JSON validi. Granite 350M ha talvolta copiato il prompt o restituito l’estratto in inglese. Con il solo riassunto, Granite 1B ha conservato le date del rinvio di un videogioco, il numero di parametri di un modello e l’incertezza sul volume del ghiaccio marziano. Ha anche trasformato le trattative in «sanzioni diplomatiche». Gemma 1B ha inventato una data e dettagli della missione per un titolo privo di estratto.

LFM2.5 1.2B dichiara otto lingue, tra cui francese e spagnolo. L’italiano è dichiarato da Liquid AI nel modello 2.6B. Ho considerato anche Llama 3.2 1B e il derivato LlaMaestra addestrato sull’italiano. SmolLM3 3B include l’italiano e resta un candidato per hardware con più margine. [Liquid AI 1.2B](https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct) · [Liquid AI 2.6B](https://huggingface.co/LiquidAI/LFM2.5-2.6B) · [Meta Llama 3.2 1B](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct) · [LlaMaestra](https://huggingface.co/collections/puettmann/maestra) · [SmolLM3](https://huggingface.co/HuggingFaceTB/SmolLM3-3B)

## Scelta proposta

LFM2.5 2.6B Q4_K_M con budget di ragionamento a zero è il primo candidato per classificare e riassumere sul Pi. Se il costo in RAM o tempo è troppo alto, il candidato più leggero emerso dalla prova è Granite 4.0 1B Q4_K_M per i soli riassunti, affiancato al ranking della Fase 7. La qualità sul campione RSS e le misure sul Pi determinano se adottare uno dei due.

In una richiesta breve su x86-64, LFM2.5 2.6B ha completato l’inferenza con un limite di 2300 MiB e senza swap nel container. Il contatore `memory.peak`, che include la memoria addebitata al container, ha raggiunto il limite. Granite 1B ha completato una richiesta breve con un limite di 2 GiB e un picco di 1,82 GiB. Queste prove riguardano il runtime e la macchina locale. Sul Pi conta la memoria disponibile per tutto il sistema e la latenza durante un briefing intero.

I file dei due finalisti sono in `output/model-evaluation/models/`. Per identificare i GGUF esatti, questi sono i loro SHA-256.

| File | SHA-256 |
| --- | --- |
| `LFM2.5-2.6B-Q4_K_M.gguf` | `02a8b7e17487d326e46d68ce0ba24211e1b80a14c4cd0597fa73c1cd697f52ed` |
| `granite-4.0-1b-Q4_K_M.gguf` | `22ec0f9cc99a90185312de3c882c84e7bd6789bdd050389844380a01a831d7f1` |

## Criteri per la prova sul Pi

1. Controllare `uname -m` e `free -h`. Partire con Linux arm64, contesto 2048, un solo slot e un articolo per richiesta. Provare tre e quattro thread con i servizi abituali attivi.
2. Usare 30 estratti RSS reali in italiano e inglese, inclusi articoli ambigui o fuori tema e descrizioni mancanti. Valutare separatamente JSON, categoria, qualità dell’italiano e fedeltà di nomi, numeri, date e negazioni. Confrontare le categorie con il ranking della Fase 7 sullo stesso campione.
3. Misurare la durata di un briefing di 15 articoli, `MemAvailable` minimo, attività dello swap con `vmstat 1` ed eventuale throttling. Come soglie iniziali, propongo 15 minuti per il briefing, almeno 750 MiB disponibili durante la prova, assenza di swap sostenuto e almeno 27 riassunti utilizzabili su 30 estratti con informazioni sufficienti. Ogni riassunto utilizzabile deve essere fedele alla fonte.
4. Trattare un estratto assente come informazione insufficiente e usare il titolo. Per timeout o risultati scartati, usare il punteggio della Fase 7 e l’estratto RSS. Se i riassunti superano la prova ma le categorie peggiorano rispetto alla Fase 7, mantenere le categorie della Fase 7 per l’edizione.

llama.cpp è il runtime della prova. Ollama offre un pacchetto Linux ARM64 e supporta schemi JSON in locale. Per valutare Ollama sul Pi, usare la stessa quantizzazione e limitare il parallelismo a una richiesta. [Ollama su Linux](https://docs.ollama.com/linux) · [Output strutturati](https://docs.ollama.com/capabilities/structured-outputs) · [Memoria e parallelismo](https://docs.ollama.com/faq)
