import asyncio
import requests
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from html import unescape
from urllib.parse import quote
import re

ALLOWED_MODES = {'safe', 'r18', 'no'}
ALLOWED_ORDERS = {'date', 'popular'}


def parse_pixiv_search_xml(xml_text: str) -> Dict[str, Any]:
    """将 Pixiv 搜索的 RSS/Atom XML 文本解析为 JSON 可序列化字典。"""
    if xml_text:
        xml_text = xml_text.lstrip('\ufeff').strip()
        if xml_text.startswith('<?xml') and '\n' in xml_text[:60]:
            xml_text = xml_text.replace('<?xml\n', '<?xml ', 1)
    try:
        root = ET.fromstring(xml_text)
    except Exception as e:
        return {"error": f"failed to parse xml: {e}"}

    def _local(tag: str) -> str:
        return tag.split('}', 1)[-1] if '}' in tag else tag

    def _text(elem: Optional[ET.Element]) -> Optional[str]:
        return elem.text.strip() if elem is not None and elem.text else None

    def _extract_image_and_text(summary_html: Optional[str]) -> Dict[str, Optional[str]]:
        if not summary_html:
            return {"image": None, "text": None}
        s = summary_html
        m = re.search(r'<img[^>]+src=[\"\']([^\"\']+)[\"\']', s, re.I)
        img = m.group(1).strip() if m else None
        text = re.sub(r'(?i)<br\s*/?>', '\n', s)
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('\xa0', ' ').replace('&nbsp;', ' ').strip()
        return {"image": img, "text": text or None}

    def parse_rss(r: ET.Element) -> Dict[str, Any]:
        channel = r.find('channel')
        if channel is None:
            for child in r:
                if _local(child.tag) == 'channel':
                    channel = child
                    break
        items: List[Dict[str, Any]] = []
        if channel is not None:
            for it in channel.findall('item'):
                desc_raw = _text(it.find('description'))
                desc_unescaped = unescape(desc_raw) if desc_raw else None
                extra = _extract_image_and_text(desc_unescaped)
                items.append({
                    'title': _text(it.find('title')),
                    'link': _text(it.find('link')),
                    'guid': _text(it.find('guid')),
                    'pubDate': _text(it.find('pubDate')),
                    'description': desc_unescaped,
                    'image': extra['image'],
                    'description_text': extra['text'],
                })
            ch_desc_raw = _text(channel.find('description'))
            return {
                'title': _text(channel.find('title')),
                'link': _text(channel.find('link')),
                'description': unescape(ch_desc_raw) if ch_desc_raw else None,
                'updated': _text(channel.find('lastBuildDate')),
                'items': items,
            }
        return {'title': None, 'link': None, 'description': None, 'updated': None, 'items': items}

    def parse_atom(r: ET.Element) -> Dict[str, Any]:
        items: List[Dict[str, Any]] = []
        for entry in r.findall('.//'):
            if _local(entry.tag) == 'entry':
                link_href = None
                link_el = entry.find('.//{*}link')
                if link_el is not None:
                    link_href = link_el.attrib.get('href')
                summary_raw = _text(entry.find('.//{*}summary')) or _text(entry.find('.//{*}content'))
                summary_unescaped = unescape(summary_raw) if summary_raw else None
                extra = _extract_image_and_text(summary_unescaped)
                items.append({
                    'title': _text(entry.find('.//{*}title')),
                    'link': link_href,
                    'guid': _text(entry.find('.//{*}id')),
                    'pubDate': _text(entry.find('.//{*}published')) or _text(entry.find('.//{*}updated')),
                    'description': summary_unescaped,
                    'image': extra['image'],
                    'description_text': extra['text'],
                })
        feed_link_el = r.find('.//{*}link')
        feed_link = feed_link_el.attrib.get('href') if feed_link_el is not None else None
        subtitle_raw = _text(r.find('.//{*}subtitle'))
        return {
            'title': _text(r.find('.//{*}title')),
            'link': feed_link,
            'description': unescape(subtitle_raw) if subtitle_raw else None,
            'updated': _text(r.find('.//{*}updated')),
            'items': items,
        }

    root_name = _local(root.tag).lower()
    if root_name == 'rss':
        return parse_rss(root)
    if root_name == 'feed':
        return parse_atom(root)
    return parse_atom(root) if root.find('channel') is None else parse_rss(root)


def _rsshub_base() -> str:
    import os
    return os.getenv('RSSHUB_BASE_URL', '').rstrip('/')


async def get_pixiv_search(keyword: str, order: str = 'popular', mode: str = 'safe') -> Dict[str, Any]:
    """调用 Pixiv 搜索 RSS 接口并解析为 JSON。

    - keyword: 搜索关键字，将进行 URL 编码
    - mode 取值: safe, r18, no
    """
    if mode not in ALLOWED_MODES:
        return {"error": f"invalid mode: {mode}", "allowed": sorted(ALLOWED_MODES)}
    if order not in ALLOWED_ORDERS:
        return {"error": f"invalid order: {order}", "allowed": sorted(ALLOWED_ORDERS)}

    base = f'{_rsshub_base()}/pixiv/search'
    kw = quote(keyword, safe='')
    url = f"{base}/{kw}/{order}/{mode}"
    try:
        response = await asyncio.to_thread(requests.get, url, timeout=20)
        response.raise_for_status()
        xml_text = response.text
    except Exception as e:
        return {"error": f"failed to fetch pixiv search: {e}", "url": url}

    return parse_pixiv_search_xml(xml_text)


if __name__ == "__main__":
    import json

    result = asyncio.run(get_pixiv_search('高嶺愛花', 'popular', 'r18'))
    print(json.dumps(result, ensure_ascii=False, indent=2))
