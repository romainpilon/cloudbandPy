#!/bin/bash
#SBATCH --job-name RunCBDmultiyear
#SBATCH --chdir /scratch/rpilon/log
#SBATCH --nodes 1
#SBATCH --ntasks-per-node 1
#SBATCH --cpus-per-task 1
#SBATCH --mem 64G
#SBATCH --time 01:00:00
#SBATCH --array=0-62

module purge
module load gcc python
module load geos proj
source /work/FAC/FGSE/IDYST/ddomeise/default/romain/ProdEnvPy3.9/bin/activate

DIR=/users/rpilon
cd "${DIR}" || return

# Set paths
# for code source
srcdir=/users/rpilon/codes/unil/cloudbandPy # TODO
# for temporary config files. we create one config file per year to save memory (instead of loading 43 years of reanalysis)
tmpdir_config=/users/rpilon/tmp # TODO
[[ ! -d "${tmpdir_config}" ]] && mkdir "${tmpdir_config}"

# Select the domain(s)
# declare -a domains=("southPacific" "northPacific" "southAfricaIO" "southAtlantic")
domain="northernhemisphere"
# Iterate the string array using for loop
# for domain in "${domains[@]}"; do
echo "${domain}"
# domain=southPacific

configname=config_cbworkflow_"${domain}"
configpath="${srcdir}"/config/"${configname}".yml

years=({1959..2021..1})

echo "${years["${SLURM_ARRAY_TASK_ID}"]}"
outfil="${tmpdir_config}"/"${configname}"_"${years["${SLURM_ARRAY_TASK_ID}"]}".yml
old=2016 # check the start/end year
new="${years["${SLURM_ARRAY_TASK_ID}"]}"
sed "s|${old}|${new}|g" "${configpath}" >"${outfil}"

configfilename="${configname}"_"${years["${SLURM_ARRAY_TASK_ID}"]}".yml
configpath="${tmpdir_config}"/"${configfilename}"

echo "${srcdir}" "${configpath}"

python "${srcdir}"/src/cloudbandpy/run.py "${configpath}"

# done
