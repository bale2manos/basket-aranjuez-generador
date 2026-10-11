# Generador Basket Aranjuez 2.0 - temporada 2026/27

Genera portada, horarios y resultados en PNG de 1080x1350 desde un Excel.

## Uso sencillo en Windows

1. Descarga el ZIP de la release de GitHub y descomprimelo completo.
2. Abre `BasketAranjuezGenerador.exe`. Python y las fuentes van incluidos; no hace falta instalarlos.
3. Selecciona el Excel y la foto de fondo. La misma foto se usa en portada y partidos.
4. Elige Horarios o Resultados; para resultados selecciona tambien el Word `.docx`.
5. Pulsa Generar imagenes y despues Abrir carpeta generada.

Las carpetas `_internal`, `fonts`, `logos` y `data` deben permanecer junto al ejecutable.
Las salidas se guardan en `output/jornada_YYYY-MM-DD/horarios/` o `resultados/`.
Cada carpeta incluye `portada.png`, paginas `local1.png` / `visitante1.png`, `summary.json` y `run.log`.

## Datos y archivos editables

El Excel necesita las columnas Categoria (con o sin tilde), Local, Visitante, Fecha, Hora y Campo de juego.
Se ordenan los partidos por fecha y hora y se separan local y visitante, con un maximo de ocho partidos por pagina.
Las filas amarillas de playoffs muestran PLAYOFFS en horarios.

- `data/club_logo_map.csv`: nombres y logos de rivales.
- `data/venue_map.csv`: nombres de pistas y pabellones.
- `data/result_overrides.json`: marcadores pendientes. Escribe siempre el resultado en orden local-visitante.
- `logos/`: logos PNG editables. Si falta uno, se deja el hueco y se registra un aviso.

En resultados se ocultan fecha/hora/pabellon y la banda negra del perdedor se vuelve traslucida al 35% de opacidad.
Los nombres mantienen patrocinadores, anos, colores, letras de equipo y las correcciones Junior C/D y Senior Fem A.

## Uso desde Python

```powershell
pip install -r requirements.txt
python launcher.py
python main.py --mode horarios --excel-path "input/ejemplo.xlsx"
python main.py --mode resultados --excel-path "input/ejemplo.xlsx" --results-doc-path "resultados/cronicas.docx"
```

Las rutas se centralizan en `config.py`. Los argumentos CLI permiten sobrescribirlas en una ejecucion.
`font_path` es Barlow Bold; `number_font_path` y `cover_title_font_path` son Kvant; `cover_date_font_path` es Amoresa Aged.
El oscurecimiento de portada se controla con `cover_dark_overlay_opacity` (0.65 por defecto) o `--cover-dark-overlay-opacity`.
Una fuente o foto ausente produce un error con su ruta; no se sustituye silenciosamente.

## Diseno y calidad

Las bandas y hexagonos se dibujan como formas y los textos son dinamicos. El ZIP de referencia contiene ejemplos rasterizados.
Portada y partidos comparten el mismo recorte de la foto, en blanco y negro. El render se hace a doble resolucion y se reduce una vez.
Los cuadros de texto se miden por sus limites visibles para respetar cursivas y descendentes.
La cabecera y los ajustes Poppins de versiones anteriores ya no intervienen en el diseno 2.0.

## Compilar y comprobar

```powershell
pip install pyinstaller
./build_release.ps1
python -m unittest tests.test_assets tests.test_normalization tests.test_layout tests.test_pipeline tests.test_renderer tests.test_cover_renderer tests.test_results tests.test_design_v2 tests.test_launcher
```

La distribucion publica del generador se mantiene en `bale2manos/basket-aranjuez-generador`.
El codigo se publica bajo MIT. Las fuentes y los logos son recursos de sus respectivos autores; Barlow incluye su licencia OFL.
