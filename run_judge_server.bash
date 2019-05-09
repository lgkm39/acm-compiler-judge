#!/bin/bash

cd ./JudgeServer
while(true)
do
	./judge.py ChenYuXuan 2>&1 >>/dev/null
done
