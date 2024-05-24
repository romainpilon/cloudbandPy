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


module purge
module load gcc python
module load geos proj


# Check if cloudbandPy is installed and activate the environment
if python -c "import cloudbandpy" &> /dev/null; then
    echo "cloudbandPy is installed, checking for environments."
    # Check for a Python virtual environment
    if [[ -n "$VIRTUAL_ENV" ]]; then
        echo "Using the Python virtual environment."
        source "${VIRTUAL_ENV}"/bin/activate
    # Check for a Conda environment
    elif conda info --envs | grep "$(basename "$CONDA_PREFIX")" &> /dev/null; then
        echo "Using the Conda environment: $(basename "$CONDA_PREFIX")"
        source activate "$(basename "$CONDA_PREFIX")"
    else
        echo "No Python virtual or Conda environment is active. Running the script in the base environment."
    fi
else
    echo "cloudbandPy is not installed. Please install it before running this script."
    exit 1
fi


# We need to have access to configuration files
# Check if the CLOUDBANDPY_DIR environment variable is set
if [[ -z "${CLOUDBANDPY_DIR}" ]]; then
    echo "The CLOUDBANDPY_DIR environment variable is not set. Please set it to your cloudbandPy directory path."
    exit 1
else
    echo "Using cloudbandPy directory: ${CLOUDBANDPY_DIR}"
fi
export CLOUDBANDPY_DIR=/path/to/your/cloudbandPy


# For temporary config files. we create one config file per year to save memory (instead of loading 43 years of reanalysis)
tmpdir_config=~/tmp
[[ ! -d "${tmpdir_config}" ]] && mkdir "${tmpdir_config}"

# Select the domain(s)
declare -a domains=("southPacific" "northPacific" "southIndianOcean" "southAtlantic" "southernhemisphere" "northernhemisphere")

for domain in "${domains[@]}"; do
    echo "${domain}"

    configname=config_cbworkflow_"${domain}"
    configpath="${CLOUDBANDPY_DIR}"/config/"${configname}".yml

    years=({1959..2022..1})

    echo "${years["${SLURM_ARRAY_TASK_ID}"]}"
    outfil="${tmpdir_config}"/"${configname}"_"${years["${SLURM_ARRAY_TASK_ID}"]}".yml
    old=2016 # check the start/end year
    new="${years["${SLURM_ARRAY_TASK_ID}"]}"
    sed "s|${old}|${new}|g" "${configpath}" >"${outfil}"
    sed -i "s|save_cloudbands_netcdf: .*|save_cloudbands_netcdf: True|g" "${outfil}"

    configfilename="${configname}"_"${years["${SLURM_ARRAY_TASK_ID}"]}".yml
    configpath="${tmpdir_config}"/"${configfilename}"

    echo "${CLOUDBANDPY_DIR}" "${configpath}"

    python "${CLOUDBANDPY_DIR}"/runscripts/run.py "${configpath}"

done
