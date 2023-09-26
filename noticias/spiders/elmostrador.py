import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider
from datetime import datetime
from bs4 import BeautifulSoup
from noticias.items import NoticiasItem
from noticias.utils import clean_text

class ElMostradorSpider(CrawlSpider):
    name = 'elmostrador'
    item_count = 0
    allowed_domain = ['www.elmostrador.cl']
    start_urls = [
        'https://www.elmostrador.cl/categoria/pais/',
        'https://www.elmostrador.cl/categoria/agenda-sustentable/'
    ]

    rules = {
        Rule(LinkExtractor(allow=['pais/page/', 'agenda-sustentable/page/'])),  # navigation
        Rule(LinkExtractor(allow=(), restrict_xpaths='//h4[@class="d-tag-card__title"]/a'),  # items
             callback='parse_item', follow=False)
    }

    def parse_item(self, response):
        news_item = NoticiasItem()
        news_item['media'] = 'elmostrador'

        # Article title & subtitle
        news_item['title'] = clean_text(response.xpath('//h1/text()').extract())
        news_item['subtitle'] = clean_text(response.xpath('//p[@class="d-the-single__excerpt | u-fw-600"]/text()').extract())
        
        if not news_item['title']:
            return

        # Article Body (B4S to extract the bold and link texts)
        article_text = ''
        soup = BeautifulSoup(response.body, 'html.parser')
        main_content = soup.find('main')
        paragraphs = main_content.select('p')

        for paragraph in paragraphs:
            text_parts = []
            for element in paragraph.contents:
                if element.name in ('a', 'strong'):
                    text_parts.append(element.get_text())
                elif isinstance(element, str):
                    text_parts.append(element)
            paragraph_text = ' '.join(text_parts).strip()
            article_text += paragraph_text + ' '

        news_item['body'] = clean_text(article_text.strip())

        # Fecha de publicación
        time_element = soup.find('time')
        datetime_str = time_element.get('datetime')

        try:
            published_time = datetime.strptime(datetime_str, "%Y-%m-%d")
        except:
            published_time = datetime.strptime(datetime_str, "%d-%m-%Y")

        news_item['date'] = datetime_str

        # URL de la noticia
        news_item['url'] = response.url

        days = (datetime.now().replace(tzinfo=None) - published_time.replace(tzinfo=None)).days
        if days > 1:
            return

        yield news_item
