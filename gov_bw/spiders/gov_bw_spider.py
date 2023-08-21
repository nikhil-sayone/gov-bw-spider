import os
import scrapy
from urllib.parse import urljoin
from ..items import GovBwItem

class GovBwSpider(scrapy.Spider):
    name = 'govbw_spider'
    start_urls = ['https://www.gov.bw/']

    def parse(self, response):
        sections = response.xpath('//div[contains(@class, "highlight_content")]')
        for section in sections:
            department_name = section.xpath('.//h4/a/text()').get()
            department_link = section.css('h4 a::attr(href)').get()
            absolute_department_link = response.urljoin(department_link)
            
            yield scrapy.Request(absolute_department_link, callback=self.parse_department,
                                 meta={'department_name': department_name})

    def parse_department(self, response):
        link_selectors = response.css('a[gva_layout="menu-list"]::attr(href)').getall()
        department_name = response.meta['department_name']
        
        for link in link_selectors:
            absolute_link = response.urljoin(link)
            yield scrapy.Request(absolute_link, callback=self.parse_page,
                                 meta={'department_name': department_name})
            
    def parse_page(self, response):
        department_name = response.meta['department_name']
        sub_page_links = response.css('a[hreflang="en"]::attr(href)').getall()
        category_name = response.xpath('//h2[@class="block-title"]/span/text()').get()
        
        for link in sub_page_links: 
            sub_category_name = response.css('a[href="' + link + '"]::text').get()
            absolute_link = urljoin(response.url, link)
            yield scrapy.Request(absolute_link, callback=self.parse_final_data,
                                 meta={'department_name': department_name,
                                       'sub_category_name': sub_category_name,
                                       'category_name': category_name,
                                       'url': absolute_link})
                
    def parse_final_data(self, response):
        department_name = response.meta['department_name']
        sub_category_name = response.meta['sub_category_name']
        category_name = response.meta['category_name']
        title = response.xpath('//h2[@class="block-title"]/span/span/text()').get()
        url = response.meta['url']
         
        headings = response.xpath('//div[@class="field__label"]/text()').getall()        
        contents = [div.xpath('string()').get().strip().replace('\n', '').replace('\t', '') for div in response.xpath('//div[@class="field__item"]')]

        data = {'contents': {}}
        
        heading_counter = 1
        for heading, content in zip(headings, contents):
            if heading == 'Related Forms' or heading == 'Related Documents':
                continue
            data['contents'][f'heading{heading_counter}'] = heading.strip()
            data['contents'][f'content{heading_counter}'] = content.strip()
            heading_counter += 1
        
        pdf_filenames = response.xpath("//span[contains(@class, 'file--mime-application-pdf')]/a/text()").getall()
        pdf_filename = [pdf_link.split('/')[-1].strip() for pdf_link in pdf_filenames]      
        pdf_links = response.xpath('//span[contains(@class, "file--mime-application-pdf")]/a/@href').getall()
        for pdf_link in pdf_links:
            yield scrapy.Request(url=response.urljoin(pdf_link), callback=self.save_pdf)
            
        item = GovBwItem(
            url=url,
            department=department_name.strip(),
            section=category_name,
            title=title.strip(),
            contents=data['contents'],
            documents=pdf_filename,
        )
        yield item
        
    def save_pdf(self, response):
        filename = response.url.split('/')[-1]
        folder = 'gov_bw/gov_bw/related_documents'

        if not os.path.exists(folder):
            os.makedirs(folder)

        filepath = os.path.join(folder, filename)

        with open(filepath, 'wb') as f:
            f.write(response.body)