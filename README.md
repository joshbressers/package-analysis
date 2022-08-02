# npm-analysis
A project to mine npm packages for interesting data


# Running

- All packages
- `curl https://replicate.npmjs.com/registry/_all_docs > all_packages.json`
- To continue
- `curl 'https://replicate.npmjs.com/registry/_all_docs?startkey="@openfonts/baloo-da_vietnamese"' >> all_packages.json`

If you have to continue, the json will require manual surgery.

The loop-parse.sh script will download all the packages. The script likes
to timeout, so this keep restarting it. It will take many days to download
all the data. We can't thread this because the API rate limits pretty fast.

There is no bulk query ability I have found to get this data.

# Interesting notes

Here is how we query just one package
- One package
- `curl https://registry.npmjs.org/express`

The NPM versioning rules are here
https://nodejs.dev/learn/semantic-versioning-using-npm/

To get downloads
https://github.com/npm/registry/blob/master/docs/download-counts.md
https://api.npmjs.org/downloads/point/last-year/@nebulare/tsconfig
