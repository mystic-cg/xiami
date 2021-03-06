#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by PyCharm
# @author  : mystic
# @date    : 2017/12/28 11:12
import scrapy
from bs4 import BeautifulSoup
from scrapy import Request, Selector, FormRequest
from scrapy.http import HtmlResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from xiami.items import XiamiItem


class Spider(CrawlSpider):

    def __init__(self, email='xxx@qq.com', upwd='xxx'):
        # 执行父类构造方法
        super(Spider, self).__init__()
        self.account_number = email
        self.password = upwd

    # 爬虫名
    name = 'Ada'
    allowed_domains = ['xiami.com']
    start_urls = ['http://www.xiami.com']

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.8",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
        "Referer": "https://login.xiami.com/member/login?spm=a1z1s.6843761.226669498.1.2iL1jx"
    }

    rules = {
        Rule(LinkExtractor(
            allow=('/search/song/page/1?spm=a1z1s.3521869.0.0.N35ts9&key=%E9%99%88%E5%A5%95%E8%BF%85&category=-1',)),
             callback='parse_page', follow=True),
    }

    def start_requests(self):
        return [Request('https://login.xiami.com/member/login',
                        meta={'cookiejar': 1},
                        callback=self.post_login)]

    # FormRequest
    def post_login(self, response):
        print('Preparing login')
        # 下面这句话用于抓取请求页面后返回页面汇总的_xiamitoken字段的文字，用于成功提交表单
        _xiamitoken = Selector(response).xpath('//input[@name="_xiamitoken"]/@value').extract_first()
        print('验证信息: ', _xiamitoken)
        # FormRequest.from_response是Scrapy提供的一个函数，用于post表单
        # 登陆成功后，会调用after_login回调函数
        return [FormRequest.from_response(response,
                                          meta={'cookiejar': response.meta['cookiejar']},
                                          headers=self.headers,
                                          formdata={
                                              'source': 'index_nav',
                                              '_xiamitoken': _xiamitoken,
                                              'email': self.account_number,
                                              'password': self.password
                                          },
                                          callback=self.after_login,
                                          dont_filter=True)]

    def after_login(self, response):
        print('after login=======')
        for url in self.start_urls:
            # 创建Request
            yield Request(url, meta={'cookiejar': response.meta['cookiejar']})

    def _requests_to_follow(self, response):
        if not isinstance(response, HtmlResponse):
            return
        seen = set()
        for n, rule in enumerate(self._rules):
            links = [lnk for lnk in rule.link_extractor.extract_links(response)
                     if lnk not in seen]
            if links and rule.process_links:
                links = rule.process_links(links)
            for link in links:
                seen.add(link)
                r = Request(url=link.url, callback=self._response_downloaded)
                # 重写
                r.meta.update(rule=n, link_text=link.text, cookiejar=response.meta['cookiejar'])
                yield rule.process_request(r)

    def parse(self, response):
        num_pages = 66
        base_url = 'http://www.xiami.com/search/song/page/{0}' \
                   '?spm=a1z1s.3521869.0.0.N35ts9&key=%E9%99%88%E5%A5%95%E8%BF%85&category=-1'
        for page in range(1, num_pages):
            yield scrapy.Request(base_url.format(page), dont_filter=True, callback=self.parse_page)

    def parse_page(self, response):
        html = response.body
        soup = BeautifulSoup(html, 'lxml')
        song_names = soup.select('td.song_name > a:nth-of-type(1)')
        song_artists = soup.select('td.song_artist > a')
        for i in range(len(song_artists)):
            if song_artists[i]['title'] != '陈奕迅':
                continue
            print(song_artists[i]['title'])
            print(song_names[i]['title'])
            item = XiamiItem()
            item['title'] = 'xiami_music'
            item['name'] = song_artists[i]['title']
            item['song'] = song_names[i]['title']
            yield item
