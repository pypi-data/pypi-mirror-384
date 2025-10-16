#!/bin/sh

rm -rf dist/*
py -m build
py -m twine upload dist/*