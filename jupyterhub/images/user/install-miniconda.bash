#!/bin/bash
# Set up
# This downloads and installs a pinned version of miniconda
set -ex

export MAMBA_ROOT_PREFIX=/tmp/conda
export MAMBA_ALWAYS_YES=true

wget -qO- https://micro.mamba.pm/api/micromamba/linux-64/1.4.2 | tar --directory /tmp -xvj bin/micromamba

echo "installing root env:"
time /tmp/bin/micromamba create -p "${CONDA_DIR}" -f /tmp/conda.lock

# clear out temporary files
rm -rf /tmp/bin

source "$CONDA_DIR"/etc/profile.d/conda.sh
conda list

# Clean things out!
# don't clean conda packages when using mount cache
# conda clean -pity

# Remove some large files to reduce image size
echo "Usage before:"
du -hs "$CONDA_DIR"
for d in "share/apbs/examples" \
    "share/apbs/tools/matlab" \
    "share/jupyterhub/static/components/requirejs/bin" \
    "x86_64-conda-linux-gnu/sysroot/usr/lib64/locale/locale-archive.tmpl" \
    ; do
    fullpath="$CONDA_DIR/$d"
    echo "Removing ${fullpath}" $(du -hs "${fullpath}")
    rm -rf "${fullpath}"
done

# remove most static libs, but not everywhere
rm -vf "${CONDA_DIR}/lib/*.a"
# find "${CONDA_DIR}" -name '*.a' -exec rm -vf {} \;

# strip boost headers
# this is 100MB of just headers (?!)
# but at least some seem to be needed
# rm -rf "${CONDA_DIR}"/include/boost

# strip some mkl (more?)
rm -vf "${CONDA_DIR}"/lib/libmkl_avx.*
rm -vf "${CONDA_DIR}"/lib/libmkl_avx512*
rm -vf "${CONDA_DIR}"/lib/libmkl_blacs*
rm -vf "${CONDA_DIR}"/lib/libmkl_mc*
rm -vf "${CONDA_DIR}"/lib/libmkl_pgi*
rm -vf "${CONDA_DIR}"/lib/libmkl_scalapack*
rm -vf "${CONDA_DIR}"/lib/libmkl_tbb*
rm -vf "${CONDA_DIR}"/lib/libmkl_vml_mc*
rm -vf "${CONDA_DIR}"/lib/libmkl_vml_avx.*
rm -vf "${CONDA_DIR}"/lib/libmkl_vml_avx512*

# strip dylibs
find "${CONDA_DIR}"/lib -size +1000k -name '*.so' -type f -exec strip -s {} \;
find "${CONDA_DIR}"/lib -size +1000k -name '*.so.*' -type f -exec strip -s {} \;

# strip exes
find "${CONDA_DIR}"/bin -size +1000k -exec strip -s {} \;


# discard sourcemaps
for pat in '*.map' '*.min.map'; do
    find "${CONDA_DIR}" -name "$pat" -exec rm -vf {} \;
done

echo "Usage after:"
du -hs "$CONDA_DIR"

chown -R "$NB_USER" "${CONDA_DIR}"
