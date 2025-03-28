---
title: "pubget documentation"
source: "https://neuroquery.github.io/pubget/pubget.html#vectorize_corpus_to_npz"
author:
published:
created: 2025-03-23
description:
tags:
  - "clippings"
---
## pubget

![](https://neuroquery.github.io/pubget/pubget.svg)

[![build](https://github.com/neuroquery/pubget/actions/workflows/testing.yml/badge.svg)](https://github.com/neuroquery/pubget/actions/workflows/testing.yml) [![codecov](https://codecov.io/gh/neuroquery/pubget/branch/main/graph/badge.svg?token=8KEBP2EN3A)](https://codecov.io/gh/neuroquery/pubget) [![pubget on GitHub](https://img.shields.io/static/v1?label=&message=pubget%20on%20GitHub&color=black&style=flat&logo=github)](https://github.com/neuroquery/pubget)

**This document describes pubget version 0.0.8**

`pubget` is a command-line tool for collecting data for biomedical text-mining, and in particular large-scale coordinate-based neuroimaging meta-analysis. It exposes some of the machinery that was used to create the [neuroquery dataset](https://github.com/neuroquery/neuroquery_data), which powers [neuroquery.org](https://neuroquery.org/).

`pubget` downloads full-text articles from [PubMed Central](https://www.ncbi.nlm.nih.gov/pmc/) and extracts their text, metadata and stereotactic coordinates. It can also compute [TFIDF features](https://en.wikipedia.org/wiki/Tf%E2%80%93idf) for the extracted text, fit [NeuroQuery](https://neuroquery.org/) or [NeuroSynth](https://neurosynth.org/), and format its output for use with [NiMARE](https://nimare.readthedocs.io/) or [labelbuddy](https://jeromedockes.github.io/labelbuddy/). It can be extended with plugins.

Besides the command-line interface, `pubget`'s functionality is also exposed through its [Python API](https://neuroquery.github.io/pubget/#python-api).


## Python API

`pubget` is mostly intended for use as a command-line tool. However, it is also a Python package and its functionality can be used in Python programs. The Python API closely reflects the command-line programs described above.

The Python API is described on the `pubget` [website](https://neuroquery.github.io/pubget/#python-api).

class Command:@abstractmethod

def edit\_argument\_parser( self, argument\_parser: Union\[argparse.ArgumentParser, argparse.\_ArgumentGroup\]) -> None:

Add arguments needed by this command to parser.

@abstractmethod

def run(self, args: argparse.Namespace) -> [pubget.ExitCode](https://neuroquery.github.io/pubget/#ExitCode):

Execute this command. Return exit code.

class ExitCode(enum.IntEnum):Exit code for a processing step.

COMPLETED = <[ExitCode.COMPLETED](https://neuroquery.github.io/pubget/#ExitCode.COMPLETED): 0>

INCOMPLETE = <[ExitCode.INCOMPLETE](https://neuroquery.github.io/pubget/#ExitCode.INCOMPLETE): 1>

ERROR = <[ExitCode.ERROR](https://neuroquery.github.io/pubget/#ExitCode.ERROR): 2>

##### Inherited Members

enum.Enum

name

value

builtins.int

conjugate

bit\_length

bit\_count

to\_bytes

from\_bytes

as\_integer\_ratio

real

imag

numerator

denominator

class PipelineStep:An individual step in the `pubget` pipeline (`pubget run`).

@abstractmethod

def edit\_argument\_parser( self, argument\_parser: Union\[argparse.ArgumentParser, argparse.\_ArgumentGroup\]) -> None:

Add arguments needed by this step to parser.

@abstractmethod

def run( self, args: argparse.Namespace, previous\_steps\_output: Mapping\[str, pathlib.Path\]) -> Tuple\[Optional\[pathlib.Path\], pubget.\_ExitCode\]:

Execute this step. Return resulting directory and exit code.

def download\_pmcids( pmcids: Sequence\[int\], data\_dir: Union\[os.PathLike, str\], \*, n\_docs: Optional\[int\] \= None, retmax: int \= 500, api\_key: Optional\[str\] \= None) -> Tuple\[pathlib.Path, pubget.\_ExitCode\]:Download articles in a provided list of PMCIDs.

###### Parameters

- **pmcids**: List of PubMed Central IDs to download.
- **data\_dir**: Path to the directory where all pubget data is stored; a subdirectory will be created for this download.
- **n\_docs**: Approximate maximum number of articles to download. By default, all results returned for the search are downloaded. If n\_docs is specified, at most n\_docs rounded up to the nearest multiple of `retmax` articles will be downloaded.
- **retmax**: Batch size -- number of articles that are downloaded per request.
- **api\_key**: API key for the Entrez E-utilities (see [the E-utilities help](https://www.ncbi.nlm.nih.gov/books/NBK25497/)). If the API key is provided, it is included in all requests to the Entrez E-utilities.

###### Returns

- **output\_dir**: The directory that was created in which downloaded data is stored.
- **exit\_code**: COMPLETED if all articles have been successfully downloaded and INCOMPLETE or ERROR otherwise. Used by the `pubget` command-line interface.

def download\_query\_results( query: str, data\_dir: Union\[os.PathLike, str\], \*, n\_docs: Optional\[int\] \= None, retmax: int \= 500, api\_key: Optional\[str\] \= None) -> Tuple\[pathlib.Path, pubget.\_ExitCode\]:Download articles matching a query from PubMedCentral.

###### Parameters

- **query**: Search term for querying the PMC database. You can build the query using the [PMC advanced search interface](https://www.ncbi.nlm.nih.gov/pmc/advanced). For more information see [the E-Utilities help](https://www.ncbi.nlm.nih.gov/books/NBK3837/).
- **data\_dir**: Path to the directory where all pubget data is stored; a subdirectory will be created for this download.
- **n\_docs**: Approximate maximum number of articles to download. By default, all results returned for the search are downloaded. If n\_docs is specified, at most n\_docs rounded up to the nearest multiple of `retmax` articles will be downloaded.
- **retmax**: Batch size -- number of articles that are downloaded per request.
- **api\_key**: API key for the Entrez E-utilities (see [the E-utilities help](https://www.ncbi.nlm.nih.gov/books/NBK25497/)). If the API key is provided, it is included in all requests to the Entrez E-utilities.

###### Returns

- **output\_dir**: The directory that was created in which downloaded data is stored.
- **exit\_code**: COMPLETED if all articles have been successfully downloaded and INCOMPLETE or ERROR otherwise. Used by the `pubget` command-line interface.

def extract\_articles( articlesets\_dir: Union\[os.PathLike, str\], output\_dir: Union\[str, os.PathLike, NoneType\] \= None, n\_jobs: int \= 1) -> Tuple\[pathlib.Path, pubget.\_ExitCode\]:Extract articles from bulk download files.

###### Parameters

- **articlesets\_dir**: Directory containing the downloaded files. It is a directory created by `pubget.download_articles_for_query`: it is named `articlesets` and it contains the bulk download files `articleset_00000.xml`, `articleset_00001.xml`, etc.
- **output\_dir**: Directory where to store the extracted articles. If not specified, a sibling directory of `articlesets_dir` called `articles` will be used.
- **n\_jobs**: Number of processes to run in parallel. `-1` means using all processors.

###### Returns

- **output\_dir**: The directory in which articles are stored. To avoid having a very large number of files in one directory, subdirectories with names ranging from `000` to `fff` are created. Each article is stored in the subdirectory that matches the first hexadecimal digits of the md5 checksum of its PMC id. Therefore the contents of the `articles` directory might look like:

```
· articles
  ├── 001
  │   └── pmcid_4150635
  └── 00b
      ├── pmcid_2568959
      └── pmcid_5102699
```

Each article gets its own subdirectory, containing the article's XML and its tables.

- **exit\_code**: COMPLETED if the download in `articlesets_dir` was complete and the article extraction finished normally and INCOMPLETE otherwise. Used by the `pubget` command-line interface.

def fit\_neuroquery( tfidf\_dir: Union\[os.PathLike, str\], extracted\_data\_dir: Union\[str, os.PathLike, NoneType\] \= None, output\_dir: Union\[str, os.PathLike, NoneType\] \= None, n\_jobs: int \= 1) -> Tuple\[pathlib.Path, pubget.\_ExitCode\]:Fit a NeuroQuery encoder.

###### Parameters

- **vectorized\_dir**: The directory containing the vectorized text (TFIDF features). It is the directory created by `[pubget.vectorize_corpus_to_npz](https://neuroquery.github.io/pubget/#vectorize_corpus_to_npz)` using `extracted_data_dir` as input.
- **extracted\_data\_dir**: The directory containing extracted metadata and coordinates. It is a directory created by `[pubget.extract_data_to_csv](https://neuroquery.github.io/pubget/#extract_data_to_csv)`. If `None`, this function looks for a sibling directory of the `vectorized_dir` whose name ends with `_extractedData`.
- **output\_dir**: Directory in which to store the NeuroQuery model. If not specified, a sibling directory of `vectorized_dir` whose name ends with `_neuroqueryModel` is created. It will contain a `neuroquery_model` subdirectory that can be loaded with `neuroquery.NeuroQueryModel.from_data_dir`

###### Returns

- **output\_dir**: The directory in which the neuroquery model is stored.
- **exit\_code**: COMPLETED if the neuroquery model was fitted and previous steps were complete and INCOMPLETE otherwise. Used by the `pubget` command-line interface.

def fit\_neurosynth( tfidf\_dir: Union\[os.PathLike, str\], extracted\_data\_dir: Union\[str, os.PathLike, NoneType\] \= None, output\_dir: Union\[str, os.PathLike, NoneType\] \= None, n\_jobs: int \= 1) -> Tuple\[pathlib.Path, pubget.\_ExitCode\]:Run a NeuroSyth-style meta-analysis.

(Chi2 test of independence between term occurrence and voxel activation).

###### Parameters

- **vectorized\_dir**: The directory containing the vectorized text (TFIDF features). It is the directory created by `[pubget.vectorize_corpus_to_npz](https://neuroquery.github.io/pubget/#vectorize_corpus_to_npz)` using `extracted_data_dir` as input.
- **extracted\_data\_dir**: The directory containing extracted metadata and coordinates. It is a directory created by `[pubget.extract_data_to_csv](https://neuroquery.github.io/pubget/#extract_data_to_csv)`. If `None`, this function looks for a sibling directory of the `vectorized_dir` whose name ends with `_extractedData`.
- **output\_dir**: Directory in which to store the NeuroSynth maps. If not specified, a sibling directory of `vectorized_dir` whose name ends with `_neurosynthResults` is created. It will contain the images (of Z values) resulting from the analysis.

###### Returns

- **output\_dir**: The directory in which the meta-analysis maps are stored.
- **exit\_code**: COMPLETED if the analysis ran successfully and previous steps were complete and INCOMPLETE otherwise. Used by the `pubget` command-line interface.

def make\_labelbuddy\_documents( extracted\_data\_dir: Union\[os.PathLike, str\], output\_dir: Union\[str, os.PathLike, NoneType\] \= None, batch\_size: Optional\[int\] \= 200) -> Tuple\[pathlib.Path, pubget.\_ExitCode\]:Prepare articles for annotation with labelbuddy.

The documents are prepared in JSONL format, with `batch_size` documents in each `.jsonl` file. They can thus be imported into labelbuddy with, for example: `labelbuddy mydb.labelbuddy --import-docs documents_00001.jsonl`.

See the [labelbuddy documentation](https://jeromedockes.github.io/labelbuddy/) for details.

###### Parameters

- **extracted\_data\_dir**: The directory containing extracted text and metadata. It is a directory created by `[pubget.extract_data_to_csv](https://neuroquery.github.io/pubget/#extract_data_to_csv)`.
- **output\_dir**: Directory in which to store the created data. If not specified, a sibling directory of `extracted_data_dir` whose name ends with `_labelbuddyData` is created.
- **batch\_size**: Number of articles stored in each `.jsonl` file. If `None`, put all articles in one file.

###### Returns

- **output\_dir**: The directory in which the prepared documents are stored.
- **exit\_code**: COMPLETED if previous steps were complete and INCOMPLETE otherwise. Used by the `pubget` command-line interface.

def make\_nimare\_dataset( vectorized\_dir: Union\[os.PathLike, str\], extracted\_data\_dir: Union\[str, os.PathLike, NoneType\] \= None, output\_dir: Union\[str, os.PathLike, NoneType\] \= None) -> Tuple\[Optional\[pathlib.Path\], pubget.\_ExitCode\]:Create a NiMARE JSON dataset from data collected by `pubget`.

See the [NiMARE documentation](https://nimare.readthedocs.io/) for details. This function requires `nimare` to be installed.

###### Parameters

- **vectorized\_dir**: The directory containing the vectorized text (TFIDF features). It is the directory created by `[pubget.vectorize_corpus_to_npz](https://neuroquery.github.io/pubget/#vectorize_corpus_to_npz)` using `extracted_data_dir` as input.
- **extracted\_data\_dir**: The directory containing extracted metadata and coordinates. It is a directory created by `[pubget.extract_data_to_csv](https://neuroquery.github.io/pubget/#extract_data_to_csv)`. If `None`, this function looks for a sibling directory of the `vectorized_dir` whose name ends with `_extractedData`.
- **output\_dir**: Directory in which to store the extracted data. If not specified, a sibling directory of `vectorized_dir` whose name ends with `_nimareDataset` is created.

###### Returns

- **output\_dir**: The directory in which the NiMARE dataset is stored. It contains a `nimare_dataset.json` file.
- **exit\_code**: COMPLETED if previous steps were complete and the NiMARE dataset was created, INCOMPLETE if previous steps were incomplete, ERROR if NiMARE is not installed. Used by the `pubget` command-line interface.

def vectorize\_corpus\_to\_npz( extracted\_data\_dir: Union\[os.PathLike, str\], output\_dir: Union\[str, os.PathLike, NoneType\] \= None, vocabulary: Union\[os.PathLike, str, pubget.\_vectorization.Vocabulary\] \= <Vocabulary.NEUROQUERY\_VOCABULARY: 'https://github.com/neuroquery/neuroquery\_data/blob/main/neuroquery\_model/vocabulary.csv'\>, n\_jobs: int \= 1) -> Tuple\[pathlib.Path, pubget.\_ExitCode\]:Compute word counts and TFIDF features and store them in `.npz` files.

###### Parameters

- **extracted\_data\_dir**: The directory containing the text of articles to vectorize. It is a directory created by `[pubget.extract_data_to_csv](https://neuroquery.github.io/pubget/#extract_data_to_csv)`: it contains a file named `text.csv` with fields `pmcid`, `title`, `keywords`, `abstract`, `body`.
- **output\_dir**: The directory in which to store the results. If not specified, a sibling directory of `extracted_data_dir` will be used. Its name will end with `-voc_<md5 checksum of the vocabulary>_vectorizedText`.
- **vocabulary**: A file containing the vocabulary used to vectorize text, with one term or phrase per line. Each dimension in the output will correspond to the frequency of one entry in this vocabulary. By default, the vocabulary used by [https://neuroquery.org](https://neuroquery.org/) will be downloaded and used.
- **n\_jobs**: Number of processes to run in parallel. `-1` means using all processors.

###### Returns

- **output\_dir**: The directory in which the vectorized data is stored.
- **exit\_code**: COMPLETED if previous (data extraction) step was complete and this step (vectorization) finished normally as well. Used by the `pubget` command-line interface.

-----------------------------------------------------

## Quick Start for the CLI

Once `pubget` is installed, we can download and process biomedical publications so that we can later use them for text-mining or meta-analysis.

```
pubget run ./pubget_data -q "fMRI[title]"
```

See `pubget run --help` for a description of this command. For example, the `--n_jobs` option allows running some of the steps in parallel.

## Usage

The creation of a dataset happens in 3 steps:

- Downloading the articles in bulk from the [PMC](https://www.ncbi.nlm.nih.gov/pmc/) API.
- Extracting the articles from the bulk download
- Extracting text, stereotactic coordinates and metadata from the articles, and storing this information in CSV files.

Afterwards, some optional steps can also be run, such as:

- Vectorizing the text: transforming it into vectors of [TFIDF](https://en.wikipedia.org/wiki/Tf%E2%80%93idf) features.
- Running the same analyses as NeuroSynth or NeuroQuery.
- Preparing the data for use with labelbuddy or NiMARE.

Each of these steps stores its output in a separate directory. Normally, you will run the whole procedure in one command by invoking `pubget run`. However, separate commands are also provided to run each step separately. Below, we describe each step and its output. Use `pubget -h` to see a list of all available commands and `pubget run -h` to see all the options of the main command.

All articles downloaded by `pubget` come from [PubMed Central](https://www.ncbi.nlm.nih.gov/pmc/), and are therefore identified by their PubMed Central ID (`pmcid`). Note this is not the same as the PubMed ID (`pmid`). Not all articles in PMC have a `pmid`.

`pubget` only downloads articles from the [Open Access subset](https://www.ncbi.nlm.nih.gov/pmc/tools/openftlist/) of PMC. The open-access papers are the papers whose license allows downloading their text for text-mining or other reuse (Creative Commons or similar licenses). To restrict search results to the open-access subset on the PMC website (and see the papers that would be downloaded by `pubget`), select "Open access" in the "article attributes" list.

## Step 1: Downloading articles from PMC

This step is executed by the `pubget download` command. Articles to download can be selected in 2 different ways: by using a query to search the PMC database, or by providing an explicit list of article PMCIDs. To use a list of PMCIDs, we must pass the path to a file containing the IDs as the `--pmcids_file` parameter. It must contain one ID per line, for example:

```
8217889
7518235
7500239
7287136
7395771
7154153
```

Note these must be PubMedCentral IDs, *not* PubMed IDs. Moreover, Some articles can be viewed on the PubMedCentral website, but are not in the Open Access subset. The publisher of these articles forbids downloading their full text in XML form. `pubget` filters the list of PMCIDs and only downloads those that are in the Open Access subset. When we use a query instead of a PMCID list, only articles in the Open Access subset are considered.

If we use a query instead, we do not use the `--pmcids_file` option, but either `--query` or `--query_file`. Everything else works in the same way, and the rest of this documentation relies on an example that uses a query.

We must first define our query, with which Pubmed Central will be searched for articles. It can be simple such as `fMRI`, or more specific such as `fMRI[Abstract] AND (2000[PubDate] : 2022[PubDate])`. You can build the query using the [PMC advanced search interface](https://www.ncbi.nlm.nih.gov/pmc/advanced). For more information see [the E-Utilities help](https://www.ncbi.nlm.nih.gov/books/NBK3837/). Some examples are provided in the `pubget` git repository, in `docs/example_queries`.

The query can be passed either as a string on the command-line with `-q` or `--query` or by passing the path of a text file containing the query with `-f` or `--query_file`.

If we have an NCBI API key (see details in the [E-utilities documentation](https://www.ncbi.nlm.nih.gov/books/NBK25497/)), we can provide it through the `NCBI_API_KEY` environment variable or through the `--api_key` command line argument (the latter has higher precedence).

We must also specify the directory in which all `pubget` data will be stored. It can be provided either as a command-line argument (as in the examples below), or by exporting the `PUBGET_DATA_DIR` environment variable. Subdirectories will be created for each different query. In the following we suppose we are storing our data in a directory called `pubget_data`.

We can thus download all articles with "fMRI" in their title published in 2019 by running:

```
pubget download -q "fMRI[Title] AND (2019[PubDate] : 2019[PubDate])" pubget_data
```

---

**Note:** writing the query in a file rather than passing it as an argument is more convenient for complex queries, for example those that contain whitespace, newlines or quotes. By storing it in a file we do not need to take care to quote or escape characters that would be interpreted by the shell. In this case we would store our query in a file, say `query.txt`:

```
fMRI[Title] AND (2019[PubDate] : 2019[PubDate])
```

and run

```
pubget download -f query.txt pubget_data
```

---

After running this command, these are the contents of our data directory:

```
· pubget_data
  └── query_3c0556e22a59e7d200f00ac8219dfd6c
      ├── articlesets
      │   ├── articleset_00000.xml
      │   └── info.json
      └── query.txt
```

`pubget` has created a directory for this query, `query_3c0556e22a59e7d200f00ac8219dfd6c` — in the following we will call it "the query directory". Its name contains the md5 checksum of the query (or PMCID list), which is useful for `pubget` to reuse the same directory if we run the same query again, but not very helpful for us humans. Therefore, we can use the `--alias` command-line argument to give this query an alternative name, and `pubget` will create a symbolic link for us. For example if we run the query above with the added option `--alias "fMRI-2019"`, our `pubget_data` directory will look like this:

```
· pubget_data
  ├── fMRI-2019 -> query_3c0556e22a59e7d200f00ac8219dd6c
  └── query_3c0556e22a59e7d200f00ac8219dd6c
```

If we had used a PMCID list instead of a query, the directory name would start with `pmcidList_` instead of `query_`.

If we used a query it will be stored in `query.txt`, and if we used a list of PMCIDs, in `requested_pmcids.txt`, in the query directory.

Inside the query directory, the results of the bulk download are stored in the `articlesets` subdirectory. The articles themselves are in XML files bundling up to 500 articles called `articleset_*.xml`. Here there is only one because the search returned less than 500 articles.

Some information about the download is stored in `info.json`. In particular, `is_complete` indicates if all articles matching the search have been downloaded. If the download was interrupted, some batches failed to download, or the number of results was limited by using the `--n_docs` parameter, `is_complete` will be `false` and the exit status of the program will be 1. You may want to re-run the command before moving on to the next step if the download is incomplete.

If we run the same query again, only missing batches will be downloaded. If we want to force re-running the search and downloading the whole data we need to remove the `articlesets` directory.

## Step 2: extracting articles from bulk download

This step is executed by the `pubget extract_articles` command.

Once our download is complete, we extract articles and store each of them in a separate directory. To do so, we pass the `articlesets` directory created by the `pubget download` command in step 1:

```
pubget extract_articles pubget_data/query_3c0556e22a59e7d200f00ac8219dfd6c/articlesets
```

This creates an `articles` subdirectory in the query directory, containing the articles. To avoid having a large number of files in a single directory when there are many articles, which can be problematic on some filesystems, the articles are spread over many subdirectories. The names of these subdirectories range from `000` to `fff` and an article goes in the subdirectory that matches the first 3 hexidecimal digits of the md5 hash of its `pmcid`.

Our data directory now looks like this (with many articles omitted for conciseness):

```
· pubget_data
  └── query_3c0556e22a59e7d200f00ac8219dfd6c
      ├── articles
      │   ├── 019
      │   │   └── pmcid_6759467
      │   │       ├── article.xml
      │   │       └── tables
      │   │           └── tables.xml
      │   ├── 01f
      │   │   └── pmcid_6781806
      │   │       ├── article.xml
      │   │       └── tables
      │   │           ├── table_000.csv
      │   │           ├── table_000_info.json
      │   │           ├── table_001.csv
      │   │           ├── table_001_info.json
      │   │           └── tables.xml
      │   ├── ...
      │   └── info.json
      └── articlesets
```

Note that the subdirectories such as `articles/01f` can contain one or more articles, even though the examples that appear here only contain one.

Each article directory, such as `articles/01f/pmcid_6781806`, contains:

- `article.xml`: the XML file containing the full article in its original format.
- a `tables` subdirectory, containing:
- `tables.xml`: all the article's tables, each provided in 2 formats: its original version, and converted to XHTML using the [DocBook](https://docbook.org/) stylesheets.
- For each table, a CSV file containing the extracted data and a JSON file providing information such as the table label, id, caption, and `n_header_rows`, the number of rows at the start of the CSV that should be treated as part of the table header.

If the download and article extraction were successfully run and we run the same query again, the article extraction is skipped. If we want to force re-running the article extraction we need to remove the `articles` directory (or the `info.json` file it contains).

## Step 3: extracting data from articles

This step is executed by the `pubget extract_data` command.

It creates another directory that contains CSV files, containing the text, metadata and coordinates extracted from all the articles.

If we use the `--articles_with_coords_only` option, only articles in which `pubget` finds stereotactic coordinates are kept. The name of the resulting directory will reflect that choice.

We pass the path of the `articles` directory created by `pubget extract_articles` in the previous step to the `pubget extract_data` command:

```
pubget extract_data --articles_with_coords_only pubget_data/query_3c0556e22a59e7d200f00ac8219dfd6c/articles/
```

Our data directory now contains (ommitting the contents of the previous steps):

```
· pubget_data
  └── query_3c0556e22a59e7d200f00ac8219dfd6c
      ├── articles
      ├── articlesets
      └── subset_articlesWithCoords_extractedData
          ├── authors.csv
          ├── coordinates.csv
          ├── coordinate_space.csv
          ├── info.json
          ├── links.csv
          ├── neurovault_collections.csv
          ├── neurovault_images.csv
          ├── metadata.csv
          └── text.csv
```

If we had not used `--articles_with_coords_only`, the new subdirectory would be named `subset_allArticles_extractedData` instead.

- `metadata.csv` contains one row per article, with some metadata: `pmcid` (PubMed Central ID), `pmid` (PubMed ID), `doi`, `title`, `journal`, `publication_year` and `license`. Note some values may be missing (for example not all articles have a `pmid` or `doi`).
- `authors.csv` contains one row per article per author. Fields are `pmcid`, `surname`, `given-names`.
- `text.csv` contains one row per article. The first field is the `pmcid`, and the other fields are `title`, `keywords`, `abstract`, and `body`, and contain the text extracted from these parts of the article.
- `links.csv` contains the external links found in the articles. The fields are `pmcid`, `ext-link-type` (the type of link, for example "uri", "doi"), and `href` (usually an URL).
- `neurovault_collections.csv` and `neurovault_images.csv`: [NeuroVault](https://neurovault.org/) collection and image IDs that could be extracted from links in the articles, if any.
- `coordinates.csv` contains one row for each `(x, y, z)` stereotactic coordinate found in any article. Its fields are the `pmcid` of the article, the table label and id the coordinates came from, and `x`, `y`, `z`.
- `coordinate_space.csv` has fields `pmcid` and `coordinate_space`. It contains a guess about the stereotactic space coordinates are reported in, based on a heuristic derived from [neurosynth](https://github.com/neurosynth/ACE). Possible values for the space are the terms used by `neurosynth`: "MNI", "TAL" (for Talairach space), and "UNKNOWN".

The different files can be joined on the `pmcid` field.

If all steps up to data extraction were successfully run and we run the same query again, the data extraction is skipped. If we want to force re-running the data extraction we need to remove the corresponding directory (or the `info.json` file it contains).

This step is executed by the `pubget extract_vocabulary` command. When running the full pipeline this step is optional: we must use the `--extract_vocabulary` option for it to be executed.

It builds a vocabulary of all the words and 2-grams (groups of 2 words) that appear in the downloaded text, and computes their document frequency (the proportion of documents in which a term appears).

```
pubget extract_vocabulary pubget_data/query_3c0556e22a59e7d200f00ac8219dfd6c/subset_articlesWithCoords_extractedData
```

The vocabulary is stored in a csv file in a new directory. There is no header and the 2 columns are the term and its document frequency.

```
· pubget_data
  └── query_3c0556e22a59e7d200f00ac8219dfd6c
      ├── articles
      ├── articlesets
      ├── subset_articlesWithCoords_extractedData
      └── subset_articlesWithCoords_extractedVocabulary
          ├── info.json
          └── vocabulary.csv
```

When running the whole pipeline (`pubget run`), if we use the `--extract_vocabulary` option and do not provide an explicit value for `--vocabulary_file`, the freshly-extracted vocabulary is used instead of the default `neuroquery` one for computing TFIDF features (see next step).

## Optional step: vectorizing (computing TFIDF features)

This step is executed by the `pubget vectorize` command. When running the full pipeline this step is optional: we must use the `--vectorize_text` option for it to be executed. However, if any of the subsequent steps that rely on TFIDF features (NeuroQuery, NeuroSynth or NiMARE steps, see below) are requested, this step is always run and `--vectorize_text` is ignored. This step is also run whenever we use the `--vocabulary_file` option.

Some large-scale meta-analysis methods such as [NeuroSynth](https://neurosynth.org/) and [NeuroQuery](https://neuroquery.org/) rely on [TFIDF features](https://en.wikipedia.org/wiki/Tf%E2%80%93idf) to represent articles' text. The last step before we can apply these methods is therefore to extract TFIDF features from the text we obtained in the previous step.

TFIDF features rely on a predefined vocabulary (set of terms or phrases). Each dimension of the feature vector corresponds to a term in the vocabulary and represents the importance of that term in the encoded text. This importance is an increasing function of the *term frequency* (the number of time the term occurs in the text divided by the length of the text) and a decreasing function of the *document frequency* (the total number of times the term occurs in the whole corpus or dataset).

To extract the TFIDF features we must therefore choose a vocabulary.

- By default, `pubget` will download and use the vocabulary used by [neuroquery.org](https://neuroquery.org/).
- If we use the `--extract_vocabulary` option, a new vocabulary is created from the downloaded text and used for computing TFIDF features (see "extracting a new vocabulary" below).
- If we want to use a different vocabulary we can specify it with the `--vocabulary_file` option. This file will be parsed as a CSV file with no header, whose first column contains the terms. Other columns are ignored.

We also pass to `pubget vectorize` the directory containing the text we want to vectorize, created by `pubget extract_data` in step 3 (here we are using the default vocabulary):

```
pubget vectorize pubget_data/query_3c0556e22a59e7d200f00ac8219dfd6c/subset_articlesWithCoords_extractedData/
```

This creates a new directory whose name reflects the data source (whether all articles are kept or only those with coordinates) and the chosen vocabulary (`e6f7a7e9c6ebc4fb81118ccabfee8bd7` is the md5 checksum of the contents of the vocabulary file, concatenated with those of the vocabulary mapping file, see "vocabulary mapping" below):

```
· pubget_data
  └── query_3c0556e22a59e7d200f00ac8219dfd6c
      ├── articles
      ├── articlesets
      ├── subset_articlesWithCoords_extractedData
      └── subset_articlesWithCoords-voc_e6f7a7e9c6ebc4fb81118ccabfee8bd7_vectorizedText
          ├── abstract_counts.npz
          ├── abstract_tfidf.npz
          ├── body_counts.npz
          ├── body_tfidf.npz
          ├── feature_names.csv
          ├── info.json
          ├── keywords_counts.npz
          ├── keywords_tfidf.npz
          ├── merged_tfidf.npz
          ├── pmcid.txt
          ├── title_counts.npz
          ├── title_tfidf.npz
          ├── vocabulary.csv
          └── vocabulary.csv_voc_mapping_identity.json
```

The extracted features are stored in `.npz` files that can be read for example with [`scipy.sparse.load_npz`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.load_npz.html).

These files contain matrices of shape `(n_docs, n_features)`, where `n_docs` is the number of documents and `n_features` the number of terms in the vocabulary. The `pmcid` corresponding to each row is found in `pmcid.txt`, and the term corresponding to each column is found in the first column of `feature_names.csv`.

`feature_names.csv` has no header; the first column contains terms and the second one contains their document frequency.

For each article part ("title", "keywords", "abstract" and "body"), we get the `counts` which hold the raw counts (the number of times each word occurs in that section), and the `tfidf` which hold the TFIDF features (the counts divided by article length and log document frequency). Moreover, `merged_tfidf` contains the mean TFIDF computed across all article parts.

If all steps up to vectorization were successfully run and we run the same query again, the vectorization is skipped. If we want to force re-running the vectorization we need to remove the corresponding directory (or the `info.json` file it contains).

### Vocabulary mapping: collapsing synonyms

It is possible to instruct the tokenizer (that extracts words from text) to collapse some pairs of terms that have the same meaning but different spellings, such as "brainstem" and "brain stem".

This is done through a JSON file that contains a mapping of the form `{term: replacement}`. For example if it contains `{"brain stem": "brainstem"}`, "brain stem" will be discarded from the vocabulary and every occurrence of "brain stem" will be counted as an occurrence of "brainstem" instead. To be found by `pubget`, this vocabulary mapping file must be in the same directory as the vocabulary file, and its name must be the vocabulary file's name with `_voc_mapping_identity.json` appended: for example `vocabulary.csv`, `vocabulary.csv_voc_mapping_identity.json`.

When a vocabulary mapping is provided, a shorter vocabulary is therefore created by removing redundant words. The TFIDF and word counts computed by `pubget` correspond to the shorter vocabulary, which is stored along with its document frequencies in `feature_names.csv`.

`vocabulary.csv` contains the document frequencies of the original (full, longer) vocabulary. A `vocabulary.csv_voc_mapping_identity.json` file is always created by `pubget`, but if no vocabulary mapping was used, that file contains an empty mapping (`{}`) and `vocabulary.csv` and `feature_names.csv` are identical.

The vocabulary mapping is primarily used by the `neuroquery` package and its tokenization pipeline, and you can safely ignore this – just remember that the file providing the terms corresponding to the TFIDF *features* is `feature_names.csv`.

## Optional step: fitting a NeuroQuery encoding model

This step is executed by the `pubget fit_neuroquery` command. When running the full pipeline it is optional: we must use the `--fit_neuroquery` option for it to be executed.

In this step, once the TFIDF features and the coordinates have been extracted from downloaded articles, they are used to train a NeuroQuery encoding model — the same type of model that is exposed at [neuroquery.org](https://neuroquery.org/). Details about this model are provided in [the NeuroQuery paper](https://elifesciences.org/articles/53385) and the documentation for the [neuroquery package](https://github.com/neuroquery/neuroquery).

Note: for this model to give good results a large dataset is needed, ideally close to 10,000 articles (with coordinates).

We pass the `_vectorizedText` directory created by `pubget vectorize`:

```
pubget fit_neuroquery pubget_data/query_3c0556e22a59e7d200f00ac8219dfd6c/subset_articlesWithCoords-voc_e6f7a7e9c6ebc4fb81118ccabfee8bd7_vectorizedText
```

This creates a directory whose name ends with `_neuroqueryModel`:

```
· pubget_data
  └── query_3c0556e22a59e7d200f00ac8219dfd6c
      ├── articles
      ├── articlesets
      ├── subset_articlesWithCoords_extractedData
      ├── subset_articlesWithCoords-voc_e6f7a7e9c6ebc4fb81118ccabfee8bd7_neuroqueryModel
      │   ├── app.py
      │   ├── info.json
      │   ├── neuroquery_model
      │   │   ├── corpus_metadata.csv
      │   │   ├── corpus_tfidf.npz
      │   │   ├── mask_img.nii.gz
      │   │   ├── regression
      │   │   │   ├── coef.npy
      │   │   │   ├── intercept.npy
      │   │   │   ├── M.npy
      │   │   │   ├── original_n_features.npy
      │   │   │   ├── residual_var.npy
      │   │   │   └── selected_features.npy
      │   │   ├── smoothing
      │   │   │   ├── smoothing_weight.npy
      │   │   │   └── V.npy
      │   │   ├── vocabulary.csv
      │   │   └── vocabulary.csv_voc_mapping_identity.json
      │   ├── README.md
      │   └── requirements.txt
      └── subset_articlesWithCoords-voc_e6f7a7e9c6ebc4fb81118ccabfee8bd7_vectorizedText
```

You do not need to care about the contents of the `neuroquery_model` subdirectory, that is data used by the `neuroquery` package. Just know that it can be used to initialize a `neuroquery.NeuroQueryModel` with:

```pdoc
from neuroquery import NeuroQueryModel
model = NeuroQueryModel.from_data_dir("neuroquery_model")
```

The `neuroquery` documentation provides information and examples on how to use this model.

### Visualizing the newly trained model in an interactive web page

It is easy to interact with the model through a small web (Flask) application. From inside the `[...]_neuroqueryModel` directory, just run `pip install -r requirements.txt` to install `flask`, `nilearn` and `neuroquery`. Then run `flask run` and point your web browser to `https://localhost:5000`: you can play with a local, simplified version of [neuroquery.org](https://neuroquery.org/) built with the data we just downloaded.

This step is executed by the `pubget fit_neurosynth` command. When running the full pipeline it is optional: we must use the `--fit_neurosynth` option for it to be executed.

In this step, once the TFIDF features and the coordinates have been extracted from downloaded articles, they are used to run meta-analyses using NeuroSynth's "association test" method: a Chi-squared test of independence between voxel activation and term occurrences. See [the NeuroSynth paper](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3146590/) and [neurosynth.org](https://neurosynth.org/), as well as the [neurosynth](https://github.com/neurosynth/neurosynth) and [NiMARE](https://nimare.readthedocs.io/) documentation pages for more information.

We pass the `_vectorizedText` directory created by `pubget vectorize`:

```
pubget fit_neurosynth pubget_data/query_3c0556e22a59e7d200f00ac8219dfd6c/subset_articlesWithCoords-voc_e6f7a7e9c6ebc4fb81118ccabfee8bd7_vectorizedText
```

This creates a directory whose name ends with `_neurosynthResults`:

```
· pubget_data
  └── query_3c0556e22a59e7d200f00ac8219dfd6c
      ├── articles
      ├── articlesets
      ├── subset_articlesWithCoords_extractedData
      ├── subset_articlesWithCoords-voc_e6f7a7e9c6ebc4fb81118ccabfee8bd7_neurosynthResults
      │   ├── app.py
      │   ├── info.json
      │   ├── metadata.csv
      │   ├── neurosynth_maps
      │   │   ├── aberrant.nii.gz
      │   │   ├── abilities.nii.gz
      │   │   ├── ability.nii.gz
      │   │   └── ...
      │   ├── README.md
      │   ├── requirements.txt
      │   ├── terms.csv
      │   └── tfidf.npz
      └── subset_articlesWithCoords-voc_e6f7a7e9c6ebc4fb81118ccabfee8bd7_vectorizedText
```

The meta-analytic maps for all the terms in the vocabulary can be found in the `neurosynth_maps` subdirectory.

### Visualizing the meta-analytic maps in an interactive web page

It is easy to interact with the NeuroSynth maps through a small web (Flask) application. From inside the `[...]_neurosynthResults` directory, just run `pip install -r requirements.txt` to install `flask` and other dependencies. Then run `flask run` and point your web browser to `https://localhost:5000`: you can search for a term and see the corresponding brain map and the documents that mention it.

## Optional step: preparing articles for annotation with `labelbuddy`

This step is executed by the `pubget extract_labelbuddy_data` command. When running the full pipeline this step is optional: we must use the `--labelbuddy` or `--labelbuddy_batch_size` option for it to be executed.

It prepares the articles whose data was extracted for annotation with [labelbuddy](https://jeromedockes.github.io/labelbuddy/).

We pass the `_extractedData` directory created by `pubget extract_data`:

```
pubget extract_labelbuddy_data pubget_data/query_3c0556e22a59e7d200f00ac8219dfd6c/subset_articlesWithCoords_extractedData
```

This creates a directory whose name ends with `labelbuddyData` containing the batches of documents in JSONL format (in this case there is a single batch):

```
· pubget_data
  └── query_3c0556e22a59e7d200f00ac8219dfd6c
      ├── articles
      ├── articlesets
      ├── subset_articlesWithCoords_extractedData
      ├── subset_articlesWithCoords_labelbuddyData
      │   ├── batch_info.csv
      │   ├── documents_00001.jsonl
      │   └── info.json
      └── subset_articlesWithCoords-voc_e6f7a7e9c6ebc4fb81118ccabfee8bd7_vectorizedText
```

The documents can be imported into `labelbuddy` using the GUI or with:

```
labelbuddy mydb.labelbuddy --import-docs documents_00001.jsonl
```

See the [labelbuddy documentation](https://jeromedockes.github.io/labelbuddy/labelbuddy/current/documentation/) for details.

The CSV file `batch_info.csv` provides the location of each article in the `.jsonl` files: its columns are `pmcid`, `file_name` (the name of the `.jsonl` file containing that article) and `line` (the line number that contains that article, first line is 0).

## Optional step: creating a NiMARE dataset

This step is executed by the `pubget extract_nimare_data` command. When running the full pipeline this step is optional: we must use the `--nimare` option for it to be executed.

It creates a [NiMARE](https://nimare.readthedocs.io/) dataset for the extracted data in JSON format. See the NiMARE [documentation](https://nimare.readthedocs.io/en/latest/generated/nimare.dataset.Dataset.html#nimare.dataset.Dataset) for details.

We pass the `_vectorizedText` directory created by `pubget vectorize`:

```
pubget extract_nimare_data pubget_data/query_3c0556e22a59e7d200f00ac8219dfd6c/subset_articlesWithCoords-voc_e6f7a7e9c6ebc4fb81118ccabfee8bd7_vectorizedText
```

The resulting directory contains a `nimare_dataset.json` file that can be used to initialize a `nimare.Dataset`.

```
· pubget_data
  └── query_3c0556e22a59e7d200f00ac8219dfd6c
      ├── articles
      ├── articlesets
      ├── subset_articlesWithCoords_extractedData
      ├── subset_articlesWithCoords-voc_e6f7a7e9c6ebc4fb81118ccabfee8bd7_nimareDataset
      │   ├── info.json
      │   └── nimare_dataset.json
      └── subset_articlesWithCoords-voc_e6f7a7e9c6ebc4fb81118ccabfee8bd7_vectorizedText
```

Using this option requires installing NiMARE, which is not installed by default with `pubget`. To use this option, install NiMARE separately with

```
pip install nimare
```

or install `pubget` with

```
pip install "pubget[nimare]"
```

## Full pipeline

We can run all steps in one command by using `pubget run`.

The full procedure described above could be run by executing:

```
pubget run -q "fMRI[Title] AND (2019[PubDate] : 2019[PubDate])" \
    --articles_with_coords_only                               \
    pubget_data
```

(The output directory, `pubget_data`, could also be provided by exporting the `PUBGET_DATA_DIR` environment variable instead of passing it on the command line.)

If we also want to apply the optional steps:

```
pubget run -q "fMRI[Title] AND (2019[PubDate] : 2019[PubDate])" \
    --articles_with_coords_only                               \
    --fit_neuroquery                                          \
    --labelbuddy                                              \
    --nimare                                                  \
    pubget_data
```

(remember that `--nimare` requires NiMARE to be installed).

Here also, steps that had already been completed are skipped; we need to remove the corresponding directories if we want to force running these steps again.

See `pubget run --help` for a description of all options.

## Logging

By default `pubget` commands report their progress by writing to the standard streams. In addition, they can write log files if we provide the `--log_dir` command-line argument, or if we define the `PUBGET_LOG_DIR` environment variable (the command-line argument has higher precedence). If this log directory is specified, a new log file with a timestamp is created and all the output is written there as well.

## Writing plugins

It is possible to write plugins and define [entry points](https://setuptools.pypa.io/en/latest/userguide/entry_point.html) to add functionality that is automatically executed when `pubget` is run.

The name of the entry point should be `pubget.plugin_actions`. It must be a function taking no arguments and returning a dictionary with keys `pipeline_steps` and `commands`. The corresponding values must be lists of processing step objects, that must implement the interface defined by `[pubget.PipelineStep](https://neuroquery.github.io/pubget/#PipelineStep)` and `[pubget.Command](https://neuroquery.github.io/pubget/#Command)` respectively (their types do not need to inherit from these classes).

All steps in `pipeline_steps` will be run when `pubget run` is used. All steps in `standalone_steps` will be added as additional pubget commands; for example if the `name` of a standalone step is `my_plugin`, the `pubget my_plugin` command will become available.

An example plugin that can be used as a template, and more details, are provided in the `pubget` git repository, in `docs/example_plugin`.

## Contributing

Feedback and contributions are welcome. Development happens at the [pubget GitHub repositiory](https://github.com/neuroquery/pubget). To install the dependencies required for development, from the directory where you cloned `pubget`, run:

```
pip install -e ".[dev]"
```

The tests can be run with `make test_all`, or `make test_coverage` to report test coverage. The documentation can be rendered with `make doc`. `make run_full_pipeline` runs the full `pubget` pipeline on a query returning a realistic number of results (`fMRI[title]`).
