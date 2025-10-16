{ nixpkgs, pynix, }:
let
  python_overlay = final: prev: {
    arch-lint = import ./arch_lint.nix {
      inherit nixpkgs pynix;
      python_pkgs = prev;
    };
    fa-purity = import ./fa_purity.nix {
      inherit nixpkgs pynix;
      python_pkgs = final;
    };
    pure-requests = import ./pure_requests.nix {
      inherit nixpkgs pynix;
      python_pkgs = final;
    };
  };
  python = pynix.lib.python.override {
    packageOverrides = python_overlay;
    self = python;
  };
  python_pkgs = python.pkgs;
in { inherit python_pkgs; }
