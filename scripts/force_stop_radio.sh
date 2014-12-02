#!/bin/sh
ps auxw | grep radio\.py | grep -v grep | sed -e 's/root[ ]*//' | sed -e 's/[ ].*//' | xargs kill -9
