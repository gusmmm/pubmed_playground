Google Search Engine Results API
API uptime
99.982%

/search API endpoint allows you to scrape the results from Google search engine via our SerpApi service. Head to the playground for a live and interactive demo. You can query https://serpapi.com/search using a GET request.
API Parameters
Search Query

q

Required

Parameter defines the query you want to search. You can use anything that you would use in a regular Google search. e.g. inurl:, site:, intitle:. We also support advanced search query parameters such as as_dt and as_eq. See the full list of supported advanced search query parameters.
Geographic Location

location

Optional

Parameter defines from where you want the search to originate. If several locations match the location requested, we'll pick the most popular one. Head to the /locations.json API if you need more precise control. The location and uule parameters can't be used together. It is recommended to specify location at the city level in order to simulate a real user’s search. If location is omitted, the search may take on the location of the proxy.

uule

Optional

Parameter is the Google encoded location you want to use for the search. uule and location parameters can't be used together.
Advanced Google Parameters

ludocid

Optional

Parameter defines the id (CID) of the Google My Business listing you want to scrape. Also known as Google Place ID.

lsig

Optional

Parameter that you might have to use to force the knowledge graph map view to show up. You can find the lsig ID by using our Local Pack API or Google Local API.
lsig ID is also available via a redirect Google uses within Google My Business.

kgmid

Optional

Parameter defines the id (KGMID) of the Google Knowledge Graph listing you want to scrape. Also known as Google Knowledge Graph ID. Searches with kgmid parameter will return results for the originally encrypted search parameters. For some searches, kgmid may override all other parameters except start, and num parameters.

si

Optional

Parameter defines the cached search parameters of the Google Search you want to scrape. Searches with si parameter will return results for the originally encrypted search parameters. For some searches, si may override all other parameters except start, and num parameters. si can be used to scrape Google Knowledge Graph Tabs.

ibp

Optional

Parameter is responsible for rendering layouts and expansions for some elements (e.g., gwp;0,7 to expand searches with ludocid for expanded knowledge graph).

uds

Optional

Parameter enables to filter search. It's a string provided by Google as a filter. uds values are provided under the section: filters with uds, q and serpapi_link values provided for each filter.
Localization

google_domain

Optional

Parameter defines the Google domain to use. It defaults to google.com. Head to the Google domains page for a full list of supported Google domains.

gl

Optional

Parameter defines the country to use for the Google search. It's a two-letter country code. (e.g., us for the United States, uk for United Kingdom, or fr for France). Head to the Google countries page for a full list of supported Google countries.

hl

Optional

Parameter defines the language to use for the Google search. It's a two-letter language code. (e.g., en for English, es for Spanish, or fr for French). Head to the Google languages page for a full list of supported Google languages.

cr

Optional

Parameter defines one or multiple countries to limit the search to. It uses country{two-letter upper-case country code} to specify countries and | as a delimiter. (e.g., countryFR|countryDE will only search French and German pages). Head to the Google cr countries page for a full list of supported countries.

lr

Optional

Parameter defines one or multiple languages to limit the search to. It uses lang_{two-letter language code} to specify languages and | as a delimiter. (e.g., lang_fr|lang_de will only search French and German pages). Head to the Google lr languages page for a full list of supported languages.
Advanced Filters

tbs

Optional

(to be searched) parameter defines advanced search parameters that aren't possible in the regular query field. (e.g., advanced search for patents, dates, news, videos, images, apps, or text contents).

safe

Optional

Parameter defines the level of filtering for adult content. It can be set to active or off, by default Google will blur explicit content.

nfpr

Optional

Parameter defines the exclusion of results from an auto-corrected query when the original query is spelled wrong. It can be set to 1 to exclude these results, or 0 to include them (default). Note that this parameter may not prevent Google from returning results for an auto-corrected query if no other results are available.

filter

Optional

Parameter defines if the filters for 'Similar Results' and 'Omitted Results' are on or off. It can be set to 1 (default) to enable these filters, or 0 to disable these filters.
Search Type

tbm

Optional

(to be matched) parameter defines the type of search you want to do.

