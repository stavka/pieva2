#!/bin/bash

BASEPATH=$(dirname $0)/..

FCSERVER="$BASEPATH/fadecandy/server/fcserver ../conf/pieva-prod.json"
PROGRAM="cd $BASEPATH ; python go.py"

$FCSERVER &
FC_PID=$!
echo "fc pid $FC_PID"

$PROGRAM &
PROG_PID=$!
echo "prog pid $PROG_PID"


trap "echo exiting; kill $FC_PID $PROG_PID 2> /dev/null; exit" SIGINT SIGTERM EXIT

echo "waiting to terminate"
wait
