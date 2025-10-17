# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0
VERSION=${1:-latest}
docker build --no-cache --build-arg VERSION=$VERSION -t ghcr.io/scc-digitalhub/digitalhub-sdk/wrapper-dbt:test  -f DBT.dockerfile .
docker build --no-cache --build-arg VERSION=$VERSION -t ghcr.io/scc-digitalhub/digitalhub-sdk/wrapper-kfp:test  -f KFP.dockerfile .
docker build --no-cache --build-arg VERSION=$VERSION -t ghcr.io/scc-digitalhub/digitalhub-serverless/python-runtime:3.9-test -f PY9.dockerfile .
docker build --no-cache --build-arg VERSION=$VERSION -t ghcr.io/scc-digitalhub/digitalhub-serverless/python-runtime:3.10-test -f PY10.dockerfile .
docker build --no-cache --build-arg VERSION=$VERSION -t ghcr.io/scc-digitalhub/digitalhub-serverless/python-runtime:3.11-test -f PY11.dockerfile .
