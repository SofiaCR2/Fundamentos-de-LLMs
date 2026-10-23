# Ficha del modelo: llama3.2:3b en Ollama (Modalidad 2.3)

> Los datos marcados **(verificar)** salen de la documentación pública del modelo y deben confirmarse en tu máquina con `ollama show llama3.2:3b`. Las secciones de **resultados medidos** se completan con los scripts de `backend/scripts/`; este documento no incluye mediciones inventadas.

## 1. Ficha técnica

| Campo | Valor |
|---|---|
| Modelo | Llama 3.2 3B Instruct (Meta), servido por Ollama como `llama3.2:3b` |
| Parámetros | ~3.2 mil millones (verificar) |
| Arquitectura | Transformer decoder-only; 28 capas, dimensión 3072, 24 cabezas de atención con 8 cabezas KV (GQA), vocabulario ~128 mil tokens (verificar) |
| Contexto máximo | 128K tokens (el pipeline usa < 4K) |
| Formato | GGUF, cuantización por defecto **Q4_K_M** (~4,5-5 bits efectivos por peso) (verificar) |
| Tamaño en disco | ~2 GB (verificar con `ollama list`) |
| Idiomas | Español incluido entre los idiomas soportados oficialmente |
| Licencia | Llama 3.2 Community License (revisar condiciones de uso comercial) |
| Endpoint | `http://localhost:11434` (`/api/chat`, `/api/tags`, `/api/ps`) |

Comandos para confirmar los valores reales:
```bash
ollama show llama3.2:3b              # arquitectura, parámetros, cuantización, contexto
ollama show llama3.2:3b --modelfile  # plantilla y parámetros por defecto
ollama ps                            # memoria usada y si corre en CPU o GPU
```

## 2. RAM requerida (estimación a partir de la arquitectura)

Pesos cuantizados: ~2,0 GB. El caché KV en fp16 cuesta por token `2 x capas x cabezas_KV x dim_cabeza x 2 bytes = 2 x 28 x 8 x 128 x 2 = 114.688 bytes (~112 KiB)`.

| Contexto (`num_ctx`) | Caché KV | Total aprox. del modelo (pesos + KV + ~0,5 GB overhead) |
|---|---|---|
| 4.096 | ~0,45 GB | ~3,0 GB |
| 8.192 | ~0,9 GB | ~3,4 GB |
| 32.768 | ~3,6 GB | ~6,1 GB |

El pipeline recorta el texto a 6.000 caracteres (~1.500-2.000 tokens) más el prompt, por lo que `num_ctx` de 4.096 alcanza. **Recomendación:** equipo con 8 GB de RAM como mínimo (modelo + sistema + API + frontend); 16 GB da holgura. El script de instalación avisa si hay menos de 6 GB. La memoria real se registra en `backend/results/benchmark.json` (campo `ollama_ps`).

Parámetros de Ollama relevantes para operar:
- `OLLAMA_KEEP_ALIVE`: por defecto el modelo se descarga tras ~5 min de inactividad; la siguiente petición paga la carga (arranque en frío). Subirlo a `1h` si hay tráfico intermitente.
- `OLLAMA_NUM_PARALLEL`: peticiones simultáneas por modelo; cada una multiplica el caché KV.
- `temperature: 0` en todas las etapas, para resultados lo más reproducibles posible.

## 3. Benchmarks (medir en tu equipo)

```bash
python backend/scripts/benchmark_ollama.py --runs 3
```
Usa los prompts reales del pipeline (`backend/app/prompts.py`) sobre `backend/data/samples.json` y genera `backend/results/benchmark.md` con latencia p50/máx, tokens de entrada y salida, tokens/s de generación y de lectura del prompt, aciertos y memoria usada.

| Tarea | p50 (s) | tok/s generación | tok/s prompt | Aciertos % |
|---|---|---|---|---|
| Analizar (categoría) | *medir* | *medir* | *medir* | *medir* |
| Enriquecer (NER + sentimiento) | *medir* | *medir* | *medir* | *medir* |
| Resumen SEO | *medir* | *medir* | *medir* | *medir* |
| **Latencia por artículo** | *medir* | | | |

Hardware usado: *completar con la salida del script (CPU, RAM, GPU)*.

