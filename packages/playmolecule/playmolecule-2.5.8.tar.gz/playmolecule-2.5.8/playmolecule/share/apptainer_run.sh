# (c) 2015-2023 Acellera Ltd http://www.acellera.com
# All Rights Reserved
# Distributed under HTMD Software License Agreement
# No redistribution in whole or part
#
#!/bin/bash

license_server={{ license_file_or_server }}
slpm={{ root_dir }}
image_file=$slpm/apps/$1
decrypter_file=$slpm/apps/pm-decrypter
job_dir=$2
inputfolder=$3

if which singularity; then
    echo "Found singularity executable"
    SINGULARITY_BIN=singularity
    export SINGULARITYENV_PM_APP_ROOT=$slpm
    if [[ -v CUDA_VISIBLE_DEVICES ]]; then
        export SINGULARITYENV_CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES
    fi
fi

if which apptainer; then
    echo "Found apptainer executable"
    SINGULARITY_BIN=apptainer
    unset SINGULARITYENV_PM_APP_ROOT
    export APPTAINERENV_PM_APP_ROOT=$slpm
    if [[ -v CUDA_VISIBLE_DEVICES ]]; then
        unset SINGULARITYENV_CUDA_VISIBLE_DEVICES
        export APPTAINERENV_CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES
    fi
fi

if [ -z "$SINGULARITY_BIN" ]; then
    echo "Could not find singularity/apptainer executable"
    exit 1
fi

ACELLERA_LICENCE_FILE=$license_server ACELLERA_LICENCE_SERVER=$license_server $decrypter_file -appimage $image_file -singularity $SINGULARITY_BIN \
        run --nv --cleanenv --home $job_dir \
        -B $job_dir:/data \
        -B $slpm \
        $image_file \
        --input-json $inputfolder/inputs.json

if [ $? -eq 2 ]; then
    echo "License is not valid for app $image_file"
    exit 1
fi
if [ $? -ne 0 ]; then
    echo "Error in running application. Check logs..."
    exit 1
fi
