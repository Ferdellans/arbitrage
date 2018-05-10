# BUILD_DIR := $(shell pwd)/build
# DIST_DIR := $(shell pwd)/dist
# VERSION := $(shell git describe --always)

test: venv
	venv/bin/pytest -s -v --flake8

venv:
	virtualenv --python=python3 venv
	venv/bin/pip install -r requirements.txt

# clean:
# 	rm -rf build dist

# receiver: clean
# 	mkdir -p $(DIST_DIR)
# 	git archive --format=tar.gz \
# 				--prefix=services/receiver/ HEAD:receiver/ > $(DIST_DIR)/receiver-$(VERSION).tar.gz
