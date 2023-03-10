#!/bin/bash
#SBATCH --job-name RunCBDmultiyear
#SBATCH --chdir /scratch/rpilon/log
#SBATCH --nodes 1
#SBATCH --ntasks-per-node 1
#SBATCH --cpus-per-task 1
#SBATCH --mem 16G
#SBATCH --time 03:00:00
#SBATCH --array=0-61

module purge
module load gcc python
module load geos proj
source /work/FAC/FGSE/IDYST/ddomeise/default/romain/ProdEnvPy3.9/bin/activate

DIR=/users/rpilon
cd "${DIR}" || return

# Set paths
# for code source
srcdir=./cloudbandPy
# for temporary config files. we create one config file per year to save memory (instead of loading 43 years of reanalysis)
tmpdir_config=./tmp

[[ ! -d "${tmpdir_config}" ]] &&  mkdir "${tmpdir_config}"

# Copy original config file into tmp directory and change its start/end year
domain=southPacific

configname=config_cbworkflow_"${domain}"
configpath="${srcdir}"/config/"${configname}".yml

years=({1960..2021..1})

for iyear in "${years[@]}"; do
    outfil="${tmpdir_config}"/"${configname}"_"${iyear}".yml
    old=2016 # check the start/end year
    new=${iyear}
    sed "s|${old}|${new}|g" "${configpath}" > "${outfil}"
done


configfilename="${configname}"_"${years["${SLURM_ARRAY_TASK_ID}"]}".yml
configpath="${tmpdir_config}"/"${configfilename}"

echo "${srcdir}" "${configpath}"

python "${srcdir}"/src/main.py "${configpath}"