Cómo leer los "aciertos": con solo 5 muestras etiquetadas a mano son una **señal de humo, no una evaluación estadística**. Para conclusiones de calidad hay que ampliar a 30-50 artículos reales del cliente (ver RFC, sección 10).

## 4. Comparativa de respuestas: Ollama vs API cloud

```bash
# Vertex AI (alineado con el curso)
export GCP_PROJECT=mi-proyecto VERTEX_MODEL=<modelo-vigente> CLOUD_PRICE_IN=<usd/1M> CLOUD_PRICE_OUT=<usd/1M>
python backend/scripts/compare_providers.py --cloud vertex
# o Anthropic
export ANTHROPIC_API_KEY=... ANTHROPIC_MODEL=<modelo-vigente>
python backend/scripts/compare_providers.py --cloud anthropic
```
El script envía **el mismo prompt, con temperatura 0**, a ambos proveedores y escribe `backend/results/compare.md` con una tabla resumen y las respuestas lado a lado. Los nombres de modelo y los precios no se fijan en el código a propósito: cambian con frecuencia; usa los vigentes al momento de medir.

## 5. Análisis honesto de limitaciones frente a Vertex AI

Lo que sigue son **expectativas razonadas, no resultados**; la comparativa del punto 4 debe confirmarlas o refutarlas con datos.

| Dimensión | llama3.2:3b local | Modelo cloud (p. ej. Vertex AI) | Impacto en este proyecto |
|---|---|---|---|
| **Calidad** | Un modelo de 3B y cuantizado a 4 bits comete más errores de NER, confunde categorías cercanas (política/internacional) y genera entidades que no están en el texto. | Un modelo mucho mayor suele seguir mejor las instrucciones y los formatos. | Mayor tasa de correcciones manuales; el pipeline compensa con catálogos cerrados y normalización, que ocultan errores pero no los eliminan. |
| **Formato de salida** | El modo JSON de Ollama ayuda, pero el contenido puede salir incompleto o con tipos erróneos. | Salida estructurada con esquema suele ser más fiable. | Por eso existen el parseo tolerante y los valores por defecto ('otros', 'neutral'). |
| **Latencia** | Depende por completo del hardware: en CPU, decenas de segundos por artículo (3 llamadas); con GPU, pocos segundos. Arranque en frío al cargar el modelo. | Típicamente de 1 a pocos segundos por llamada, sin arranque en frío. | No afecta al webhook (202 inmediato), pero sí el tiempo hasta tener el resultado y la capacidad por hora. |
| **Capacidad / escalado** | Una instancia procesa pocas peticiones a la vez; escalar exige más hardware. | Escala por cuota, sin operar infraestructura. | Para picos de tráfico, la cola en memoria y un único Ollama son el cuello de botella. |
| **Costo** | Marginal casi nulo, pero con **costo fijo** de máquina y energía (ver RFC, sección 8: con supuestos ilustrativos, la API cloud sale más barata a volúmenes bajos y medios). | Variable por token; sin costo fijo. | La elección local se sostiene por privacidad y control, no por ahorro a bajo volumen. |
| **Privacidad** | El texto nunca sale de la infraestructura. | El contenido viaja al proveedor (revisar contrato y región). | Ventaja clara del modo local si el cliente tiene restricciones. |
| **Disponibilidad y operación** | Tú operas el servidor, las actualizaciones y los reinicios. | SLA del proveedor. | Más carga operativa para un equipo de 2-3 personas. |
| **Contexto** | Eficaz con textos cortos; artículos largos se recortan a 6.000 caracteres. | Contextos mucho mayores sin recorte. | Posible pérdida de información al final de artículos largos. |

**Conclusión provisional:** el modo local es defendible por privacidad, independencia y cumplimiento de la modalidad, pero hay que declarar abiertamente que probablemente pierde en calidad y latencia. La decisión definitiva debe apoyarse en `backend/results/compare.md` y en el análisis de costos (E6).

## 6. Ejecución reproducible

```bash
bash backend/scripts/install_ollama.sh               # Ubuntu 24.04: Ollama + modelo + backend
python backend/scripts/benchmark_ollama.py --runs 3 # benchmarks -> backend/results/benchmark.md
python backend/scripts/compare_providers.py --cloud vertex   # comparativa -> backend/results/compare.md
```
