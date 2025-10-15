{ pkgs, lib, config, inputs, ... }:
{
  env.GREET = "devenv";

  dotenv = {
    enable = true;
    disableHint = true;
  };

  cachix = {
    enable = false;
  };

  packages = [
    pkgs.texliveFull
    pkgs.git
    pkgs.gnumake
    pkgs.pre-commit
    pkgs.python3Packages.flake8
    pkgs.yamllint
  ];

  languages = {
    python = {
      enable = true;
      uv = {
        enable = true;
      };
    };
  };

  git-hooks.hooks = {
    default-version = {
      enable = true;
      name = "Ensure default version";
      entry = "git-reset-version";
      pass_filenames = false;
    };

    update-docs-requirements = {
      enable = true;
      name = "Update requirements of documentation";
      entry = "update-docs";
      pass_filenames = false;
    };

    # Remove trailing whitespace
    trailing-whitespace = {
      enable = true;
      package = pkgs.python3Packages.pre-commit-hooks;
      entry = "trailing-whitespace-fixer";
      excludes = [
        "tests/sim/sys/.*$"
        ".*\\.png$"
        ".*\\.jpeg$"
        ".*\\.svg$"
      ];
    };

    # Ensure files end with a newline
    end-of-file-fixer.enable = true;

    # Check YAML syntax
    check-yaml.enable = true;

    # Run Flake8 for Python linting
    flake8.enable = true;
  };

  scripts.update-docs.exec = ''
    temp_file=$(mktemp)
    trap "rm -f $temp_file" 0 2 3 15
    uv export > $temp_file 2>/dev/null

    if diff -q $temp_file docs/requirements.txt &>/dev/null; then
      update-doc-reqs

      if git diff --cached --name-only | grep -q -- 'uv.lock'; then
        git add docs/requirements.txt
      fi
    fi
  '';

  scripts.git-reset-version.exec = ''
      if git diff --cached --name-only | grep -q -- "^pyproject.toml"; then
        uvx --from=toml-cli toml set --toml-path=pyproject.toml project.version 0.0.0 && git add pyproject.toml
      fi
  '';

  scripts.bump-version.exec = ''
    uvx --from=toml-cli toml set --toml-path=pyproject.toml project.version $(uvx dunamai from any --no-metadata --style semver)
  '';

  scripts.generate-package.exec = ''
    bump-version
    uv build
  '';

  scripts.publish-package.exec = ''
    uv publish
  '';

  scripts.generate-doc-reqs.exec = ''
    uv export > docs/requirements.txt
  '';

  scripts.generate-coverage.exec = ''
    if [ "$EUID" -ne 0 ]; then
      uv run --with pytest-cov pytest -k 'not locking' --cov=ekfsm --cov --cov-report term --cov-report xml:coverage.xml | perl -pe 's/\e\[?.*?[\@-~]//g' | tee pytest.log
      uv run --with pytest-cov pytest -k 'not locking' --cov=ekfsm --junitxml=report.xml
    else
      uv run --with pytest-cov pytest --cov=ekfsm --cov --cov-report term --cov-report xml:coverage.xml | perl -pe 's/\e\[?.*?[\@-~]//g' | tee pytest.log
      uv run --with pytest-cov pytest --cov=ekfsm --junitxml=report.xml
    fi
  '';

  scripts.doc-coverage.exec = ''
    uv run make -C docs/ coverage
  '';

  scripts.doc-man-pages.exec = ''
    uv run make -C docs/ man
  '';

  scripts.doc-pdf.exec = ''
    uv run make -C docs/ latexpdf
  '';

  scripts.doc-html.exec = ''
    uv run make -C docs/ html
  '';

  scripts.doc-clean.exec = ''
    uv run make -C docs/ clean
  '';

  scripts.lint.exec = ''
    uvx flake8 --exclude .venv,dist,.devenv
  '';

  scripts.typing.exec = ''
    uv run mypy ekfsm
  '';

  enterShell = ''
    if [ ! -f .git/hooks/pre-commit ]; then
      pre-commit install
      echo "Pre-commit hooks installed."
    fi
    if [ -d .devenv/state/venv ]; then
      source .devenv/state/venv/bin/activate
    else
      echo "No virtual environment found. Package must be generated first."
    fi
  '';

  enterTest = ''
    echo "Running tests"
  '';

  pre-commit.hooks.shellcheck.enable = true;

}
