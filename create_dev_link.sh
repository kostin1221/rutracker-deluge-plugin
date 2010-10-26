#!/bin/bash
cd /home/dimon/rutrackerplugin
mkdir temp
export PYTHONPATH=./temp
python setup.py build develop --install-dir ./temp
cp ./temp/RutrackerPlugin.egg-link /home/dimon/.config/deluge/plugins
rm -fr ./temp
