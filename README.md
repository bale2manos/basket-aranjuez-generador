# Generador de jornadas Basket Aranjuez

Aplicación para crear automáticamente las imágenes verticales de una jornada a partir de un Excel. Incluye los modos **Horarios** y **Resultados**, portadas, logos, mapas editables y salida preparada para Instagram.

## Uso sencillo en Windows

1. Descarga `BasketAranjuezGenerador-vX.Y.Z-windows.zip` desde **Releases**.
2. Descomprime el ZIP completo en una carpeta.
3. Abre `BasketAranjuezGenerador.exe`.
4. Selecciona el Excel y el modo.
5. En modo Resultados, selecciona también el documento `.docx` con los marcadores.
6. Pulsa **Generar imágenes**.

No hace falta instalar Python. Las imágenes aparecen en `output/jornada_YYYY-MM-DD/horarios` o `output/jornada_YYYY-MM-DD/resultados`.

## Archivos editables

- `logos/`: logos de clubes. Se pueden añadir PNG nuevos.
- `data/club_logo_map.csv`: relación entre nombre del rival y su logo.
- `data/venue_map.csv`: equivalencias de nombres de pabellones.
- `data/result_overrides.json`: resultados que no se hayan encontrado automáticamente.

El Excel debe tener las columnas `Categoría`, `Local`, `Visitante`, `Fecha`, `Hora` y `Campo de juego`. El fondo, la cabecera y la portada se pueden sustituir por archivos con el mismo nombre.

## Uso avanzado

Con Python instalado también se puede ejecutar desde una terminal:

```text
python main.py --mode horarios --excel-path "input\partidos.xlsx"
python main.py --mode resultados --excel-path "input\partidos.xlsx" --results-doc-path "resultados\cronicas.docx"
```

## Desarrollo y compilación

```text
pip install -r requirements.txt
python launcher.py
```

Para crear el ZIP portable de Windows, ejecuta `build_release.ps1` en PowerShell después de instalar PyInstaller.

## Licencia

MIT. Consulta `LICENSE`.
