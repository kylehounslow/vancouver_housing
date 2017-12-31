# -*- coding: utf-8 -*-
import logging
import scrapy
from lxml import html
from scrapy.shell import inspect_response

LOGGER = logging.getLogger(__file__)

class RealtorCaVanSpider(scrapy.Spider):
    name = 'realtor_ca_van'
    allowed_domains = ['realtor.ca']
    start_urls = ['https://www.realtor.ca/Residential/map.aspx#CultureId=1&ApplicationId=1&RecordsPerPage=9&MaximumResults=9&PropertySearchTypeId=1&TransactionTypeId=2&StoreyRange=0-0&BedRange=0-0&BathRange=0-0&LongitudeMin=-123.64539337158163&LongitudeMax=-121.56073760986288&LatitudeMin=48.97711924031795&LatitudeMax=49.71077272536693&SortOrder=A&SortBy=1&viewState=m&Longitude=-123.017799377441&Latitude=49.3621978759766&ZoomLevel=10&PropertyTypeGroupID=1/']

    def parse(self, response):
        inspect_response(response, self)

        return self.parse_main(response)
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
            listing_dict['price'] = price
            href = html.fromstring(address).get("href")
            # within link:
            child_link = self.base_url + href
            listing_dict['link'] = child_link
            # LOGGER.info(child_link)
            # yield listing_dict
            yield scrapy.Request(url=child_link, callback=self.parse_child_page, meta=listing_dict)

        # next_url = response.css()
        ul = response.css("div.paginator.paginator").css('ul').extract()
        ul_text = ul[0].replace('\n','')
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

        listing_dict['address'] = response.css('div.propertyheader-address').css("span::text").extract()[0]
        summary_spans = response.css("div.summarybar--property").css("span").extract() # bed, bath, sqft, type
        for summary_span in summary_spans:
            text = summary_span.replace('\n','')
            span = html.fromstring(text)
            val = html.fromstring(text).find("strong").text
            key = span.text_content().replace(val, '').lower() # hack way to get this
            listing_dict[key] = val
        yield listing_dict

