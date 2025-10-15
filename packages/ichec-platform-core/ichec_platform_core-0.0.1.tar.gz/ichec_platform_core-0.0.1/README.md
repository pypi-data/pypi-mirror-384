# ichec-platform-core

This package has a set of low-level and low-dependency tools used by several ICHEC Platform Engineering projects. Some basic CLI commands are also included, sometimes just as a demo or way to easily test out library features.

# Features #

## Filesystem ##

Filesystem interaction utilities.

**Example CLI:** You can replace all occurences of a string with another recursively in files with:

``` shell
ichec_platform_core filesystem replace_in_files --target $REPLACE_DIR --search $FILE_WITH_SEARCH_TERM --replace $FILE_WITH_REPLACE_TERM 
```

The `search` and `replace` terms are read from files. This can be handy to avoid shell escape sequences - as might be needed in `sed`.

## Network ##

Tooling for communication over a network, includes a:

* `HttpClient`

**Example CLI:** You can download a file with:

``` shell
ichec_platform_core network download --url $RESOURCE_URL --download_dir $WHERE_TO_PUT_DOWNLOAD
```

## Version Control ##

Tooling for interacting with `git` and `gitlab` via its API. Includes a:

* `GitlabClient`

**Example CLI:** You can get the version number of the most recent project release with:

``` shell
ichec_platform_core gitlab --token $GITLAB_TOKEN latest_release $PROJECT_ID
```

or download a particular release asset with:

``` shell
ichec_platform_core gitlab --token $GITLAB_TOKEN latest_release $PROJECT_ID --asset_name $ASSET_NAME
```

The token should have suitable permissions to download project release assets, in particular 'read api', 'repo access' and Developer Role.

You can get info about a git repo with:

``` shell
ichec_platform_core git info 
```

run in the repo.

# Install  #

It is available on PyPI:

``` sh
pip install ichec_platform_core
```

# License #

This project is licensed under the GPLv3+. See the incluced `LICENSE.txt` file for details.
