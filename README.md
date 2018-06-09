Fedirect
==========

Fediverse + redirect = Fedirect

Find user page by username.

e.g. https://brined.fish/link/KayMW@brined.fish will 302 redirect to https://s.brined.fish/@KayMW

Tested on Mastodon and GNU Social.

Special thanks to [niconiconi@cybre.space](https://brined.fish/link/niconiconi@cybre.space)( @biergaizi ) for naming the repo.


Deploy
------

Clone the reposistory, install the dependencies, and run `main.py`.  
Don't forget to use a web server to reverse proxy it.

How does it work
----------------

1. Split username into two parts (username and host).
2. Fetch and parse host's `.well-known/host-meta`, get the link to host's webfinger.
3. Fetch user's page by accessing webfinger.
