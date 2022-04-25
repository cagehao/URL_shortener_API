# URL_shortener_API
> Using Flask, MongoDB and python build a backend URL shortener API
# Basic Function:
(1)Given any URL input via POST to localhost/urlshorten with set body form-data :
+ KEY=url and VALUE = https://a.very-long.url/need_to_be_shorten_532sdwasdfads1 (the URL)
 API can return a JSON with the following properties:

+  original - The input URL.
+  short - The shortened URL. Path should contain 6 alphanumeric characters. e.g. /aKCb2g
+  count - This is the number of times the same given URL has been sent to your API for shortening regardless of which client sent it.

 all shortened URLs are globally unique; 
 + for example: https://a.very-long.url/foo?lorem=ipsum should Always return the same shortened URL.
 There can never be more than 1 record of the same shortened URL in the database. (Can be validate by function (2)).
 If shortened an URL to be https://foo.bar/aKCb2g, then there cannot be another record of aKCb2g in the db.

 (2)Validate if there is any duplicate shortened urls in the db.
 + Using GET to localhost/validate, 
 The API can return a dictionary of duplicate shortened urls, the key is shortened url the value is the number of that same urls in the database
 
(3)update the original url base using the shortened url
 Using PATCH to localhost/update with with set body form-data:
 + KEY: short_url     VALUE: https://foo.bar/3a0005 (the url you want to update its original url)
 + KEY: original_url  VALUE: https://google1.com232 (the updated original url)

(4)backup and delete the url data using the shortened url
  Using PATCH to <the address>/update with with set body form-data:
  + KEY: short_url     VALUE: https://foo.bar/3a0005 (the url you want to delete)
