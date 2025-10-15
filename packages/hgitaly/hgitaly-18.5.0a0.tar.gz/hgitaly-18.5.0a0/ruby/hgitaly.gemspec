# coding: utf-8
lib = 'lib'
$LOAD_PATH.unshift(lib) unless $LOAD_PATH.include?(lib)
require 'hgitaly/version'

Gem::Specification.new do |spec|
  spec.name          = "hgitaly"
  spec.version       = Hgitaly::VERSION
  spec.authors       = ["Georges Racinet"]
  spec.email         = ["georges.racinet@octobus.net"]

  spec.summary       = %q{Auto-generated gRPC client for HGitaly}
  spec.description   = %q{Auto-generated gRPC client for the HGitaly protocol, an extension of the Gitaly protocol. Definitions for the latter are not included in this gem.}
  spec.homepage      = "https://foss.heptapod.net/heptapod/hgitaly"
  spec.license       = "LGPL-3.0+"

  spec.files         = Dir.glob(lib + '/**/*.rb')
  spec.require_paths = [lib]

  spec.add_dependency "google-protobuf", "~> 3.1"
  spec.add_dependency "grpc", "~> 1.0"
  # TODO add dependency to gitaly-proto gem (not yet replaced by the one
  # bundle with Gitaly sources, that we expect to be called just "gitaly"),
  # with the appropriate version
end