It can be set to:
(no tbm parameter): regular Google Search,
isch: Google Images API,
lcl - Google Local API
vid: Google Videos API,
nws: Google News API,
shop: Google Shopping API,
pts: Google Patents API,
or any other Google service.
Pagination

start

Optional

Parameter defines the result offset. It skips the given number of results. It's used for pagination. (e.g., 0 (default) is the first page of results, 10 is the 2nd page of results, 20 is the 3rd page of results, etc.).

Google Local Results only accepts multiples of 20(e.g. 20 for the second page results, 40 for the third page results, etc.) as the start value.

num

Optional

Parameter defines the maximum number of results to return. (e.g., 10 (default) returns 10 results, 40 returns 40 results, and 100 returns 100 results).

The use of num may introduce latency, and/or prevent the inclusion of specialized result types. It is better to omit this parameter unless it is strictly necessary to increase the number of results per page.

Results are not guaranteed to have the number of results specified in num.
Serpapi Parameters

engine

Optional

Set parameter to google (default) to use the Google API engine.

device

Optional

Parameter defines the device to use to get the results. It can be set to desktop (default) to use a regular browser, tablet to use a tablet browser (currently using iPads), or mobile to use a mobile browser (currently using iPhones).

no_cache

Optional

Parameter will force SerpApi to fetch the Google results even if a cached version is already present. A cache is served only if the query and all parameters are exactly the same. Cache expires after 1h. Cached searches are free, and are not counted towards your searches per month. It can be set to false (default) to allow results from the cache, or true to disallow results from the cache. no_cache and async parameters should not be used together.

async

Optional

Parameter defines the way you want to submit your search to SerpApi. It can be set to false (default) to open an HTTP connection and keep it open until you got your search results, or true to just submit your search to SerpApi and retrieve them later. In this case, you'll need to use our Searches Archive API to retrieve your results. async and no_cache parameters should not be used together. async should not be used on accounts with Ludicrous Speed enabled.

zero_trace

Optional

Enterprise only. Parameter enables ZeroTrace mode. It can be set to false (default) or true. Enable this mode to skip storing search parameters, search files, and search metadata on our servers. This may make debugging more difficult.

api_key

Required

Parameter defines the SerpApi private key to use.

output

Optional

Parameter defines the final output you want. It can be set to json (default) to get a structured JSON of the results, or html to get the raw html retrieved.
Note on Search Queries using the parameter num

Due to Google's new Knowledge Graph layout, Google is ignoring the num parameter for the first page of results in many searches related to celebrities, famous groups, and popular media.

When start parameter is used and set to 1 or higher, the num parameter works as expected.

Until Google resolves this issue, if necessary, you may set start to 1 in order to get the parameter num to work normally.

However, the first Organic Results item and the Knowledge Graph will not be returned when using this approach.
API Results
JSON Results

JSON output includes structured data for organic results, local results, ad results, the knowledge graph, direct answer boxes, images results, news results, shopping results, video results, and more.

A search status is accessible through search_metadata.status. It flows this way: Processing -> Success || Error. If a search has failed, error will contain an error message. search_metadata.id is the search ID inside SerpApi.
HTML Results

HTML output is useful to debug JSON results or support features not supported yet by SerpApi.
HTML output gives you the raw HTML results from Google.

---------------------------------------------------------------------

# Google Scholar API
API uptime
99.957%

Our Google Scholar API allows you to scrape SERP results from a Google Scholar search query. The API is accessed through the following endpoint: /search?engine=google_scholar.

A user may query the following: https://serpapi.com/search?engine=google_scholar utilizing a GET request. Head to the playground for a live and interactive demo.
API Parameters
Search Query

q

Required

Parameter defines the query you want to search. You can also use helpers in your query such as: author:, or source:.

Usage of cites parameter makes q optional. Usage of cites together with q triggers search within citing articles.

Usage of cluster together with q and cites parameters is prohibited. Use cluster parameter only.
Advanced Google Scholar Parameters

cites

Optional

Parameter defines unique ID for an article to trigger Cited By searches. Usage of cites will bring up a list of citing documents in Google Scholar. Example value: cites=1275980731835430123. Usage of cites and q parameters triggers search within citing articles.

as_ylo

Optional

