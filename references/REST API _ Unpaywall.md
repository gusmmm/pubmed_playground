REST API
Overview

The REST API gives anyone free, programmatic access to the Unpaywall database.

If you're using the API, we recommend you subscribe to the mailing list in order to stay up-to-date when there are changes or new features.
Schema

The API response uses the same shared schema as the database snapshot and Data Feed.
Authentication

Requests must include your email as a parameter at the end of the URL, like this: api.unpaywall.org/my/request?email=YOUR_EMAIL.
Rate limits

Please limit use to 100,000 calls per day. If you need faster access, you'll be better served by downloading the entire database snapshot for local access.
Versions

The current version of the API is Version 2, and this is the only version supported. Version updates are announced on the mailing list.
Alternatives

Depending on your use case, there are often easier ways to access the data than using the API. You can learn more about these in our brief Get Stated pages:

    Get started: Library
    Get started: Enterprise
    Get started: Research

Endpoints
GET /v2/:doi
Description 	Gets OA status and bibliographic info for an given DOI-assigned resource.
Accepts 	A valid DOI.
Returns 	DOI Object
Example 	https://api.unpaywall.org/v2/10.1038/nature12373?email=YOUR_EMAIL
GET /v2/search?query=:your_query[&is_oa=boolean][&page=integer]

Usage notes and additional examples are available in the Unpaywall FAQ.

This endpoint can be accessed through our Article Search tool.
Description 	Provides the full GET /v2/:doi responses for articles whose titles match your query. 50 results are returned per request and the page argument requests pages after the first.
Accepts

    query: The text to search for. Search terms are separated by whitespace and are AND-ed together by default. The title must contain all search terms to be matched. This behavior can be modified by:
        "quoted text" : words inside quotation marks must appear as a phrase to match
        OR : replaces the default AND between words, making a match on either word
        - : negation, only titles not containing this term will match
    is_oa: (Optional) A boolean value indicating whether the returned records should be Open Access or not.
        true: filter the results to OA articles
        false: filter the results to non-OA articles
        null/unspecified: return the most relevant results regardless of OA status
    page: (Optional) An integer indicating which page of results should be returned.
        1/unspecified: return results 1 to 50
        2: return results 51 to 100
        etc.

Returns 	An array of results sorted by the strength of the query match. Each result consists of:

    response: the full DOI Object for this match
    score: the numeric score used to rank the results
    snippet: An HTML-formatted string showing how the title matched the query. For example:

    "Single-<b>cell</b> photoacoustic <b>thermometry</b>"

Example 	https://api.unpaywall.org/v2/search?query=cell%20thermometry&is_oa=true&email=YOUR_EMAIL
