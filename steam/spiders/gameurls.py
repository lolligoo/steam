#-*- coding: utf-8 -*-

import re
import config
import utils
import json 
from scrapy.spiders import Spider
from scrapy import Request
from scrapy.selector import Selector
from sqlhelper import SqlHelper


class GameUrls(Spider):
    name = 'game_urls'
    #'https://store.steampowered.com/search/results/?query&start=150&count=50&dynamic_data=&sort_by=_ASC&snr=1_7_7_230_7&infinite=1'
    #start_urls = ['https://store.steampowered.com/search/?sort_by=Released_DESC&sort_order=DESC&page=%s' % n for n in range(1,3500)]
    start_urls = ['https://store.steampowered.com/search/results/?query&start=%s&count=50&dynamic_data=&sort_by=_ASC&&infinite=1' % n for n in range(50,100100,50)]
    def __init__(self, *a, **kw):
        super(GameUrls, self).__init__(*a, **kw)

        self.dir_game = 'log/%s' % self.name
        self.sql = SqlHelper()
        self.init()

        utils.make_dir(self.dir_game)

    def init(self):
        command = (
            "CREATE TABLE IF NOT EXISTS {} ("
            "`id` INT(10) NOT NULL AUTO_INCREMENT,"
            "`appid` VARCHAR(20) ,"
            "`type` VARCHAR(10) ,"
            "`name` TEXT ,"
            "`url` TEXT ,"
            "`released` VARCHAR(100) ,"
            "`price` VARCHAR(50) ,"
            "`is_crawled` VARCHAR(5) DEFAULT 'no',"
            "`page` INT(5) NOT NULL ,"
            "PRIMARY KEY(id)"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;".format(config.steam_game_urls_table))
        self.sql.create_table(command)

    def start_requests(self):
        for i, url in enumerate(self.start_urls):
            yield Request(
                    url = url,
                    headers = {
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept-Language': 'en-US;q=0.3,en;q=0.2',
                        'Connection': 'keep-alive',
                        'Host': 'store.steampowered.com',
                        'Upgrade-Insecure-Requests': '1',
                        #'Referer': url,
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
                    },
                    meta = {
                        'url': url,
                        'page': i + 1,
                    },
                    dont_filter = True,
                    callback = self.parse_all,
                    errback = self.error_parse,
            )

    def parse_all(self, response):
        # file_name = '%s/%s.html' % (self.dir_game, response.meta.get('page'))
        # self.save_page(file_name, response.body)

        self.log('parse_all url:%s' % response.url)

        game_list = Selector(text=json.loads(response.text).get('results_html')).xpath('//a[has-class("search_result_row")]').getall()

        for game in game_list:
            sel = Selector(text = "".join(game.splitlines()))
            url = sel.xpath('//@href').get()

            appid, apptype = self.get_id(url)
            # id = sel.xpath('//@data-ds-appid').extract_first()
            name = sel.xpath('//div[has-class("col","search_name","ellipsis")]/span/text()').get()
            released = sel.xpath('//div[has-class("col","search_released","responsive_secondrow")]/text()').get()
            price = sel.xpath('//div[has-class("col","search_price","responsive_secondrow")]/text()').get()
            msg = (None, appid, apptype, name.replace('\'','’'), url, released, price.strip(), 'no', response.meta.get('page'))
            # print(name.replace('\'','’'))
            command = ("INSERT INTO {} "
                       "(id, appid, type, name, url, released, price, is_crawled, page)"
                       "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)".format(config.steam_game_urls_table))

            self.sql.insert_data(command, msg)

    def error_parse(self, faiture):
        request = faiture.request
        utils.log('error_parse url:%s meta:%s' % (request.url, request.meta))

    def get_id(self, url):
        type = ''
        if '/sub/' in url:
            pattern = re.compile('/sub/(\d+)/')
            type = 'sub'
        elif '/app/' in url:
            pattern = re.compile('/app/(\d+)/', re.S)
            type = 'app'
        elif '/bundle/' in url:
            pattern = re.compile('/bundle/(\d+)/', re.S)
            type = 'bundle'
        else:
            pattern = re.compile('/(\d+)/', re.S)
            type = 'other'
            utils.log('get_id other url:%s' % url)

        id = re.search(pattern, url)
        if id:
            id = id.group(1)
            return id, type

        utils.log('get_id error url:%s' % url)
        return 0, 'error'

    def save_page(self, file_name, data):
        with open(file_name, 'w') as f:
            f.write(data)
            f.close()
