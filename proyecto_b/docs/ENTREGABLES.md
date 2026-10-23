# Indice de entregables (Proyecto B, modalidad 2.3)

| Entregable | Pts | Archivo | Estado |
|---|---|---|---|
| E1 Diagrama de arquitectura | 15 | `docs/E1_Diagrama_Arquitectura.pdf` (+ `docs/diagrams/*.png` y fuentes `.dot`) | Listo |
| E2 Documento de diseno (RFC) | 15 | `docs/E2_Documento_de_Diseno_RFC.pdf` | Listo. Completar autores; alinear seccion 8 con E6 |
| E3 Backend funcional | 15 | `backend/app/`, `backend/scripts/install_ollama.sh`, `Makefile` | Listo; probar con `make smoke` |
| E4 Frontend funcional | 10 | `frontend/` (carpeta propia) | Listo; probar con `make frontend-dev` |
| E5 Video de presentacion | 20 | Guion en un documento de Claude (fuera del zip) | Falta grabar (MP4, max. 30 min) |
| E6 Analisis de costos | 15 | `docs/E6_Analisis_de_Costos.xlsx` | Listo; reemplazar supuestos con mediciones |
| E7 Reflexion critica | 10 | Borrador en un documento de Claude (fuera del zip) | Completar los [COMPLETAR] y exportar a PDF (max. 3 pp) |

Criterios de la modalidad 2.3: `docs/MODELO_OLLAMA.md` (ficha GGUF, RAM, limitaciones vs Vertex AI),
`backend/scripts/benchmark_ollama.py` y `backend/scripts/compare_providers.py` (benchmarks y comparativa).

**E5 y E7** viven como documentos editables en la conversacion de Claude. Exportalos desde alli a PDF o Markdown
y guardalos en `docs/` antes de entregar.

## Orden recomendado para cerrar el proyecto
1. `make install` (o `make venv` si ya tienes Ollama) y `make run`.
2. `make smoke` para confirmar que el sistema funciona de punta a punta.
3. `make benchmark` y `make compare CLOUD=vertex` -> pegar cifras en `docs/MODELO_OLLAMA.md` y en E6.
4. Revisar E6 con las mediciones; actualizar el RFC si cambian las conclusiones.
5. Grabar el video siguiendo el guion; completar E7; `make zip`.