Parameter defines the year from which you want the results to be included. (e.g. if you set as_ylo parameter to the year 2018, the results before that year will be omitted.). This parameter can be combined with the as_yhi parameter.

as_yhi

Optional

Parameter defines the year until which you want the results to be included. (e.g. if you set as_yhi parameter to the year 2018, the results after that year will be omitted.). This parameter can be combined with the as_ylo parameter.

scisbd

Optional

Parameter defines articles added in the last year, sorted by date. It can be set to 1 to include only abstracts, or 2 to include everything. The default value is 0 which means that the articles are sorted by relevance.

cluster

Optional

Parameter defines unique ID for an article to trigger All Versions searches. Example value: cluster=1275980731835430123. Usage of cluster together with q and cites parameters is prohibited. Use cluster parameter only.
Localization

hl

Optional

Parameter defines the language to use for the Google Scholar search. It's a two-letter language code. (e.g., en for English, es for Spanish, or fr for French). Head to the Google languages page for a full list of supported Google languages.

lr

Optional

Parameter defines one or multiple languages to limit the search to. It uses lang_{two-letter language code} to specify languages and | as a delimiter. (e.g., lang_fr|lang_de will only search French and German pages). Head to the Google lr languages for a full list of supported languages.
Pagination

start

Optional

Parameter defines the result offset. It skips the given number of results. It's used for pagination. (e.g., 0 (default) is the first page of results, 10 is the 2nd page of results, 20 is the 3rd page of results, etc.).

num

Optional

Parameter defines the maximum number of results to return, ranging from 1 to 20, with a default of 10.
Search Type

as_sdt

Optional

Parameter can be used either as a search type or a filter.

As a Filter (only works when searching articles):
0 - exclude patents (default).
7 - include patents.

As a Search Type:
4 - Select case law (US courts only). This will select all the State and Federal courts.
e.g. as_sdt=4 - Selects case law (all courts)

To select specific courts, see the full list of supported Google Scholar courts.
e.g. as_sdt=4,33,192 - 4 is the required value and should always be in the first position, 33 selects all New York courts and 192 selects Tax Court.
Values have to be separated by comma (,)
Advanced Filters

safe

Optional

Parameter defines the level of filtering for adult content. It can be set to active or off, by default Google will blur explicit content.

filter

Optional

Parameter defines if the filters for 'Similar Results' and 'Omitted Results' are on or off. It can be set to 1 (default) to enable these filters, or 0 to disable these filters.

as_vis

Optional

Parameter defines whether you would like to include citations or not. It can be set to 1 to exclude these results, or 0 (default) to include them.

as_rr

Optional

Parameter defines whether you would like to show only review articles or not (these articles consist of topic reviews, or discuss the works or authors you have searched for). It can be set to 1 to enable this filter, or 0 (default) to show all results.
Serpapi Parameters

engine

Required

Set parameter to google_scholar to use the Google Scholar API engine.

no_cache

Optional

Parameter will force SerpApi to fetch the Google Scholar results even if a cached version is already present. A cache is served only if the query and all parameters are exactly the same. Cache expires after 1h. Cached searches are free, and are not counted towards your searches per month. It can be set to false (default) to allow results from the cache, or true to disallow results from the cache. no_cache and async parameters should not be used together.

async

Optional

Parameter defines the way you want to submit your search to SerpApi. It can be set to false (default) to open an HTTP connection and keep it open until you got your search results, or true to just submit your search to SerpApi and retrieve them later. In this case, you'll need to use our Searches Archive API to retrieve your results. async and no_cache parameters should not be used together. async should not be used on accounts with Ludicrous Speed enabled.

zero_trace

Optional

Enterprise only. Parameter enables ZeroTrace mode. It can be set to false (default) or true. Enable this mode to skip storing search parameters, search files, and search metadata on our servers. This may make debugging more difficult.

api_key

Required

Parameter defines the SerpApi private key to use.

output

Optional

Parameter defines the final output you want. It can be set to json (default) to get a structured JSON of the results, or html to get the raw html retrieved.
API Results
JSON Results

JSON output includes structured data for organic results.

A search status is accessible through search_metadata.status. It flows this way: Processing -> Success || Error. If a search has failed, error will contain an error message. search_metadata.id is the search ID inside SerpApi.
HTML Results

