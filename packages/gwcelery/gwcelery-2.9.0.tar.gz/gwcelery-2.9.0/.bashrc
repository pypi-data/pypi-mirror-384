# .bash_profile for deployment on LSC DataGrid clusters.
# Run at the start of an interactive shell (including a login shell).

# Source global definitions.
if [ -f /etc/bashrc ]; then
    . /etc/bashrc
fi

# Create log directories.
mkdir -p $HOME/.local/state/log

# Add user site directory to the PATH. On Linux, this is usuall ~/.local/bin.
export PATH="$(python3.11 -m site --user-base)/bin${PATH+:${PATH}}"

# Activate virtual environment if stdin is defined and if the venv exists
if [ -t 0 ] && [ -f "$HOME/.venv/bin/activate" ]; then
    source "$HOME/.venv/bin/activate"
fi

# Disable editable installs
export UV_NO_EDITABLE=1

# Disable OpenMP, MKL, and OpenBLAS threading by default.
# In this environment, it will be enabled selectively by processes that use it.
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

# Configuration for GWCelery web applications.
export FLASK_RUN_PORT=5556
export FLASK_URL_PREFIX=/gwcelery
export FLOWER_PORT=5555
export FLOWER_URL_PREFIX=/flower

# GWCelery configuration-dependent instance variables.
case "${USER}" in
emfollow)
    export CELERY_CONFIG_MODULE="gwcelery.conf.production"
    ;;
emfollow-playground)
    export CELERY_CONFIG_MODULE="gwcelery.conf.playground"
    ;;
emfollow-test)
    export CELERY_CONFIG_MODULE="gwcelery.conf.test"
    ;;
emfollow-dev)
    export CELERY_CONFIG_MODULE="gwcelery.conf.dev"
    ;;
esac

# HTGETTOKENOPTS for passing through to condor
export HTGETTOKENOPTS="--vaultserver vault.ligo.org --issuer igwn --role read-cvmfs-${USER} --credkey read-cvmfs-${USER}/robot/${USER}.ligo.caltech.edu --nooidc"

# Don't set HTGETTOKENOPTS on headnode because sometimes we want to run without --nooidc
case "${USER}@${HOSTNAME}" in
emfollow@emfollow.ligo.caltech.edu)
    unset HTGETTOKENOPTS
    ;;
emfollow-playground@emfollow-playground.ligo.caltech.edu)
    unset HTGETTOKENOPTS
    ;;
emfollow-test@emfollow-test.ligo.caltech.edu)
    unset HTGETTOKENOPTS
    ;;
emfollow-dev@emfollow-dev.ligo.caltech.edu)
    unset HTGETTOKENOPTS
    ;;
esac
