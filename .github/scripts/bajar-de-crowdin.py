#!/usr/bin/env python3
"""
Downloads the translations from Crowdin, file by file, straight to the paths of the instance.

Why not the Crowdin CLI: the CLI compares the "export pattern" each file has in Crowdin with the
`translation` of crowdin.yml, and silently drops every file where they differ. The four files of this
project were uploaded by hand / by the old native integration, so their export patterns are the old
ones and the CLI downloads nothing ("Couldn't find any file to download"). Here every file is asked
for by its id with the API, so the export patterns in Crowdin do not matter and nothing there changes.

Reads which files exist and where each language goes from crowdin.yml and crowdin-misiones.yml (one
source of truth). Untranslated strings are skipped, like `skip_untranslated_strings: true` did.
The token comes from the CROWDIN_PERSONAL_TOKEN environment variable and is never printed.

Usage: bajar-de-crowdin.py ["pt_br,th_th,..."] [--ensayo]
  languages: Minecraft codes; empty = all.  --ensayo: list what would be downloaded, write nothing.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

API = 'https://api.crowdin.com/api/v2'
PROJECT = os.environ.get('CROWDIN_PROJECT_ID', '').strip()
TOKEN = os.environ.get('CROWDIN_PERSONAL_TOKEN', '').strip()
BRANCH = os.environ.get('RAMA_MISIONES', '[YeraX7.crowdin-biohazard-translations] main')


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f'{API}{path}', data=data, method=method, headers={
        'Authorization': f'Bearer {TOKEN}', 'Accept': 'application/json',
        **({'Content-Type': 'application/json'} if data else {}),
    })
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read() or b'null')
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                time.sleep(2 ** attempt)
                continue
            detail = e.read().decode('utf-8', 'replace')[:300]
            sys.exit(f'Crowdin respondio {e.code} a {method} {path}: {detail}')
    sys.exit(f'Crowdin no respondio a {method} {path} tras 4 intentos')


def all_pages(path):
    out, offset = [], 0
    sep = '&' if '?' in path else '?'
    while True:
        r = call('GET', f'{path}{sep}limit=500&offset={offset}')
        out += [x['data'] for x in r['data']]
        if len(r['data']) < 500:
            return out
        offset += 500


def read_config(name):
    """[(dest, translation pattern, {crowdin code: minecraft code})] from a crowdin.yml of this repo."""
    text = open(name, encoding='utf-8').read()
    entries = []
    for block in re.findall(r'\{\s*"source".*?\}\s*\}\s*\}', text, re.S):
        dest = re.search(r'"dest":\s*"([^"]+)"', block).group(1)
        translation = re.search(r'"translation":\s*"([^"]+)"', block).group(1)
        mapping = json.loads(re.search(r'"locale_with_underscore":\s*(\{[^{}]*\})', block).group(1))
        entries.append((dest, translation, mapping))
    if not entries:
        sys.exit(f'No se encontraron archivos en {name}')
    return entries


def main():
    args = [a for a in sys.argv[1:] if a != '--ensayo']
    dry = '--ensayo' in sys.argv[1:]
    wanted = {c.strip() for c in (args[0] if args else '').replace(' ', ',').split(',') if c.strip()}
    if not PROJECT or not TOKEN:
        sys.exit('Faltan los secretos CROWDIN_PROJECT_ID / CROWDIN_PERSONAL_TOKEN')

    targets = call('GET', f'/projects/{PROJECT}')['data']['targetLanguageIds']
    branches = {b['name']: b['id'] for b in all_pages(f'/projects/{PROJECT}/branches')}
    if BRANCH not in branches:
        sys.exit(f'No existe en Crowdin la rama {BRANCH!r}')
    files = all_pages(f'/projects/{PROJECT}/files')

    def find(dest, branch_id):
        folder, name = os.path.split(dest)
        hits = [f for f in files if f['name'] == name and f.get('branchId') == branch_id
                and (f.get('path') or '').rstrip('/').endswith(dest)]
        if len(hits) != 1:
            sys.exit(f'En Crowdin hay {len(hits)} archivos que encajan con {dest} (se esperaba 1)')
        return hits[0]['id']

    plan = []
    for config, branch_id in (('crowdin.yml', None), ('crowdin-misiones.yml', branches[BRANCH])):
        for dest, translation, mapping in read_config(config):
            missing = [t for t in targets if t not in mapping]
            if missing:
                sys.exit(f'{config}: idiomas de Crowdin sin codigo de Minecraft: {", ".join(missing)}')
            file_id = find(dest, branch_id)
            for lang in targets:
                code = mapping[lang]
                if wanted and code not in wanted:
                    continue
                plan.append((file_id, dest, lang, translation.lstrip('/').replace('%locale_with_underscore%', code)))
    unknown = wanted - {p[3].rsplit('/', 1)[1][:-5] for p in plan}
    if unknown:
        sys.exit(f'Idiomas pedidos que no estan en Crowdin: {", ".join(sorted(unknown))}')

    print(f'{len(plan)} archivos ({len({p[2] for p in plan})} idiomas x {len({p[0] for p in plan})} archivos de Crowdin)')
    if dry:
        for file_id, dest, lang, path in plan:
            print(f'  {dest} [{lang}] -> {path}')
        return

    written = empty = 0
    for file_id, dest, lang, path in plan:
        url = call('POST', f'/projects/{PROJECT}/translations/builds/files/{file_id}',
                   {'targetLanguageId': lang, 'skipUntranslatedStrings': True})['data']['url']
        with urllib.request.urlopen(url, timeout=120) as r:
            raw = r.read()
        content = json.loads(raw.decode('utf-8-sig'))
        if not any(isinstance(v, str) for v in content.values()) and not os.path.exists(path):
            empty += 1  # nothing translated and no file yet: do not create an empty one
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as fh:
            fh.write(raw)
        written += 1
    print(f'Escritos: {written} | sin nada traducido (no se crean): {empty}')


if __name__ == '__main__':
    main()
