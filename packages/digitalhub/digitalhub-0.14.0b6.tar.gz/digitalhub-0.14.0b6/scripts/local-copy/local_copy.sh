# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0
SRC=
DST=
DIRECTORIES=(
    digitalhub
    runtimes/container/digitalhub_runtime_container
    runtimes/dbt/digitalhub_runtime_dbt
    runtimes/kfp/digitalhub_runtime_kfp
    runtimes/python/digitalhub_runtime_python
    runtimes/modelserve/digitalhub_runtime_modelserve
)
for dir in "${DIRECTORIES[@]}"; do
    cp -r $SRC/$dir $DST
done
echo "Done"
