# Traducciones de Biohazard: Project Genesis

Textos del modpack y sus traducciones, **con la misma estructura que la instancia de Minecraft**: lo que hay
aquí se copia tal cual dentro de la carpeta de la instancia. Las traducciones se hacen en Crowdin
(https://crowdin.com/project/biohazard); este repositorio es la copia maestra y el historial.

| Carpeta | Qué es | Origen |
|---|---|---|
| `kubejs/assets/ftbquestlocalizer/lang/` | Misiones (FTB Quests), ~1.636 textos | `en_us.json` |
| `kubejs/assets/biohazard/lang/` | Menú principal, 12 textos | `en_us.json` |
| `kubejs/assets/mca/lang/` | Introducción de MCA, 4 textos | `en_us.json` |
| `resourcepacks/BiohazardCustoms/assets/minecraft/lang/` | Dos libros, 12 textos. En la instancia va **comprimido** como `resourcepacks/BiohazardCustoms.zip` | `en_us.json` |

- El origen en Crowdin es el **inglés** (`en_us.json`). El español (`es_es.json`) es nuestro y se sube como
  traducción aprobada. `es_mx.json` no se guarda: se genera copiando `es_es.json` al exportar.
- Idiomas: ar_sa, bg_bg, de_de, es_es, fr_fr, it_it, ja_jp, ko_kr, pl_pl, pt_br, pt_pt, ru_ru, tr_tr, zh_cn,
  th_th, nl_nl, sv_se, uk_ua, vi_vn, id_id (los seis últimos, añadidos el 09-10-2026, aún sin traducir).
- Las claves que no existen en `en_us.json` no se guardan en ningún idioma.

## Cómo se mueve todo (nada es automático)

En **Actions → Traducciones → Run workflow**:

1. **subir-textos**: sube a Crowdin los `en_us.json` de `main`. Hacerlo después de cambiar textos.
2. **subir-espanol**: sube los `es_es.json` como traducción aprobada.
3. **bajar-traducciones**: trae de Crowdin lo traducido y abre un pull request a `main`. Se revisa y se mezcla.

Después, lo que hay en `main` se copia a la instancia (o lo hace el panel del estudio). Secretos necesarios en
el repositorio: `CROWDIN_PROJECT_ID` y `CROWDIN_PERSONAL_TOKEN`.

## Historia

Hasta el 09-10-2026 el repo tenía carpetas `ftb-quests/`, `main-menu/`, `mca/` y `biohazard-customs/` y la
integración automática de Crowdin, que escribía las traducciones con una carpeta de idioma delante
(`bg/ftb-quests/bg_bg.json`) porque las rutas de `crowdin.yml` no empezaban por `/`. Se reestructuró a las
rutas de la instancia y se pasó a la acción manual.
