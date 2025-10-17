import asyncio
import requests
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from html import unescape
import re


def _rsshub_base() -> str:
    import os
    return os.getenv('RSSHUB_BASE_URL', '').rstrip('/')


def parse_github_trending_xml(xml_text: str) -> Dict[str, Any]:
    # 规范化：去除 BOM，修正分行的 XML 声明
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

    def _extract_summary_fields(summary_html: str) -> Dict[str, Any]:
        s = summary_html or ''
        # 图片
        img = None
        m = re.search(r'<img[^>]+src=[\"\']([^\"\']+)[\"\']', s, re.I)
        if m:
            img = m.group(1).strip()
        # 文本：去标签并保留换行
        text = re.sub(r'(?i)<br\s*/?>', '\n', s)
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('\xa0', ' ').replace('&nbsp;', ' ')
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        # 语言 / stars / forks
        language = None
        ml = re.search(r'(?i)Language:\s*([^\n]+)', text)
        if ml:
            language = ml.group(1).strip()
        stars = None
        ms = re.search(r'(?i)Stars:\s*([\d,._]+)', text)
        if ms:
            digits = re.sub(r'\D', '', ms.group(1))
            stars = int(digits) if digits else None
        forks = None
        mf = re.search(r'(?i)Forks:\s*([\d,._]+)', text)
        if mf:
            digits = re.sub(r'\D', '', mf.group(1))
            forks = int(digits) if digits else None
        # 描述：第一条非“Language/Stars/Forks”的行
        description_text = None
        for ln in lines:
            if not re.match(r'(?i)\s*(Language|Stars|Forks)\s*:', ln):
                description_text = ln
                break
        return {
            'image': img,
            'description_text': description_text,
            'language': language,
            'stars': stars,
            'forks': forks,
        }

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
                # author 兼容不同命名空间
                author = _text(it.find('author'))
                if not author:
                    creator_any_ns = it.find('.//{*}creator')
                    author = _text(creator_any_ns)
                summary_raw = _text(it.find('description'))
                summary_unescaped = unescape(summary_raw) if summary_raw else None
                extra = _extract_summary_fields(summary_unescaped or '') if summary_unescaped else {
                    'image': None, 'description_text': None, 'language': None, 'stars': None, 'forks': None
                }
                items.append({
                    'title': _text(it.find('title')),
                    'link': _text(it.find('link')),
                    'author': author,
                    'pubDate': _text(it.find('pubDate')),
                    'updated': _text(it.find('updated')),
                    'summary': summary_unescaped,
                    'image': extra['image'],
                    'description_text': extra['description_text'],
                    'language': extra['language'],
                    'stars': extra['stars'],
                    'forks': extra['forks'],
                })
            desc_raw = _text(channel.find('description'))
            return {
                'title': _text(channel.find('title')),
                'link': _text(channel.find('link')),
                'description': unescape(desc_raw) if desc_raw else None,
                'updated': _text(channel.find('lastBuildDate')),
                'items': items,
            }
        return {'title': None, 'link': None, 'description': None, 'updated': None, 'items': items}

    def parse_atom(r: ET.Element) -> Dict[str, Any]:
        items: List[Dict[str, Any]] = []
        for entry in r.findall('..//'):
            if _local(entry.tag) == 'entry':
                link_href = None
                link_el = entry.find('.//{*}link')
                if link_el is not None:
                    link_href = link_el.attrib.get('href')
                summary_raw = _text(entry.find('.//{*}summary')) or _text(entry.find('.//{*}content'))
                summary_unescaped = unescape(summary_raw) if summary_raw else None
                extra = _extract_summary_fields(summary_unescaped or '') if summary_unescaped else {
                    'image': None, 'description_text': None, 'language': None, 'stars': None, 'forks': None
                }
                items.append({
                    'title': _text(entry.find('.//{*}title')),
                    'link': link_href,
                    'author': _text(entry.find('.//{*}author/{*}name')),
                    'pubDate': _text(entry.find('.//{*}published')),
                    'updated': _text(entry.find('.//{*}updated')),
                    'summary': summary_unescaped,
                    'image': extra['image'],
                    'description_text': extra['description_text'],
                    'language': extra['language'],
                    'stars': extra['stars'],
                    'forks': extra['forks'],
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
    if root.find('channel') is not None:
        return parse_rss(root)
    return parse_atom(root)


async def get_github_trending(language: str = 'python', since: str = 'daily', spoken_language_code: str = 'en') -> Dict[str, Any]:
    url = f"{_rsshub_base()}/github/trending/{since}/{language}/{spoken_language_code}"
    try:
        response = await asyncio.to_thread(requests.get, url, timeout=15)
        response.raise_for_status()
        xml_text = response.text
    except Exception as e:
        return {"error": f"failed to fetch trending: {e}", "url": url}

    return parse_github_trending_xml(xml_text)



if __name__ == "__main__":
    import json

    async def main():
        result = await get_github_trending('python', 'daily', 'en')
        print(json.dumps(result, indent=2, ensure_ascii=False))

    asyncio.run(main())