Quotes
======

Returns 10 famous quotes each time the page is refreshed. Quotes are obtained
by sending concurrent HTTP requests to a Quotes API with the requests client.

This example shows how you can incorporate blocking code into your aioflask
application without blocking the asyncio loop. 

To run this example, set `FLASK_APP=quotes.py` in your environment and then use
the standard `flask aiorun` command to start the server.
