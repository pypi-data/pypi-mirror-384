{ nixpkgs, pynix, python_pkgs }:
let
  commit = "bbc7729d6d95c46c60e56fbfa0bfa9fb41f6607d"; # v3.0.0
  sha256 = "1s8946gjxzayfl5dpsf105lwk3lpdbxxb560a4r8z95ssyz5z6p1";
  bundle = let
    src = builtins.fetchTarball {
      inherit sha256;
      url =
        "https://gitlab.com/dmurciaatfluid/pure_requests/-/archive/${commit}/pure_requests-${commit}.tar";
    };
  in import "${src}/build" {
    inherit src;
    inherit nixpkgs pynix;
  };
  extended_python_pkgs = python_pkgs // {
    inherit (bundle.deps) types-simplejson;
  };
in bundle.builders.pkgBuilder
(bundle.builders.requirements extended_python_pkgs)
