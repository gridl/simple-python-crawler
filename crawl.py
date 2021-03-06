import argparse
import asyncio
from urllib.parse import urljoin, urlsplit

import aiohttp
import logging
from bs4 import BeautifulSoup


__all__ = ['main']
_crawled_pages = []


def check_link(from_url, to_url):
    # don't follow links out from the domain
    parts = urlsplit(to_url)
    if parts.hostname and parts.hostname != urlsplit(from_url).hostname:
        return False

    # strip query string
    url = urljoin(from_url, parts.path)

    # ensure we don't crawl the same page twice
    if url in _crawled_pages:
        return False
    else:
        _crawled_pages.append(url)

    return True


async def handle_page(loop, session, url, depth_remaining):
    logging.info('Getting {}'.format(url))

    # get page
    async with session.get(url) as response:
        # get the page
        html = await response.text()
        soup = BeautifulSoup(html, 'html.parser')

        # recurse if we have depth left
        if depth_remaining > 1:
            links = [link.get('href') for link in soup.find_all('a')]
            for link in links:
                new_url = urljoin(url, link)

                # check whether we want to follow the link
                if check_link(url, new_url):
                    await handle_page(loop, session, new_url, depth_remaining - 1)

        # print image links
        images = [img.get('src') for img in soup.find_all('img', src=True)]
        for image in images:
            print(urljoin(url, image))


async def crawl(loop, url, depth):
    logging.info('Parsing {} for {} level(s)'.format(url, depth))

    # run checklink to add initial page to the crawled pages list
    check_link(url, url)

    async with aiohttp.ClientSession(loop=loop) as session:
        await handle_page(loop, session, url, depth)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url', metavar='URL', help='The URL to crawl')
    parser.add_argument('--depth', dest='depth', type=int, default=1,
                        help='How many levels of links should be followed')
    parser.add_argument('--debug', dest='debug', action='store_const', const=True, default=False,
                        help='Should debug messages be printed')
    arguments = parser.parse_args()


    if arguments.debug:
        logging.basicConfig(level=logging.DEBUG)

    # start crawling async
    loop = asyncio.get_event_loop()
    loop.run_until_complete(crawl(loop, arguments.url, arguments.depth))


if __name__ == '__main__':
    main()
