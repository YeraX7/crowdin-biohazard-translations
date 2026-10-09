# Traducciones de Biohazard: Project Genesis

Textos del modpack y sus traducciones, **con la misma estructura que la instancia de Minecraft**: lo que hay
aqui se copia tal cual dentro de la carpeta de la instancia. Las traducciones se hacen en Crowdin
(https://crowdin.com/project/biohazard); este repositorio es la copia maestra y el historial.

**Este repositorio no es el modpack.** Cambiar algo aqui no cambia nada para los jugadores: los textos
solo llegan al juego cuando alguien los publica en el pack.

| Carpeta | Que es | Archivo de Crowdin |
|---|---|---|
| `kubejs/assets/ftbquestlocalizer/lang/` | Misiones (FTB Quests), 1.636 textos | `ftb-quests/en_us.json` (rama `[YeraX7.crowdin-biohazard-translations] main`) |
| `kubejs/assets/biohazard/lang/` | Menu principal, 12 textos | `main-menu-RP-en_us.json` |
| `kubejs/assets/mca/lang/` | Introduccion de MCA, 4 textos | `mca_introduction-en_us.json` |
| `resourcepacks/BiohazardCustoms/assets/minecraft/lang/` | Dos libros, 12 textos. En la instancia van **dentro** de `resourcepacks/BiohazardCustoms.zip` (junto con imagenes que aqui no estan) | `bh_customs-RP-en_us.json` |

- Origen en Crowdin: el **ingles** (`en_us.json`). El espanol es nuestro. `es_mx.json` no esta en Crowdin.
- Los `.json` se guardan **byte a byte** (`.gitattributes`), sin reformatear.
- Idiomas en Crowdin (20): ar, bg, de, es-ES, fr, it, ja, ko, pl, pt-PT, pt-BR, ru, tr, zh-CN, th, nl, sv-SE,
  uk, vi, id. Los siete ultimos se anadieron el 09-10-2026 y aun no tienen traducciones.

## Como se mueve todo (nada es automatico)

**Actions → Traducciones → Run workflow**:

1. **comprobar**: ensayo que no cambia nada. Empezar siempre por aqui.
2. **bajar-traducciones**: trae de Crowdin lo traducido a una rama nueva y abre un pull request a `main`.
3. **subir-textos**: sube a Crowdin los `en_us.json` de `main` (cuando cambian los textos del juego).

El espanol no se sube desde aqui (ver el comentario de `.github/workflows/traducciones.yml`).

Secretos necesarios en el repositorio: `CROWDIN_PROJECT_ID` y `CROWDIN_PERSONAL_TOKEN`. Para que la accion
pueda abrir el pull request: Settings → Actions → General → "Allow GitHub Actions to create and approve
pull requests" (si no, deja la rama hecha y el PR se abre a mano).

## Historia

- Hasta el 09-10-2026: carpetas `ftb-quests/`, `main-menu/`, `mca/`, `biohazard-customs/` y la integracion
  automatica de Crowdin (cada hora), que escribia las traducciones con una carpeta de idioma delante
  (`bg/ftb-quests/bg_bg.json`) porque las rutas de `crowdin.yml` no empezaban por `/`.
- 09-10-2026: `main` pasa a ser una copia exacta (byte a byte, 58 archivos) de los textos de la instancia
  publicada de CurseForge; la integracion automatica queda pausada y la sustituye la accion manual.
  Copias de todo lo anterior: `panel-estudio/backups/2026-10-09/` en el PC del estudio.
