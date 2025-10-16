# ipeds-wrangler

## What it does

The United States National Center for Education Statistics (NCES) maintains the Integrated Postsecondary Education Data System (IPEDS). Each year, IPEDS collects data from approximately 6,000 institutions, representing more than 15 million students. These data can enable many institutional research projects, such as: benchmarking against peer institutions, tracking enrollment trends, and analyzing graduation rates. However, IPEDS data can be challenging to wrangle into actionable insights - especially for Python users.

This package is new, but ipeds-wrangler will enable Python users to:

- Webscrape IPEDS databases from NCES.
- Search IPEDS databases efficiently.
- Read .accdb tables into pd.DataFrame() format.
- Convert numerical categorical variables into user-friendly text.

## Get started

```python
>>> from ipeds-wrangler import download_databases
>>> download_databases()

```