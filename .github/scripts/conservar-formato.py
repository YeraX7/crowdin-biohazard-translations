#!/usr/bin/env python3
"""
Runs in the "bajar-traducciones" action, after the Crowdin CLI has written its files.

Crowdin writes every language file in its own format (4-space indent, LF, raw "&"). The files of the
instance each have their own (2 or 4 spaces, CRLF or LF or mixed, and es_es writes & as \\u0026 like
Gson). Without this, a download shows every file as changed even when no text changed.

What it does, for each language file the download created or changed:
  - Language not in the list (when a list is given): the file goes back to what it was (or is removed if
    it is new). Lets the action bring only some languages.
  - Existing file: starts from the file as it is in the repo and changes only the value of the keys whose
    text really changed, byte for byte the rest (line endings, indentation, escaping, order). Keys that
    Crowdin did not send (untranslated) are kept as they are; nothing is ever removed.
  - New file (a new language): written with exactly the format of a translated sibling in the same folder
    (same order of keys, indent, line endings, escaping), with only the keys Crowdin sent.
The result: the pull request shows only real text changes.

Usage: conservar-formato.py ["pt_br,th_th,..."]   (empty or no argument = all languages)
"""
import json
import os
import re
import subprocess
import sys

LANG_DIRS = (
    'kubejs/assets/ftbquestlocalizer/lang',
    'kubejs/assets/biohazard/lang',
    'kubejs/assets/mca/lang',
    'resourcepacks/BiohazardCustoms/assets/minecraft/lang',
)
SOURCE = 'en_us'
CODE = re.compile(r'^[a-z]{2}_[a-z]{2}$')
# one "key": "value" line, with its own indent, separator, trailing comma and line ending
LINE = re.compile(r'^(?P<pre>\s*)"(?P<key>(?:[^"\\]|\\.)*)"(?P<sep>\s*:\s*)"(?P<val>(?:[^"\\]|\\.)*)"(?P<post>[ \t]*,?[ \t]*)(?P<eol>\r?\n)?$')
GSON = {'<': '\\u003c', '>': '\\u003e', '&': '\\u0026', '=': '\\u003d', "'": '\\u0027'}


def git(*args, check=True):
    return subprocess.run(['git', *args], check=check, capture_output=True).stdout


def head_bytes(path):
    r = subprocess.run(['git', 'show', f'HEAD:{path}'], capture_output=True)
    return r.stdout if r.returncode == 0 else None


def encode(value, gson):
    s = json.dumps(value, ensure_ascii=False)[1:-1]
    if gson:
        s = ''.join(GSON.get(ch, ch) for ch in s)
    return s


def uses_gson(text):
    return '\\u0026' in text or '\\u003d' in text or '\\u0027' in text


def parse_lines(text):
    """[(line, match or None)] keeping each line ending."""
    return [(ln, LINE.match(ln)) for ln in text.splitlines(keepends=True)]


def fix_trailing_commas(lines):
    """After the last key line there must be no comma; every earlier key line needs one."""
    idx = [i for i, ln in enumerate(lines) if LINE.match(ln)]
    for n, i in enumerate(idx):
        m = LINE.match(lines[i])
        post = m.group('post')
        has = ',' in post
        want = n < len(idx) - 1
        if has != want:
            core = post.replace(',', '') if has else ',' + post.lstrip()
            lines[i] = lines[i][:m.start('post')] + core + lines[i][m.end('post'):]
    return lines


def merge_existing(orig, new):
    """Change only values that differ; keep everything else byte for byte. Keys not present are added
    at the end (before the closing brace) in the same style as the last key line."""
    bom = orig.startswith(b'\xef\xbb\xbf')
    text = orig.decode('utf-8-sig')
    gson = uses_gson(text)
    out, seen = [], set()
    last_key_line = None
    for ln, m in parse_lines(text):
        if m:
            key = json.loads(f'"{m.group("key")}"')
            seen.add(key)
            if key in new and json.loads(f'"{m.group("val")}"') != new[key]:
                ln = ln[:m.start('val')] + encode(new[key], gson) + ln[m.end('val'):]
            last_key_line = len(out)
        out.append(ln)
    missing = [k for k in new if k not in seen]
    if missing and last_key_line is not None:
        model = LINE.match(out[last_key_line])
        eol = model.group('eol') or ('\r\n' if '\r\n' in text else '\n')
        extra = [f'{model.group("pre")}"{encode(k, gson)}"{model.group("sep")}"{encode(new[k], gson)}",{eol}' for k in missing]
        if not out[last_key_line].endswith(('\n', '\r')):
            out[last_key_line] += eol
        out[last_key_line + 1:last_key_line + 1] = extra
        out = fix_trailing_commas(out)
    result = ''.join(out)
    json.loads(result)  # never write a broken file
    return (b'\xef\xbb\xbf' if bom else b'') + result.encode('utf-8')


