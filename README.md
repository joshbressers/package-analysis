# npm-analysis
A project to mine npm packages for interesting data

# Interesting notes

## First you have to collect a list of all packages. We do this with curl
- All packages
- `curl -o all_packages.json https://skimdb.npmjs.com/registry/_all_docs`
- To continue
- `curl -o all_packages.json 'https://skimdb.npmjs.com/registry/_all_docs?startkey="@openfonts/baloo-da_vietnamese"'`

## Then we run


# Other notes
- One package
- `curl https://registry.npmjs.org/express`

The NPM versioning rules are here
https://nodejs.dev/learn/semantic-versioning-using-npm/

To get downloads
https://github.com/npm/registry/blob/master/docs/download-counts.md
https://api.npmjs.org/downloads/point/last-year/@nebulare/tsconfig
