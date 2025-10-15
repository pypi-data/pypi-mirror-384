import re

from llm_web_kit.extractor.html.magic_html.extractors.base_extractor import \
    BaseExtractor
from llm_web_kit.extractor.html.magic_html.extractors.title_extractor import \
    TitleExtractor
from llm_web_kit.extractor.html.magic_html.utils import _tostring, load_html


class WeixinExtractor(BaseExtractor):
    """公众号文章抽取器."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def extract(self, html='', base_url='') -> dict:
        """抽取内容方法.

        Args:
            html: 网页str
            base_url: 网页对应的url

        Returns:
            抽取结果dict. For example:
            {
            "xp_num": "weixin",
            "drop_list": True,
            "html": "<html></html>",
            "title": "title",
            "base_url": "http://test.com/",
             }
        """
        tree = load_html(html)
        if tree is None:
            raise ValueError

        # 获取title
        title = TitleExtractor().process(tree)

        # base_url
        base_href = tree.xpath('//base/@href')

        if base_href and 'http' in base_href[0]:
            base_url = base_href[0]

        # 文章区域
        try:
            body_tree = tree.xpath('.//*[@id="img-content"]')[0]
        except Exception:
            raise ValueError

        # 去除 js , style, comment
        for script in body_tree.xpath('.//script'):
            self.remove_node(script)
        for style in body_tree.xpath('.//style'):
            self.remove_node(style)
        for comment in body_tree.xpath('.//comment()'):
            self.remove_node(comment)

        # 删除所有的公众号介绍
        for mp in body_tree.xpath('.//div[@id="meta_content"]'):
            self.remove_node(mp)
        for mp in body_tree.xpath('.//div[@id="js_tags"]'):
            self.remove_node(mp)
        for mp in body_tree.xpath('.//div[@class="original_area_primary"]'):
            self.remove_node(mp)
            # 隐藏的封禁 介绍
        for mp in body_tree.xpath('.//section[@class="wx_profile_card_inner"]'):
            self.remove_node(mp)
            # 特殊的wx卡片介绍
        for mp in body_tree.xpath(
                ".//section[contains(@class, 'wx_profile_msg_inner')]"
        ):
            self.remove_node(mp)

        #  针对杂乱内容进行去除
        all_raga = body_tree.xpath(
            ".//*[contains(@style, 'color: rgba(255, 255, 255, 0)')] | .//*[contains(@style, 'color: rgba(255 255 255 0)')]"
        )

        for mp in all_raga:
            flag_have_color_rgb, detail_style = self.ensure_have_color_rgb(
                mp.attrib['style']
            )

            if not flag_have_color_rgb:
                continue
            self.remove_node(mp)

        for img in body_tree.xpath('.//img'):

            if 'data-src' not in img.attrib:
                continue

            try:
                img.set('src', img.attrib['data-src'])
            except Exception:
                continue

        for h1 in body_tree.xpath('.//h1'):
            if not h1.text:
                continue
            h1.text = h1.text.replace('\n', '').strip()

        body_html = _tostring(body_tree)

        return {
            'xp_num': 'weixin',
            'drop_list': False,
            'html': body_html,
            'title': title,
            'base_url': base_url
        }

    @staticmethod
    def ensure_have_color_rgb(htmlstr):
        pattern = r'(?<!-)\bcolor\s*:\s*rgba\(\s*255\s*[,|\s]\s*255\s*[,|\s]\s*255\s*[,|\s]\s*0\s*\)'

        result = re.search(pattern, htmlstr)
        if result:
            return True, result.group()
        else:
            return False, ''
