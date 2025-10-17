# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0
ARG VERSION=latest
FROM ghcr.io/scc-digitalhub/digitalhub-serverless/python-runtime:3.10-${VERSION}

ARG ROOT=/opt/conda/lib/python3.10/site-packages

COPY ./digitalhub-sdk/digitalhub ${ROOT}/digitalhub
COPY ./digitalhub-sdk-runtime-python/digitalhub_runtime_python ${ROOT}/digitalhub_runtime_python
COPY ./digitalhub-sdk-runtime-container/digitalhub_runtime_container ${ROOT}/digitalhub_runtime_container
COPY ./digitalhub-sdk-runtime-kfp/digitalhub_runtime_kfp ${ROOT}/digitalhub_runtime_kfp
COPY ./digitalhub-sdk-runtime-dbt/digitalhub_runtime_dbt ${ROOT}/digitalhub_runtime_dbt
COPY ./digitalhub-sdk-runtime-modelserve/digitalhub_runtime_modelserve ${ROOT}/digitalhub_runtime_modelserve
