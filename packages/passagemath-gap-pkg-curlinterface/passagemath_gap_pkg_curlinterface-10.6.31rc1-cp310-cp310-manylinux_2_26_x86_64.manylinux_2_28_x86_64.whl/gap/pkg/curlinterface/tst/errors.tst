#
# test error handling
#

# URL too long (Download)
gap> badURL := ListWithIdenticalEntries(4096,' ');;
gap> DownloadURL(badURL);
Error, CURL_REQUEST: <URL> must be less than 4096 chars

# URL too long (Post)
gap> badURL := ListWithIdenticalEntries(4096,' ');;
gap> PostToURL(badURL, "hello");
Error, CURL_REQUEST: <URL> must be less than 4096 chars

# URL not a string (Download)
gap> DownloadURL(42);
Error, CurlRequest: <URL> must be a string

# URL not a string (Post)
gap> PostToURL(42, "hello");
Error, CurlRequest: <URL> must be a string

# request type not a string
gap> CurlRequest("www.google.com", 637, "hello", rec(verifyCert := true));
Error, CurlRequest: <type> must be a string

# post_string not a string
gap> PostToURL("httpbun.com/post", 17);
Error, CurlRequest: <out_string> must be a string

# invalid verifyCert
gap> DownloadURL("https://www.google.com", rec(verifyCert := "maybe"));
Error, CurlRequest: <opts>.verifyCert must be true or false

# invalid verbose
gap> DownloadURL("https://www.google.com", rec(verbose := "yes"));
Error, CurlRequest: <opts>.verbose must be true or false

# invalid followRedirect
gap> DownloadURL("https://www.google.com", rec(followRedirect := "always"));
Error, CurlRequest: <opts>.followRedirect must be true or false

# invalid failOnError
gap> DownloadURL("https://www.google.com", rec(failOnError := "yes"));
Error, CurlRequest: <opts>.failOnError must be true or false

# invalid opts
gap> DownloadURL("https://www.google.com", "please verify the cert");
Error, CurlRequest: <opts> must be a record

# too many arguments
gap> CurlRequest("www.google.com", "GET", "", rec(verifyCert := true), 3, true);
Error, CurlRequest: usage: requires 3 or 4 arguments, but 6 were given

# invalid time
gap> CurlRequest("www.google.com", "GET", "", rec(maxTime := -1));
Error, CurlRequest: <opts>.maxTime must be a non-negative integer

# invalid time
gap> CurlRequest("www.google.com", "GET", "", rec(maxTime := "abc"));
Error, CurlRequest: <opts>.maxTime must be a non-negative integer

# number of arguments
gap> CURL_REQUEST();
Error, Function: number of arguments must be 8 (not 0)
