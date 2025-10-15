# Dependencies area

This directory for dependencies that have to be cloned locally.

The prime example is Mercurial, because `hg-core` does not enjoy releases
on crates.io, e.g:

```
hg clone https://foss.heptapod.net/mercurial/mercurial-devel mercurial
```

Another case is `rust-protobuf`, needed for some the protocol files that
are not part of the "well-known" collection provided by `prost-types`:

```
git clone https://github.com/stepancheg/rust-protobuf
```

TODO: provide a Makefile to take care of all this
