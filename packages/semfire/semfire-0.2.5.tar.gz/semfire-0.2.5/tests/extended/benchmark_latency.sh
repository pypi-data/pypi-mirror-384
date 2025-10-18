#!/bin/bash
# Benchmark latency for API endpoint
for i in {1..10}; do
    curl http://localhost:8080/api/endpoint -o /dev/null -s -w "%{time_total}\n"
done
