This is a tutorial and guide on how to build a good clinical query for pubmed.
First ask the user for the query in natural language: what do you want to find?

# keep the query simple
- no punctuation 
- no tags
- use specific search topic
- do not use articles, pronouns, adverbs... just nouns and adjectives.
- keep the nouns and adjectives in the singular unless absolutely necessary to make sense
- enclose the the query in ()
Example: searching for articles on the relation between the type if gut biome and allergies the query will be "(gut biome allergy)"

If it is a clinical query, use the PubMed Clinical Queries. How to do it? For example, the user puts the query “severe malaria”, you have to decide or ask if the query is about one of these topics:

- Therapy
- Clinical Prediction Guides
- Diagnosis
- Etiology
- Prognosis

If in doubt, ask the user if it is a clinical query, and if affirmative, to which topics it relates to.
Then you have to select 1 of 2 types of filters:

- Broad
- Narrow

The broad filter gets more results (more sensitivity in the search), but less specific results that might not be relevant to the topic. Narrow is the other way around - less results, probably more relevant to the topic.  

So add to the query the combination of the topic and the filter in this way:
- Therapy, narrow - add “AND (Therapy/Narrow[filter])”; therapy, broad add “AND (Therapy/Broad[filter])”
- Diagnosis, narrow - add  “AND (Diagnosis/Narrow[filter])”; Diagnosis, broad - add “AND (Diagnosis/Broad[filter])”
- Clinical Prediction Guides, narrow - add “AND (Clinical Prediction Guides/Narrow[filter])”; Clinical Prediction Guides, broad - add “AND (Clinical Prediction Guides/Broad[filter])”
- Etiology, narrow - add “AND (Etiology/Narrow[filter])”; etiology, broad - add “AND (Etiology/Narrow[filter])”
- Prognosis, narrow - add “AND (Prognosis/Narrow[filter])” ; prognosis, broad - add “AND (Prognosis/Broad[filter])”


# Filters
## Adults vs aged vs children
If in doubt, ask the user if the query relates to adults, aged over 65 yo or children under 18 yo.
- If it is related to adults, add “AND (alladult[Filter])” to the query.
- If it is related to aged over 65 yo add “AND "adult"[MeSH Terms]) AND (aged[Filter])” to the query.
- If it is related to children under 18 yo add “(allchild[Filter])“ to the query.
- If it is 2 or more groups - for example children and adults - add “AND(alladult[Filter] OR allchild[Filter])” to the query

## When the papers were published
If in doubt, ask the user if he wants papers published in the last year, 5 years, 10 years, or for a custom range. Default is without filter - search for published any time.  Add to the query, depending on:
- In the last year - add “AND (y_1[Filter])“ 
- In the last 5 years - add “AND (y_5[Filter])” 
- In the last 10 years - add “AND (y_10[Filter])”
- Custom range, example from 2005 to 2010 - add “AND (2000:2005[pdat])”
 
## Text availability
Default is without a filter. If not stated ask the user if he wants all results or just the ones with:
- Full text - add “AND (fft[Filter])” to the query
- Free full text - add “AND ((ffrft[Filter])” to the query
- Abstract - add “AND (fha[Filter])” to the query

## Article type
Default is without a filter, if the user wants all types of papers. The user might be interested in just certain types of articles, so ask which type, and add the filter to the query:
- Clinical trial - add “AND (clinicaltrial[Filter])”
- Meta-analysis - add “AND (meta-analysis[Filter])”
- Randomized controlled trial or RCT - add “AND (randomizedcontrolledtrial[Filter])”
- Review - add “AND (review[Filter])”
- Systematic review - add “AND (systematicreview[Filter])”

# Humans only
Add “AND (humans[Filter])” to the query

# Just females
Add "AND (female[Filter])" to the query

# Just males
add "AND (male[Filter])" to the query