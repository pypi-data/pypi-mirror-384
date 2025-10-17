
VENV_PYTHON = ../venv/bin/python
PACKAGE_NAME = weighted_cardinality_estimation
SRC_DIR = src
BUILD_DIR = .build

.PHONY: all help build build_fast test

clean:
	rm -rf .build

# need to do testing for this
build_fast:
	pip install . \
		--no-deps \
		--no-build-isolation \
		-Cbuild-dir=$(BUILD_DIR) \
		-Ccmake.args="-DCMAKE_BUILD_TYPE=Release" \
		-vvv


build:
	python -m pip install . --no-deps --no-build-isolation -Cbuild-dir=.build -vvv

# it will also install dependencies so good for first time
build_with_deps:
	python -m pip install . -Cbuild-dir=.build -vvv

test:
	$(VENV_PYTHON) -m pytest tests/

# on my PC (ryzen 7 5800X), it runs 83 seconds. Command not used for long time, don't knwo if works.
bench:
	pytest benchmarks/bench_sketches.py -q --benchmark-disable-gc --benchmark-warmup=on

# This command is used to run regression for asv. It runs it since stable commit. 
asv_regression:
	asv run NEW