HTML output is useful to debug JSON results or support features not supported yet by SerpApi.
HTML output gives you the raw HTML results from Google.

------------------------------------------------
# Google News API
API uptime
99.999%

Our Google News API allows you to scrape results from the Google News search page. The API is accessed through the following endpoint: /search?engine=google_news.

A user may query the following: https://serpapi.com/search?engine=google_news utilizing a GET request. Head to the playground for a live and interactive demo.
API Parameters
Search Query

q

Optional

Parameter defines the query you want to search. You can use anything that you would use in a regular Google News search. e.g. site:, when:.

Parameter can't be used together with publication_token, story_token, and topic_token parameters.
Localization

gl

Optional

Parameter defines the country to use for the Google News search. It's a two-letter country code. (e.g., us for the United States (default), uk for United Kingdom, or fr for France). Head to the Google countries page for a full list of supported Google News countries.

hl

Optional

Parameter defines the language to use for the Google News search. It's a two-letter language code. (e.g., en for English, es for Spanish, or fr for French). Head to the Google languages page for a full list of supported Google languages.
Advanced Google News Parameters

topic_token

Optional

Parameter defines the Google News topic token. It is used for accessing the news results for a specific topic (e.g., "World", "Business", "Technology").

The token can be found in our JSON response or the URL of the Google News page (in the URL, it is a string of characters preceded by /topics/).

Parameter can't be used together with q, story_token, and publication_token parameters.

publication_token

Optional

Parameter defines the Google News publication token. It is used for accessing the news results from a specific publisher (e.g., "CNN", "BBC", "The Guardian").

The token can be found in our JSON response or the URL of the Google News page (in the URL, it is a string of characters preceded by /publications/).

Parameter can't be used together with q, story_token, and topic_token parameters.

section_token

Optional

Parameter defines the Google News section token. It is used for accessing the sub-section of a specific topic. (e.g., "Business -> Economy").

The token can be found in our JSON response or the URL of the Google News page (in the URL, it is a string of characters preceded by /sections/)

Parameter can only be used in combination with topic_token or publication_token parameters.

story_token

Optional

Parameter defines the Google News story token. It is used for accessing the news results with full coverage of a specific story.

The token can be found in our JSON response or the URL of the Google News page (in the URL, it is a string of characters preceded by /stories/)

Parameter can't be used together with q, topic_token, and publication_token parameters.

so

Optional

Parameter defines the sorting method. Results can be sorted by relevance or by date. By default, the results are sorted by relevance.
List of supported values are:

0 - Relevance
1 - Date

Parameter can only be used in combination with story_token parameter.
Serpapi Parameters

engine

Required

Set parameter to google_news to use the Google News API engine.

no_cache

Optional

Parameter will force SerpApi to fetch the Google News results even if a cached version is already present. A cache is served only if the query and all parameters are exactly the same. Cache expires after 1h. Cached searches are free, and are not counted towards your searches per month. It can be set to false (default) to allow results from the cache, or true to disallow results from the cache. no_cache and async parameters should not be used together.

async

Optional

Parameter defines the way you want to submit your search to SerpApi. It can be set to false (default) to open an HTTP connection and keep it open until you got your search results, or true to just submit your search to SerpApi and retrieve them later. In this case, you'll need to use our Searches Archive API to retrieve your results. async and no_cache parameters should not be used together. async should not be used on accounts with Ludicrous Speed enabled.

zero_trace

Optional

Enterprise only. Parameter enables ZeroTrace mode. It can be set to false (default) or true. Enable this mode to skip storing search parameters, search files, and search metadata on our servers. This may make debugging more difficult.

api_key

Required

Parameter defines the SerpApi private key to use.

output

Optional

Parameter defines the final output you want. It can be set to json (default) to get a structured JSON of the results, or html to get the raw html retrieved.
API Results
JSON Results

JSON output includes structured data for News Results.

A search status is accessible through search_metadata.status. It flows this way: Processing -> Success || Error. If a search has failed, error will contain an error message. search_metadata.id is the search ID inside SerpApi.
HTML Results

This API does not have the HTML response, just a text. search_metadata.prettify_html_file contains prettified version of the result. It is displayed in the playground.
