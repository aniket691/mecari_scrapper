from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from mercari.spiders.mercari_spider import MercariSpider

if __name__ == '__main__':
    process = CrawlerProcess(get_project_settings())
    process.crawl(MercariSpider)
    process.start()