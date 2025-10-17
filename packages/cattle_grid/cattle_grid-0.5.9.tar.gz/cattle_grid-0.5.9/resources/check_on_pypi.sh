#!/bin/sh

VERSION=$(uv run hatch version)

echo $VERSION

AVAILABLE=$(curl https://pypi.org/rss/project/cattle-grid/releases.xml --silent | grep $VERSION -m 1)

while [ -z "$AVAILABLE" ]; do 
    echo "not available yet"; 
    sleep 10;
    AVAILABLE=$(curl https://pypi.org/rss/project/cattle-grid/releases.xml --silent | grep $VERSION -m 1)
done