# -*- coding: utf-8 -*-
import logging
import json
import scrapy
from lxml import html
from scrapy.shell import inspect_response

LOGGER = logging.getLogger(__file__)


class RewCaVanCssSpider(scrapy.Spider):
    name = 'rew-ca-van-css'
    allowed_domains = ['rew.ca']
    base_url = 'https://www.rew.ca'
    start_urls = ['https://www.rew.ca/properties/areas/vancouver-bc']

    def parse(self, response):
        # inspect_response(response,self)
        pages = []
        subareas = response.css('a.subarealist-item::text').extract()
        links = response.css('a.subarealist-item').extract()

        for subarea, link in zip(subareas, links):
            page_dict = {}
            page_dict['subarea'] = subarea.rsplit('(')[0]
            LOGGER.info(html.fromstring(link).get('href'))
            child_link = self.base_url + html.fromstring(link).get('href')
            page_dict['link'] = child_link
            pages.append(page_dict)
            yield scrapy.Request(url=child_link, callback=self.parse_main, meta=page_dict)

    # parse main page:
    def parse_main(self, response):
        """
        Parse main listings page
        :param response:
        :return:
        """
        # inspect_response(response, self)

        listing_dict = {}
        addresses = response.css("span.listing-address").css("a:link").extract()
        prices = response.css("div.listing-price::text").extract()
        for address, price in zip(addresses, prices):
            listing_dict['address'] = html.fromstring(address).get("title")
            listing_dict['price'] = int(price.replace('$', '').replace(',', ''))
            listing_dict['subarea'] = response.meta['subarea']
            href = html.fromstring(address).get("href")
            # within link:
            child_link = self.base_url + href
            listing_dict['link'] = child_link
            # LOGGER.info(child_link)
            # yield listing_dict
            yield scrapy.Request(url=child_link, callback=self.parse_child_page, meta=listing_dict)

        # next_url = response.css()
        ul = response.css("div.paginator.paginator").css('ul').extract()
        if ul:
            ul_text = ul[0].replace('\n', '')
            ul_html = html.fromstring(ul_text)
            all_li = ul_html.findall("li")
            for li in all_li:
                a = li.find("a")
                if a is not None:
                    rel = a.get("rel")
                    if rel == 'next':
                        next_url = self.base_url + a.get("href")
                        if next_url is not None:
                            yield scrapy.Request(response.urljoin(next_url))

    def parse_child_page(self, response):
        # LOGGER.info(response)
        # inspect_response(response, self)
        listing_dict = {}
        listing_dict['address'] = response.meta['address']
        listing_dict['price'] = response.meta['price']
        listing_dict['link'] = response.meta['link']
        listing_dict['subarea'] = response.meta['subarea']

        listing_dict['address'] = response.css('div.propertyheader-address').css("span::text").extract()[0]
        summary_spans = response.css("div.summarybar--property").css("span").extract()  # bed, bath, sqft, type
        for summary_span in summary_spans:
            text = summary_span.replace('\n', '')
            span = html.fromstring(text)
            val = html.fromstring(text).find("strong").text
            key = span.text_content().replace(val, '').lower()  # hack way to get this
            listing_dict[key] = val
        info_tables = response.css('table.contenttable').extract()
        for table in info_tables:
            table_html = html.fromstring(table)
            trs = table_html.find('tbody')
            if trs is not None:
                trs = trs.findall('tr')
                for tr in trs:
                    try:
                        key = tr.find('th').text
                        val = tr.find('td').text.replace('\n', '')
                        listing_dict[key] = val
                    except Exception as e:
                        LOGGER.info(e)
        school_info_list = response.css('div.detailslist-row_cap').extract()
        all_schools = []
        for school_info in school_info_list:
            school_info = school_info.replace('\n', '')
            school_info_html = html.fromstring(school_info)
            distance = school_info_html.find('a').text
            attrib = school_info_html.find('a').attrib
            school_info = json.loads(attrib.values()[0])
            school_info['distance'] = distance
            all_schools.append(school_info)
        listing_dict['school_info'] = all_schools
        yield listing_dict
