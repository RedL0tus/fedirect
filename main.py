#!/usr/bin/env python3
# -*- encoding: UTF-8 -*-

import uvloop
import xmltodict

from collections import OrderedDict

from sanic import Sanic
from sanic import response
from sanic import exceptions
from sanic.log import logger

from aiohttp import ClientSession
from aiohttp.client_exceptions import ContentTypeError

# Config
HOST = '0.0.0.0'
PORT = '9090'

# Main program

# Initialize
LOOP = uvloop.new_event_loop()
CACHE = dict()
CLIENT = ClientSession(loop=LOOP)

app = Sanic(__name__)


def is_webfinger(link):
    """
    Test the URL is webfinger or not.
    :param link: link of the URL that is going to be tested.
    :return: True if yes, False if no.
    """
    if '@template' in link:
        if 'webfinger?resource={uri}' in link['@template']:
            return True
    return False


async def fetch(url):
    """
    Fetch data from url and transform it into an OrderedDict or something similar.
    Only supports XML and JSON.
    :param url: The URL that need :to be fetched.
    :return: JSON object if the URL returns JSON, OrderedDict if it returns XML.
    """
    async with CLIENT.get(url) as resp:
        if resp.status == 200:
            try:
                return await resp.json()
            except ContentTypeError:
                return xmltodict.parse(await resp.text())


@app.route("/<username>")
async def fetch_link(request, username):
    """
    Fetch link from the given username
    :param request: The thing that sanic give us, but seems it is useless in this case.
    :param username: The requested username.
    :return: Redirection if the profile page's link has been found.
    """
    logger.debug(request)  # Stop IDEA from blaming me about unused variable
    if username in CACHE.keys():
        logger.info('Cache hit: [ %s: %s ]' % (username, CACHE[username]))
        return response.redirect(CACHE[username])
    name = username.split('@')
    if len(name) != 2:
        raise exceptions.InvalidUsage('Invalid username', status_code=400)
    host_meta = await fetch('https://' + name[1] + '/.well-known/host-meta')
    try:
        host_links = host_meta['XRD']['Link']
    except TypeError:
        raise exceptions.InvalidUsage('Unsupported platform', status_code=400)
    # Get Webfinger's URL
    webfinger = ''
    if type(host_links) == list:
        for link in host_links:
            if is_webfinger(link):
                webfinger = link['@template']
                break
    elif type(host_links) == OrderedDict:
        if is_webfinger(host_links):
            webfinger = host_links['@template']
    else:
        raise exceptions.InvalidUsage('Unsupported platform', status_code=400)
    # Request Webfinger for user's meta
    user_meta = await fetch(webfinger.replace('{uri}', 'acct%3A' + username.replace('@', '%40')))
    try:
        user_link = ''
        if 'aliases' in user_meta.keys():
            # If the server provides aliases
            user_link = user_meta['aliases'][0]
        elif 'links' in user_meta.keys():
            # Otherwise, read `links`
            for link in user_meta['links']:
                if link['rel'] == 'self' or link['rel'] == 'http://webfinger.net/rel/profile-page':
                    user_link = link['href']
        else:
            raise exceptions.InvalidUsage('Unsupported platform', status_code=400)
        if user_link:
            logger.info('Adding to cache: [ %s: %s ], redirecting...' % (username, user_link))
            CACHE[username] = user_link
            return response.redirect(user_link)
        else:
            raise exceptions.ServerError('I don\'t really know what\'s going on...', status_code=500)
    except Exception:
        raise exceptions.InvalidUsage('Unknown error, probably the user doesn\'t exist.', status_code=500)


if __name__ == '__main__':
    server = app.create_server(host=HOST, port=PORT)  # Because it uses the same event loop with aiohttp
    # Start the server
    try:
        LOOP.run_until_complete(server)
        LOOP.run_forever()
    except Exception as e:
        LOOP.stop()
        raise RuntimeError(e)  # Stop IDEA from blaming me x2.
