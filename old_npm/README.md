# npm-analysis
A project to mine npm packages for interesting data


# Running

## First you have to collect a list of all packages. We do this with curl
- All packages
- `curl -o all_packages.json https://skimdb.npmjs.com/registry/_all_docs`
- To continue
- `curl -o all_packages.json 'https://skimdb.npmjs.com/registry/_all_docs?startkey="@openfonts/baloo-da_vietnamese"'`

If you have to continue, the json will require manual surgery.

Then run the loop-parse.sh script will download all the packages. The script likes
to timeout, so this keep restarting it. It will take many days to download
all the data. We can't thread this because the API rate limits pretty fast.

There is no bulk query ability I have found to get this data.

Then run the get-downloads-scoped.py script. This likes to fail. Run it in
a loop.

Then run get-downloads.py

These two scripts are flakey

Then run `read-deps.py output`



# Other notes

Here is how we query just one package
- One package
- `curl https://registry.npmjs.org/express`

The NPM versioning rules are here
https://nodejs.dev/learn/semantic-versioning-using-npm/

To get downloads
https://github.com/npm/registry/blob/master/docs/download-counts.md
https://api.npmjs.org/downloads/point/last-year/@nebulare/tsconfig
