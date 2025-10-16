from __future__ import annotations

import hashlib
import re
from typing import Any, Dict

from sqlalchemy import text as sql_text
from openai import OpenAI
import json
import os

_WS = re.compile(r"\s+")

def _norm_space(s: str | None) -> str:
    return _WS.sub(" ", (s or "").strip())

def _firstline(s: str | None) -> str:
    s = (s or "").strip()
    return s.splitlines()[0].strip() if s else ""

def build_annex3_index(db, table_name: str = "rules") -> Dict[str, Any]:
    """
    Читает ТОЛЬКО таблицу `rules` и строит индекс Annex III:
      - areas: { "AnnexIII.1": "Label", ..., "AnnexIII.8": "Label" }
      - items: { "AnnexIII.1": [("AnnexIII.1.a","Short"), ...], ... }
      - content: { "AnnexIII.1.a": "<title>\\n<content>", ... }
    Любые строки без подпунктов автоматически считаются "item" самого area.
    """
    rows = db.execute(sql_text(f"""
        SELECT section_code,
               COALESCE(title,'')   AS title,
               COALESCE(content,'') AS content
        FROM {table_name}
        WHERE section_code LIKE 'AnnexIII%%'
        ORDER BY section_code
    """)).fetchall()

    areas: Dict[str, str] = {}
    items: Dict[str, list[tuple[str, str]]] = {}
    content_map: Dict[str, str] = {}

    for sc, title, content in rows:
        content_map[sc] = (title or "") + ("\n" if title and content else "") + (content or "")
        if sc.count(".") == 1:
            label = _norm_space(title) or _firstline(content) or sc
            areas[sc] = label
            items.setdefault(sc, [])
        elif sc.count(".") == 2:
            parent = sc.rsplit(".", 1)[0]
            raw = title or content or sc
            short = _firstline(raw).rstrip(".;")
            items.setdefault(parent, []).append((sc, short))

    # Если у области нет подпунктов — сделаем саму область её item'ом
    for area_code, label in list(areas.items()):
        if not items.get(area_code):
            items[area_code] = [(area_code, label)]

    # Стабильная сортировка подпунктов по коду
    for area_code in list(items.keys()):
        items[area_code] = sorted(items[area_code], key=lambda x: x[0])

    return {"areas": areas, "items": items, "content": content_map}

def annex3_hash(annex3_index: Dict[str, Any]) -> str:
    """
    Хэш только из КОДОВ и меток Annex III, чтобы любое изменение в `rules`
    гарантированно меняло хэш и триггерило регенерацию.
    """
    m = hashlib.sha256()
    for area_code in sorted(annex3_index["areas"].keys()):
        m.update(area_code.encode()); m.update(b"::")
        m.update(_norm_space(annex3_index["areas"][area_code]).encode())
    for area_code in sorted(annex3_index["items"].keys()):
        for code, label in annex3_index["items"][area_code]:
            m.update(area_code.encode()); m.update(b"::")
            m.update(code.encode()); m.update(b"::")
            m.update(_norm_space(label).encode())
    return m.hexdigest()

_ART5_RX = re.compile(r'^(?:article|art\.?)\s*0*5(?:\b|[.\(])', re.IGNORECASE)

def build_article5_index(db, table_name: str = "rules") -> dict:
    """
    Строим индекс ст.5 **без хардкода**, через LLM-валидацию:
    1) Читаем сырой текст ст.5 из БД.
    2) Просим LLM выделить только подпункты "Prohibited AI practices" первого параграфа с кодами (как в тексте).
    3) Возвращаем {"items": {code: short_label, ...}} — только эти позиции.
    """
    rows = db.execute(sql_text(f"""
        SELECT COALESCE(title,'')||E'\n'||COALESCE(content,'')
        FROM {table_name}
        WHERE section_code ~* '^(Article|Art\.)\s*5(\D|$)'
        ORDER BY section_code
    """)).fetchall()
    art5_text = "\n\n".join(r[0] for r in rows if r and r[0])[:6000]
    # fallback: если нечего парсить
    if not art5_text.strip():
        return {"items": {}}
    # Only use LLM if explicitly enabled and an API key is available.
    flag = (os.getenv("ARTICLE5_LLM_ENABLED", os.getenv("OBLIGATIONS_LLM_ENABLED", "false")) or "").strip().lower()
    if flag not in ("1", "true", "yes", "on"):
        return {"items": {}}
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        return {"items": {}}
    client = OpenAI(api_key=openai_key)
    prompt = f"""From the Article 5 text below, extract ONLY the prohibited practices listed in the FIRST paragraph.
For each item, output an object: {{"code":"5(1)(x) with your source's anchor style","label":"very short label"}}.
Return JSON object: {{"items":[...]}}. TEXT:\n{art5_text}"""
    try:
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL","gpt-4o-mini"),
            temperature=0, max_tokens=1200,
            response_format={"type":"json_object"},
            messages=[{"role":"user","content":prompt}]
        )
        js = json.loads(resp.choices[0].message.content)
        items = {}
        for it in (js.get("items") or []):
            code = it.get("code"); label = it.get("label")
            if isinstance(code, str) and code.strip():
                items[code.strip()] = (label or code)
        return {"items": items}
    except Exception:
        return {"items": {}}
