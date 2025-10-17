import asyncio
import requests
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Iterable, Union
from html import unescape
from urllib.parse import quote
import re


def _rsshub_base() -> str:
    import os
    return os.getenv('RSSHUB_BASE_URL', '').rstrip('/')


def parse_steam_search_xml(xml_text: str) -> Dict[str, Any]:
    """将 Steam 搜索 RSS/Atom XML 文本解析为 JSON 可序列化字典。"""
    # 规范化：去除 BOM，修正可能换行的 XML 声明
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


def build_steam_search_param(
    *,
    maxprice: Optional[Union[str, int, float]] = None,
    hidef2p: Optional[Union[str, int, bool]] = None,
    specials: Optional[Union[str, int, bool]] = None,
    category1: Optional[Union[str, int]] = None,
    category2: Optional[Union[str, int]] = None,
    category3: Optional[Union[str, int]] = None,
    os: Optional[str] = None,
    tags: Optional[Union[str, Iterable[Union[str, int]]]] = None,
    sort_by: Optional[str] = None,
    term: Optional[str] = None,
    supportedlang: Optional[str] = 'schinese',
) -> str:
    """构建 steam/search 路由所需的 :param 字符串。

    - maxprice: 'free' 表示免费；数字表示 0～该价格；None 表示不限
    - hidef2p: 1/True 隐藏免费游戏；None/0/False 不隐藏
    - specials: 1/True 只看优惠；None/0/False 不限
    - category1: 998=游戏, 21=DLC, 996=捆绑包 等
    - category2: 30=支持创意工坊
    - category3: 2=单人, 1=多人, 9=合作, 49=对战
    - os: win/mac/linux
    - tags: 4182,492,... 可为逗号分隔字符串或可迭代；多个会以逗号连接
    - sort_by: Released_DESC/Name_ASC/Price_ASC/Price_DESC/Reviews_DESC 等
    - term: 名称模糊搜索关键词
    - supportedlang: 语言过滤（默认 schinese）
    """
    params: Dict[str, str] = {}

    if maxprice is not None:
        if isinstance(maxprice, (int, float)):
            params['maxprice'] = str(int(maxprice))
        else:
            v = str(maxprice).strip()
            if v:
                params['maxprice'] = v
    if hidef2p not in (None, '', 0, False, '0', 'false', 'False'):
        params['hidef2p'] = '1'
    if specials not in (None, '', 0, False, '0', 'false', 'False'):
        params['specials'] = '1'
    if category1 is not None and str(category1).strip() != '':
        params['category1'] = str(category1)
    if category2 is not None and str(category2).strip() != '':
        params['category2'] = str(category2)
    if category3 is not None and str(category3).strip() != '':
        params['category3'] = str(category3)
    if os is not None and str(os).strip() != '':
        params['os'] = str(os)
    if tags is not None:
        if isinstance(tags, str):
            tags_val = tags
        else:
            tags_val = ','.join(str(t) for t in tags)
        if tags_val:
            params['tags'] = tags_val
    if sort_by is not None and str(sort_by).strip() != '':
        params['sort_by'] = str(sort_by)
    if term is not None and str(term).strip() != '':
        params['term'] = str(term)
    if supportedlang is not None and str(supportedlang).strip() != '':
        params['supportedlang'] = str(supportedlang)

    # 直接拼接 key=value，并在外层对整段 :param 进行一次 quote，避免空格被转成 + 后无法还原为空格。
    query = '&'.join(f'{k}={v}' for k, v in params.items())
    return query


async def get_steam_search(param: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """调用 Steam 搜索 RSS 接口并解析为 JSON。

    使用方式：
    - 直接传入 param（如 'sort_by=Released_DESC&category1=10&os=linux'）
    - 或者通过可选参数构建：maxprice, hidef2p, specials, category1, category2, category3, os, tags, sort_by, term, supportedlang
    """
    if param is None:
        param = build_steam_search_param(**kwargs)
    # 将整个 :param 作为路径片段进行转义，避免 &、= 等在路径中被误解析
    param_enc = quote(param or '', safe='')
    url = f"{_rsshub_base()}/steam/search/{param_enc}"

    try:
        response = await asyncio.to_thread(requests.get, url, timeout=20)
        response.raise_for_status()
        xml_text = response.text
    except Exception as e:
        return {"error": f"failed to fetch steam search: {e}", "url": url}

    return parse_steam_search_xml(xml_text)


if __name__ == '__main__':
    import json
    # 示例：发行日期倒序，中文环境，按名称模糊匹配“无主之地”
    example_param = 'term=无主之地&supportedlang=schinese'
    result = asyncio.run(get_steam_search(example_param))
    print(json.dumps(result, ensure_ascii=False, indent=2))
