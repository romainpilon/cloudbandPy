#!/bin/bash
#SBATCH --job-name RunCBDmultiyear
#SBATCH --chdir /scratch/rpilon/log
#SBATCH --nodes 1
#SBATCH --ntasks-per-node 1
#SBATCH --cpus-per-task 1
#SBATCH --mem 64G
#SBATCH --time 01:00:00
#SBATCH --array=0-62

# This code allows to run cloudbandPy over multiple years.
# Please adapt #SBATCH --array=0-62 according to the number of year
# Please check the configuration file parameters of the domain where you want to run the code

# To run: `sbatch run_multiyear_cb_detection_to_file.bash`

module purge
module load gcc python
module load geos proj


# *-------- DEFINE THESE VARIABLES and SET UP CODE
# Define start and end year
YEAR_START=1959
YEAR_END=2022

source /users/rpilon/codes/unil/cloudbandPy/myenv/bin/activate
export CLOUDBANDPY_DIR=/users/rpilon/codes/unil/cloudbandPy
# *--------


# Check if cloudbandPy is installed and activate the environment
activate_env() {
    if python -c "import cloudbandpy" &> /dev/null; then
        echo "cloudbandPy is installed, checking for environments."
        if [[ -n "$VIRTUAL_ENV" ]]; then
            echo "Using the Python virtual environment."
            source "${VIRTUAL_ENV}/bin/activate"
        elif conda info --envs | grep "$(basename "$CONDA_PREFIX")" &> /dev/null; then
            echo "Using the Conda environment: $(basename "$CONDA_PREFIX")"
            source activate "$(basename "$CONDA_PREFIX")"
        else
            echo "No Python virtual or Conda environment is active. Running the script in the base environment."
        fi
    else
        echo "cloudbandPy is not installed. Please modify this script to load it."
        exit 1
    fi
}


# We need to have access to configuration files
# Check if cloudbandPy configuration directory is set up
setup_config_dir() {
    if [[ -z "${CLOUDBANDPY_DIR}" ]]; then
        echo "The CLOUDBANDPY_DIR environment variable is not set. Please set it to your cloudbandPy directory path."
        exit 1
    else
        echo "Using cloudbandPy directory: ${CLOUDBANDPY_DIR}"
    fi
}


# Function to create temporary config files
create_tmp_config() {
    local domain=$1
    local year=$2
    local configname=config_cbworkflow_"${domain}"
    local configpath="${CLOUDBANDPY_DIR}/config/${configname}.yml"
    local outfil="${tmpdir_config}/${configname}_${year}.yml"
    sed "s|2016|${year}|g" "${configpath}" >"${outfil}"
    sed -i "s|save_cloudbands_netcdf: .*|save_cloudbands_netcdf: True|g" "${outfil}"
}


# Main script execution
main() {
    tmpdir_config=~/tmp
    [[ ! -d "${tmpdir_config}" ]] && mkdir "${tmpdir_config}"
    declare -a domains=("southPacific" "northPacific" "southIndianOcean" "southAtlantic" "southernhemisphere" "northernhemisphere")
    years=($(seq $YEAR_START $YEAR_END))
    echo $years
    local year="${years[${SLURM_ARRAY_TASK_ID}]}"

    activate_env
    setup_config_dir

    for domain in "${domains[@]}"; do
        echo "${domain}"
        create_tmp_config "${domain}" "${year}"
        local configfilename=config_cbworkflow_"${domain}_${year}.yml"
        local configpath="${tmpdir_config}/${configfilename}"
        echo "${CLOUDBANDPY_DIR}" "${configpath}"
        python "${CLOUDBANDPY_DIR}/runscripts/run.py" "${configpath}"
    done
}

main