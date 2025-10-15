python_pkgs: lib:
lib.buildPythonPackage rec {
  pname = "types-simplejson";
  version = "3.17.3";
  pyproject = true;
  build-system = [ python_pkgs.setuptools ];
  src = lib.fetchPypi {
    inherit pname version;
    hash = "sha256:0lrjqniv99c888gc8fvvqp8i8zvfrqz39xss6knrk7iiqcmjhl6b";
  };
}
