#!/bin/bash
./genConf.sh $1

python Graphgen.py $1 $2

./start_nodes.sh

python NetworkObserver.py
