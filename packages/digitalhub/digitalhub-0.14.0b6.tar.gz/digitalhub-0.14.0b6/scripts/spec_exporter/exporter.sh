# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0
read -p "Enter DTO uppercase: " DTO
read -p "Enter KIND: " KIND

if [ -z "$DTO" ] || [ -z "$KIND" ]; then
    echo "Error: DTO and KIND must be provided"
    exit 1
fi
BASE_API=http://192.168.49.2:30180/api/v1/schemas
curl $BASE_API/$DTO/$KIND --user  | jq -r ".schema" > ${DTO}_${KIND}.json
datamodel-codegen   --input ${DTO}_${KIND}.json \
                    --input-file-type jsonschema \
                    --output ./ \
                    --output-model-type pydantic_v2.BaseModel \
                    --enum-field-as-literal all \
                    --field-constraints \
                    --use-generic-container-types \
                    --use-standard-collections \
                    --snake-case-field \
                    --strip-default-none \
                    --allow-extra-fields \
                    --class-name Validator

rm ${DTO}_${KIND}.json
