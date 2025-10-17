import asyncio
import requests
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from html import unescape


def _rsshub_base() -> str:
    import os
    return os.getenv('RSSHUB_BASE_URL', '').rstrip('/')


def parse_wechat_announce_xml(xml_text: str) -> Dict[str, Any]:
    """将微信公告的 RSS/Atom XML 文本解析为 JSON 可序列化字典。"""
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
                items.append({
                    'title': _text(it.find('title')),
                    'link': _text(it.find('link')),
                    'guid': _text(it.find('guid')),
                    'pubDate': _text(it.find('pubDate')),
                    'description': unescape(desc_raw) if desc_raw else None,
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
                items.append({
                    'title': _text(entry.find('.//{*}title')),
                    'link': link_href,
                    'guid': _text(entry.find('.//{*}id')),
                    'pubDate': _text(entry.find('.//{*}published')) or _text(entry.find('.//{*}updated')),
                    'description': unescape(summary_raw) if summary_raw else None,
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


async def get_wechat_announce() -> Dict[str, Any]:
    """获取微信公告的 RSS 源并解析为 JSON 可序列化的字典。"""
    url = f"{_rsshub_base()}/wechat/announce"
    try:
        response = await asyncio.to_thread(requests.get, url, timeout=15)
        response.raise_for_status()
        xml_text = response.text
    except Exception as e:
        return {"error": f"failed to fetch wechat announce: {e}", "url": url}

    return parse_wechat_announce_xml(xml_text)
