#!/bin/sh

set -eux

mkdir -p test_data

curl https://inputs.funfedi.dev/assets/samples.zip -o test_data/samples.zip
curl https://funfedi.dev/assets/samples.zip -o test_data/funfedi-samples.zip