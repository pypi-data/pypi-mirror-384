.PHONY: doc

install:
	pip install -e .[dev]  # Install dependencies
	make install-plugins-submodules  # Install plugins, which may install another solidipes version
	pip install --no-deps -e .  # Ensure local solidipes version is installed
	pre-commit install

lint:
	pre-commit run --all-files

check-annotations:
	pre-commit run --all-files --hook-stage manual ruff

build:
	python3 -m build

test:
	pytest

changelog:
	git checkout main
	git-changelog -o CHANGELOG.md

install-plugins-submodules:
	git submodule update --init --recursive
	# Install dependencies and change push url to ssh
	for dir in $(wildcard plugins/*); do \
		( \
			cd $$dir && \
			echo "Change push url to ssh"; \
			git remote set-url --push origin $$(git remote get-url origin | sed -e 's/^https:\/\/gitlab.com\//git@gitlab.com:/'); \
			pip install -e .[dev] \
		); \
	done
	# Ensure local plugin versions are installed
	for dir in $(wildcard plugins/*); do \
		( \
			cd $$dir && \
			pip install --no-deps -e . \
		); \
	done

doc:
	$(MAKE) -C docs clean html

profile-cli:
	python -m cProfile -o profile.txt solidipes/scripts/main.py
	python -c 'import pstats; p =  pstats.Stats("profile.txt"); p.sort_stats("cumtime").print_stats(30)'
	rm profile.txt
