#!/bin/sh
cd $(dirname $(readlink -f $0))/bin && python '../share/pytomtom/src/pytomtom.py'
