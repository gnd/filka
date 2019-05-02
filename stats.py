# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import scrapy
import operator
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher
import unicodedata

class StatsSpider(scrapy.Spider):
    name = 'stats'
    country_arr = {}
    i = 0

    def __init__(self, year="", delay=1.0, *args, **kwargs):
        super(StatsSpider, self).__init__(*args, **kwargs)
        self.year = year
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def start_requests(self):
        for self.i in range(12):
            print "------ SCRAPING: https://stream.filharmonia.sk/mp4stats/usage_{}{:02d}.html".format(self.year, self.i+1)
            yield scrapy.Request("https://stream.filharmonia.sk/mp4stats/usage_{}{:02d}.html".format(self.year, self.i+1), callback=self.parse)

    def parse(self, response):
        if ('Countries' in response.xpath('//table[11]//tr[2]').extract()[0]):
            hits_ = response.xpath('//table[11]//tr//td[2]/font/b/text()').extract()
            countries = response.xpath('//table[11]//tr//td[12]/font/text()').extract()
        elif ('Countries' in response.xpath('//table[12]//tr[2]').extract()[0]):
            hits_ = response.xpath('//table[12]//tr//td[2]/font/b/text()').extract()
            countries = response.xpath('//table[12]//tr//td[12]/font/text()').extract()
        else:
            hits_ = response.xpath('//table[13]//tr//td[2]/font/b/text()').extract()
            countries = response.xpath('//table[13]//tr//td[12]/font/text()').extract()

        for i in range(len(hits_)):
            hits = int(hits_[i])
            country = countries[i]

            if (country in self.country_arr):
                self.country_arr[country] += hits
            else:
                self.country_arr[country] = hits

    def spider_closed(self, spider):
        countries_sorted = sorted(self.country_arr.items(), key=operator.itemgetter(1), reverse=True)
        rest = 0
        total = 0
        # add the data
        for country in countries_sorted[:9]:
            total += country[1]
        for country in countries_sorted[9:]:
            rest += country[1]
            total += country[1]
        # print out percentages
        print "----------- Year %s Top 10 -----------" % (self.year)
        for country in countries_sorted[:9]:
            print "%s %f" % (country[0].replace(' ','_'), float(country[1]) / total * 100)
        print "Zvysne %f" % (float(rest) / total * 100)
