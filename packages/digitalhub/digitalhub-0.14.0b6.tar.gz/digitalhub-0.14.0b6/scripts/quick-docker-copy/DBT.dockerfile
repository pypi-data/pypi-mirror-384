# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0
ARG VERSION=latest
FROM ghcr.io/scc-digitalhub/digitalhub-sdk/wrapper-dbt:${VERSION}

ARG ROOT=/usr/local/lib/python3.9/site-packages

COPY ./digitalhub-sdk/digitalhub ${ROOT}/digitalhub
COPY ./digitalhub-sdk-runtime-dbt/digitalhub_runtime_dbt ${ROOT}/digitalhub_runtime_dbt
COPY ./digitalhub-sdk-wrapper-dbt/wrapper.py /app

USER root
RUN chown -R nonroot ${ROOT}/digitalhub*

USER 8877
