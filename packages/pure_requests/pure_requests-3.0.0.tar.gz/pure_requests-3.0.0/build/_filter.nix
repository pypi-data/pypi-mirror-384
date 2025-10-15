let
  metadata = (builtins.fromTOML (builtins.readFile ../pyproject.toml)).project;
in path_filter: src:
path_filter {
  root = src;
  include = [ metadata.name "tests" "pyproject.toml" "mypy.ini" "ruff.toml" ];
}