def template_for(folder, skip):
    """A translated sibling to copy the format from: the one with most keys, not en_us/es_*."""
    best, best_n = None, -1
    for name in sorted(os.listdir(folder)):
        code = name[:-5]
        if not name.endswith('.json') or code in skip or code == SOURCE or code.startswith('es_'):
            continue
        raw = head_bytes(f'{folder}/{name}')
        if raw is None:
            continue
        n = len(json.loads(raw.decode('utf-8-sig')))
        if n > best_n:
            best, best_n = raw, n
    return best or head_bytes(f'{folder}/{SOURCE}.json')


def build_new(folder, code, new, skip):
    tpl = template_for(folder, skip)
    text = tpl.decode('utf-8-sig')
    gson = uses_gson(text)
    src = json.loads(head_bytes(f'{folder}/{SOURCE}.json').decode('utf-8-sig'))
    out = []
    for ln, m in parse_lines(text):
        if m:
            key = json.loads(f'"{m.group("key")}"')
            if key not in new:
                continue  # untranslated: left out, the game falls back to en_us
            ln = ln[:m.start('val')] + encode(new[key], gson) + ln[m.end('val'):]
        out.append(ln)
    # keys of en_us that the template does not have (template older than the source)
    have = {json.loads(f'"{m.group("key")}"') for ln, m in parse_lines(''.join(out)) if m}
    extra = {k: new[k] for k in src if k in new and k not in have}
    result = ''.join(fix_trailing_commas(out))
    if extra:
        return merge_existing(result.encode('utf-8'), {**{k: new[k] for k in have}, **extra})
    json.loads(result)
    return result.encode('utf-8')


def main():
    wanted = {c.strip() for c in (sys.argv[1] if len(sys.argv) > 1 else '').replace(' ', ',').split(',') if c.strip()}
    bad = [c for c in wanted if not CODE.match(c)]
    if bad:
        sys.exit(f'Codigos de idioma no validos: {", ".join(bad)} (formato Minecraft, p. ej. pt_br)')
    status = git('status', '--porcelain', '--untracked-files=all', '--', *LANG_DIRS).decode('utf-8').splitlines()
    changed = []
    for line in status:
        path = line[3:].strip().strip('"')
        folder, name = os.path.split(path)
        if folder not in LANG_DIRS or not name.endswith('.json'):
            continue
        changed.append((line[:2], folder, name[:-5], path))
    new_codes = {code for st, f, code, p in changed if st == '??'}
    kept, dropped, same = [], [], []
    for st, folder, code, path in sorted(changed, key=lambda x: x[3]):
        tracked = st != '??'
        if code == SOURCE or (wanted and code not in wanted):
            if tracked:
                git('checkout', '--', path)
            else:
                os.remove(path)
            dropped.append(path)
            continue
        with open(path, 'rb') as fh:
            new = json.loads(fh.read().decode('utf-8-sig'))
        new = {k: v for k, v in new.items() if isinstance(v, str)}
        if tracked:
            data = merge_existing(head_bytes(path), new)
        else:
            data = build_new(folder, code, new, new_codes)
        with open(path, 'wb') as fh:
            fh.write(data)
        (same if tracked and data == head_bytes(path) else kept).append(path)
    print(f'Con cambios reales: {len(kept)}')
    for p in kept:
        print(f'  {p}')
    print(f'Iguales a lo que habia (solo formato): {len(same)}')
    print(f'Descartados por no estar en la lista de idiomas: {len(dropped)}')


if __name__ == '__main__':
    main()
