# ymp_environments
Frozen conda environments for YMP

This repository is populated from the YMP CI pipeline. It contains the
latest set of fully specified conda environments under which all unit
tests have passed. In contrast to the environment specification files
in `ymp/rules/`, these files specify each installed package, it's
version and build identifier. The `.yml` files contain this information
in YAML format suitable for `conda env install`, the `.txt` files
contain a set of URLs suitable for `conda create`. As these are
platform specific, the environment files for `macos` and `linux` are
kept in separate folders.
