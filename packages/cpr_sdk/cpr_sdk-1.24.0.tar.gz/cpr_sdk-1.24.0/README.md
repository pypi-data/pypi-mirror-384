# cpr-sdk

Internal library for persistent access to text data.

> **Warning**
> This library is heavily under construction and doesn't work with any of our open data yet. We're working on making it usable for anyone.

## Documents and Datasets

The base document model of this library is `BaseDocument`, which contains only the metadata fields that are used in the parser.

### Loading from Huggingface Hub (recommended)

The `Dataset` class is automatically configured with the Huggingface repos we use. You can optionally provide a document limit, a dataset version, and override the repo that the data is loaded from.

If the repository is private you must provide a [user access token](https://huggingface.co/docs/hub/security-tokens), either in your environment as `HUGGINGFACE_TOKEN`, or as an argument to `from_huggingface`.

```py
from cpr_sdk.models import Dataset, GSTDocument

dataset = Dataset(GSTDocument).from_huggingface(
    version="d8363af072d7e0f87ec281dd5084fb3d3f4583a9", # commit hash, optional
    limit=1000,
    token="my-huggingface-token", # required for private repos if not in env
)
```

The following flag is used for the passage level and flat dataset.

```py
dataset = Dataset(
    document_model=BaseDocument
).from_huggingface(
    dataset_name="ClimatePolicyRadar/passage-level-flat-dataset",
    passage_level_and_flat=True
)
```

### Loading from local storage or s3

```py
# document_id is also the filename stem

document = BaseDocument.load_from_local(folder_path="path/to/data/", document_id="document_1234")

document = BaseDocument.load_from_remote(dataset_key"s3://cpr-data", document_id="document_1234")
```

To manage metadata, documents need to be loaded into a `Dataset` object.

```py
from cpr_sdk.models import Dataset, CPRDocument, GSTDocument

dataset = Dataset().load_from_local("path/to/data", limit=1000)
assert all([isinstance(document, BaseDocument) for document in dataset])

dataset_with_metadata = dataset.add_metadata(
    target_model=CPRDocument,
    metadata_csv="path/to/metadata.csv",
)

assert all([isinstance(document, CPRDocument) for document in dataset_with_metadata])
```

Datasets have a number of methods for filtering and accessing documents.

```py
len(dataset)
>>> 1000

dataset[0]
>>> CPRDocument(...)

# Filtering
dataset.filter("document_id", "1234")
>>> Dataset()

dataset.filter_by_language("en")
>>> Dataset()

# Filtering using a function
dataset.filter("document_id", lambda x: x in ["1234", "5678"])
>>> Dataset()
```

## Search

This library can also be used to run searches against CPR documents and passages in Vespa.

```python
from src.cpr_sdk.search_adaptors import VespaSearchAdapter
from src.cpr_sdk.models.search import SearchParameters

adaptor = VespaSearchAdapter(instance_url="YOUR_INSTANCE_URL")

request = SearchParameters(query_string="forest fires")

response = adaptor.search(request)
```

The above example will return a `SearchResponse` object, which lists some basic information about the request, and the results, arranged as a list of Families, which each contain relevant Documents and/or Passages.

### Sorting

By default, results are sorted by relevance, but can be sorted by date, or name, eg

```python
request = SearchParameters(
    query_string="forest fires",
    sort_by="date",
    sort_order="descending",
)
```

### Filters

Matching documents can also be filtered by keyword field, and by publication date

```python
request = SearchParameters(
    query_string="forest fires",
    filters={
        "language": ["English", "French"],
        "category": ["Executive"],
    },
    year_range=(2010, 2020)
)
```

### Search within families or documents

A subset of families or documents can be retrieved for search using their ids

```python
request = SearchParameters(
    query_string="forest fires",
    family_ids=["CCLW.family.10121.0", "CCLW.family.4980.0"],
)
```

```python
request = SearchParameters(
    query_string="forest fires",
    document_ids=["CCLW.executive.10121.4637", "CCLW.legislative.4980.1745"],
)
```

### Types of query

The default search approach uses a nearest neighbour search ranking.

Its also possible to search for exact matches instead:

```python
request = SearchParameters(
    query_string="forest fires",
    exact_match=True,
)
```

Or to ignore the query string and search the whole database instead:

```python
request = SearchParameters(
    year_range=(2020, 2024),
    sort_by="date",
    sort_order="descending",
)
```

### Continuing results

The response objects include continuation tokens, which can be used to get more results.

For the next selection of families:

```python
response = adaptor.search(SearchParameters(query_string="forest fires"))

follow_up_request = SearchParameters(
    query_string="forest fires"
    continuation_tokens=[response.continuation_token],

)
follow_up_response = adaptor.search(follow_up_request)
```

It is also possible to get more hits within families by using the continuation token on the family object, rather than at the responses root

Note that `this_continuation_token` is used to mark the current continuation of the families, so getting more passages for a family after getting more families would look like this:

```python
follow_up_response = adaptor.search(follow_up_request)

this_token = follow_up_response.this_continuation_token
passage_token = follow_up_response.families[0].continuation_token

follow_up_request = SearchParameters(
    query_string="forest fires"
    continuation_tokens=[this_token, passage_token],
)
```

## Get a specific document

Users can also fetch single documents directly from Vespa, by document ID

```python
adaptor.get_by_id(document_id="id:YOUR_NAMESPACE:YOUR_SCHEMA_NAME::SOME_DOCUMENT_ID")
```

All of the above search functionality assumes that a valid set of vespa credentials is available in `~/.vespa`, or in a directory supplied to the `VespaSearchAdapter` constructor directly. See [the docs](docs/vespa-auth.md) for more information on how vespa expects credentials.

# Test setup

Some tests rely on a local running instance of vespa.

This requires the [vespa cli](https://docs.vespa.ai/en/vespa-cli.html) to be installed.

Setup can then be run with:

```
make install
make vespa_dev_setup
make test
```

Alternatively, to only run non-vespa tests:

```
make test_not_vespa
```

For clean up:

```
make vespa_dev_down
```

### Filtering for concept counts

The cpr_sdk incorporates via `SearchParameters` and a build clause in the `YqlBuilder` class the ability to perform complex queries on the agregated concept counts that are held in the family_document index.

These counts refer to the total number of matches for a concept in a family document. For example concept `Q374:extreme weather` may have 100 matches because the concept for example extreme weather is mentioned in text 100 times.

Simple example. The parameters to return documents containing at least one reference to the concept `extreme weather`:

```python
from cpr_sdk.models.search import ConceptCountFilter, SearchParameters, OperandTypeEnum

request = SearchParameters(
    concept_count_filters=[
        ConceptCountFilter(
            concept_id="Q374:extreme weather",
            count=1,
            operand=OperandTypeEnum(">="),
        )
    ],
)
```

So what other queries can we perform?
- An extensive set of tests have been written for the concept count filters, these display the full capabilities of the filtering functionality:
`tests/test_search_adaptors.py:test_vespa_search_adaptor__concept_counts`

This shows that we can:
- Filter for documents with a match for a concept.
- Filter for documents that don't have a match for a concept.
- Filter for documents with a match for a concept, with a specific count (e.g. > 10 matches)
- Filter for documents with a count of any concept (e.g. > 10 matches)
- Stack filters via an AND operator, e.g. 100 matches for Q123 AND 10 matches for Q456.
- Order results in ascending or descending order such that documents with the most/least matches appear first in search.

See the ConceptCountFilter object for more details.

## Release Flow:

- Make updates to the package.
- Bump the package version in the `cpr_sdk/version.py` module.
- Make a PR.
  - In CI/CD we will check that the version is greater than the latest release.
- Merge.
- Tag a release manually in github with a version that matches the latest on main that you just merged.
  - In CI/CD we will check that the latest release matches the versions defined in code.
- Check in `pypi`.
