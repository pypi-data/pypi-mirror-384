#!/bin/bash

lt --port 20080 --host http://lt.thingbine.com &
sleep 5
lt --port 29090 --host http://lt.thingbine.com &
sleep 5
lt --port 23000 --host http://lt.thingbine.com &