#
# Makefile
# dephilia, 2021-06-05 15:29
#

all: run

run:
	pipenv run python main.py

test-case:
	pipenv run python -m unittest


# vim:ft=make
#
