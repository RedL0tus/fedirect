#!/usr/bin/env python3
#-*- encoding: UTF-8 -*-

import json
import urllib3
import xmltodict
import collections

from http.server import BaseHTTPRequestHandler,HTTPServer

HOSTNAME = 'localhost'
PORT = 9090

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print("Received request at:" + self.path)
        splitted_path = self.path.split("/")
        for i in splitted_path:
            if '@' in i:
                try:
                    link = get_link(i)
                except Exception:
                    break
                print("Redirecting to: " + link)
                self.send_response(302)
                self.send_header('Location', link)
                self.send_header('Content-type','text/html')
                self.end_headers()
                self.wfile.write('<!DOCTYPE html><html><head>\
                <title>302 Found</title>\
                </head><body bgcolor="white">\
                <center><h1>302 Found</h1></center>\
                <hr><center>Salted Fish</center>\
                </body></html>'.encode('UTF-8'))
                break
        print("Invalid request")
        self.send_response(500)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write('<!DOCTYPE html><html><head>\
        <title>500 Invalid Request</title>\
        </head><body bgcolor="white">\
        <center><h1>500 Invalid Request</h1>\
        </center><hr><center>Salted Fish</center>\
        </body></html>'.encode('UTF-8'))
            

def start_server():
    try:
        print("Server started...")
        server = HTTPServer((HOSTNAME, PORT), RequestHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("Keyboard Interrupt")
        exit(1)

def get_link(username):
    username_splitted = username.split('@')
    if len(username_splitted) != 2:
        raise ValueError('Invalid username')
    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED')
    host_meta = xmltodict.parse(http.request('GET', 'https://' + username_splitted[1] + '/.well-known/host-meta').data)
    host_link = host_meta['XRD']['Link']
    if type(host_link) == list:
        for i in host_link:
            if '@template' in i:
                if "webfinger?resource={uri}" in i['@template']:
                    host_link = i['@template']
                    break
    elif type(host_link) == collections.OrderedDict:
        if '@template' in host_link:
            if "webfinger?resource={uri}" in host_link['@template']:
                host_link = host_link['@template']
    else:
        raise ValueError('Unsupported platform')
    user_meta = json.loads(http.request('GET', host_link.replace('{uri}', 'acct%3A' + username).replace('@', '%40')).data.decode("UTF-8"))
    return(user_meta['aliases'][0])


if __name__ == '__main__':
    start_server()