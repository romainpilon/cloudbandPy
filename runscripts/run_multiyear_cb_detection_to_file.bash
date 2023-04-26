#!/bin/bash
#SBATCH --job-name RunCBDmultiyear
#SBATCH --chdir /scratch/rpilon/log
#SBATCH --nodes 1
#SBATCH --ntasks-per-node 1
#SBATCH --cpus-per-task 1
#SBATCH --mem 16G
#SBATCH --time 03:00:00
#SBATCH --array=0-62

module purge
module load gcc python
module load geos proj
source /work/FAC/FGSE/IDYST/ddomeise/default/romain/ProdEnvPy3.9/bin/activate

DIR=/users/rpilon
cd "${DIR}" || return

# Set paths
# for code source
srcdir=/users/rpilon/codes/unil/CloudBandDetection # FIXME
# for temporary config files. we create one config file per year to save memory (instead of loading 43 years of reanalysis)
tmpdir_config=/users/rpilon/tmp # FIXME
[[ ! -d "${tmpdir_config}" ]] && mkdir "${tmpdir_config}"

# Select the domain(s)
# declare -a domains=("southPacific" "northPacific" "southAfricaIO" "southAtlantic")
declare -a domains=("northernhemisphere" "southernhemisphere")

# Iterate the string array using for loop
for domain in "${domains[@]}"; do
    echo "${domain}"
    # domain=southPacific

    configname=config_cbworkflow_"${domain}"
    configpath="${srcdir}"/config/"${configname}".yml

    years=({1959..2021..1})

    for iyear in "${years[@]}"; do
        outfil="${tmpdir_config}"/"${configname}"_"${iyear}".yml
        old=2016 # check the start/end year
        new=${iyear}
        sed "s|${old}|${new}|g" "${configpath}" >"${outfil}"
    done

    configfilename="${configname}"_"${years["${SLURM_ARRAY_TASK_ID}"]}".yml
    configpath="${tmpdir_config}"/"${configfilename}"

    echo "${srcdir}" "${configpath}"

    python "${srcdir}"/src/main.py "${configpath}"

done
