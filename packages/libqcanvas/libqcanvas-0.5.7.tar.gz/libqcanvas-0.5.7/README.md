# libqcanvas

This module uses the API client module and does most of the heavy lifting. It is concerned with synchronising with canvas and storing/reading the data on/from an SQLITE database. 

## Using API result caching for faster development

Set `ENABLE_API_CACHE=True` (or `1`) as an environment variable. This will store the result of each API call on disk for re-use next time.
The cache is written to `/tmp/qcanvas_cache`.

Only use this when debugging.