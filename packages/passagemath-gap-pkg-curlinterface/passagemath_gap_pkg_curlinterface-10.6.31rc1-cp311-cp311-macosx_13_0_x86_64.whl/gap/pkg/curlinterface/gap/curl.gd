#
# curlInterface: Simple Web Access
#
#! @Chapter Overview
#!
#! CurlInterface allows a user to interact with http and https
#! servers on the internet, using the 'curl' library.
#! Pages can be downloaded from a URL, and http POST requests
#! can be sent to the URL for processing.

#! @Section Installing curlInterface
#!
#! curlInterface requires the 'curl' library, available from
#! <URL>https://curl.haxx.se/</URL>. Instructions for building
#! and installing curl can be found at
#! <URL>https://curl.haxx.se/docs/install.html</URL>, however
#! in most systems curl can be installed from your OS's package
#! manager.
#!
#! @Subsection Linux
#!
#! <List>
#! <Item>
#! On Debian and Ubuntu, call: <C>apt-get install libcurl4-gnutls-dev</C></Item>
#! <Item>
#! On Redhat and derivatives, call: <C>yum install curl-devel</C></Item>
#! </List>
#!
#! @Subsection Cygwin
#!
#! Install <C>libcurl-devel</C> from the cygwin package manager
#!
#! @Subsection macOS
#!
#! curl is installed by default on Macs, but libcurl may be required.
#! <List>
#! <Item>Homebrew: <C>brew install curl</C></Item>
#! <Item>Fink: <C>fink install libcurl4</C></Item>
#! <Item>MacPorts: <C>port install curl</C></Item>
#! </List>

#! @Section Functions
#!
#! curlInterface currently provides the following functions for interacting with
#! URLs:

#! @Arguments URL[, opts]
#! @Returns
#!   a record
#! @Description
#!   Downloads a URL from the internet.  <A>URL</A> should be a string
#!   describing the address, and should start with either "http://" or
#!   "https://".
#!   For descriptions of the output and the additional argument <A>opts</A>, see
#!   <Ref Func="CurlRequest"/>.
#!
#! @BeginExample
#! gap> r := DownloadURL("www.gap-system.org");;
#! gap> r.success;
#! true
#! gap> r.result{[1..50]};
#! "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n\n<!DOCTYPE "
#! @EndExample
DeclareGlobalFunction("DownloadURL");

#! @Arguments URL, str[, opts]
#! @Returns
#!   a record
#! @Description
#!   Sends an HTTP POST request to a URL on the internet. <A>URL</A> should be a
#!   string describing the address, and should start with either "http://" or
#!   "https://".  <A>str</A> should be the string which will be sent to the
#!   server as a POST request.
#!   For descriptions of the output and the additional argument <A>opts</A>, see
#!   <Ref Func="CurlRequest"/>.
#!
#! @BeginExample
#! gap> r := PostToURL("httpbun.com/post", "animal=tiger");;
#! gap> r.success;
#! true
#! gap> r.result{[51..100]};
#! "\"form\": {\n    \"animal\": \"tiger\"\n  }, \n  \"headers\":"
#! @EndExample
DeclareGlobalFunction("PostToURL");

#! @Arguments URL[, opts]
#! @Returns
#!   a record
#! @Description
#!   Attempts to delete a file on the internet, by sending an HTTP DELETE
#!   request to the given URL.  <A>URL</A> should be a string describing the
#!   address to be deleted, and should start with either "http://" or
#!   "https://".
#!   For descriptions of the output and the additional argument <A>opts</A>, see
#!   <Ref Func="CurlRequest"/>.
#!
#! @BeginExample
#! gap> r := DeleteURL("www.google.com");;
#! gap> r.success;
#! true
#! gap> r.result{[1471..1540]};
#! "<p>The request method <code>DELETE</code> is inappropriate for the URL"
#! @EndExample
DeclareGlobalFunction("DeleteURL");

#! @Arguments URL, type, out_string[, opts]
#! @Returns
#!   a record
#! @Description
#!   Sends an HTTP request of type <A>type</A> to a URL on the internet.
#!   <A>URL</A>, <A>type</A>, and <A>out_string</A> should all be strings:
#!   <A>URL</A> is the URL of the server (which should start with "http://" or
#!   "https://"), <A>type</A> is the type of HTTP request (e.g. "GET"), and
#!   <A>out_string</A> is the message, if any, to send to the server (in
#!   requests such as GET this will be ignored).
#!
#!   An optional fourth argument <A>opts</A> may be included, which should be a
#!   record specifying additional options for the request.  The following
#!   options are supported:
#!     * <C>verifyCert</C>: a boolean describing whether to verify HTTPS
#!       certificates
#!       (corresponds to the curl options <C>CURLOPT_SSL_VERIFYPEER</C>
#!       and <C>CURLOPT_SSL_VERIFYHOST</C>,
#!       the default is <K>true</K> for both);
#!     * <C>verbose</C>: a boolean describing whether to print extra information
#!       to the screen
#!       (corresponds to the curl option <C>CURLOPT_VERBOSE</C>,
#!       the default is <K>false</K>);
#!     * <C>followRedirect</C>: a boolean describing whether to follow
#!       redirection to another URL
#!       (corresponds to the curl option <C>CURLOPT_FOLLOWLOCATION</C>,
#!       the default is <K>true</K>);
#!     * <C>failOnError</C>: a boolean describing whether to regard
#!       404 (and other 4xx) status codes as error
#!       (corresponds to the curl option <C>CURLOPT_FAILONERROR</C>,
#!       the default is <K>false</K>).
#!     * <C>maxTime</C>: Maximum time in seconds that you allow each transfer
#!       to take. 0 means no limitation. (default <K>0</K>).
#!
#!   As output, this function returns a record containing some of the following
#!   components, which describe the outcome of the request:
#!     * <C>success</C>: a boolean describing whether the request was
#!       successfully received by the server;
#!     * <C>result</C>: body of the information sent by the server (only if
#!       <C>success = true</C>);
#!     * <C>error</C>: human-readable string saying what went wrong (only if
#!       <C>success = false</C>).
#!
#!   Most of the standard HTTP request types should work, but currently only
#!   body information is returned.  To see headers, consider using the
#!   <C>verbose</C> option.  For convenience, dedicated functions exist for the
#!   following request types:
#!     * <Ref Func="DownloadURL"/> for GET requests;
#!     * <Ref Func="PostToURL"/> for POST requests;
#!     * <Ref Func="DeleteURL"/> for DELETE requests.
#!
#! @BeginExample
#! gap> r := CurlRequest("https://www.google.com",
#! >                     "HEAD",
#! >                     "",
#! >                     rec(verifyCert := false));
#! rec( result := "", success := true )
#! gap> r := CurlRequest("httpbun.com/post", "POST", "animal=tiger");;
#! gap> r.success;
#! true
#! gap> r.result{[51..100]};
#! "\"form\": {\n    \"animal\": \"tiger\"\n  }, \n  \"headers\":"
#! @EndExample
DeclareGlobalFunction("CurlRequest");
