# Ruby generated HGitaly code

This directory contains the Ruby HGitaly gRPC library and helpers to generate
it from the protocol declarations.

This library provides only the definitions that are specific to HGitaly, and
depends on the Gitaly gRPC library.

## Regenerating

Assuming you have an active rbenv:

```
bundle install
./generate-grpc-lib
hg commit
```

## Using the gem locally from the Rails app in a HDK workspace

Edit `Gemfile` in Rails app (clone of `heptapod/heptapod`,
with something like

```
gem 'hgitaly', '>= 0.28.0', path: '../hgitaly/ruby'
```

and run `bundle install`.

Of course, don't commit the changes to `Gemfile` and `Gemfile.lock`. Instead,
once your development is done and the new protocol is satisfying:

- release it in a new version (see below)
- change `Gemfile` to use the published gem
- run `bundle install` again
- commit/push the results.

## Publishing the gem

First, check that the version is appropriate! It is generated automatically
from `../hgitaly/VERSION` (package file in the Python implementation).

```
gem build hgitaly.gemspec
gem push hgitaly.gem
```

See also [Publishing to rubygems.org](https://guides.rubygems.org/publishing/#publishing-to-rubygemsorg)
