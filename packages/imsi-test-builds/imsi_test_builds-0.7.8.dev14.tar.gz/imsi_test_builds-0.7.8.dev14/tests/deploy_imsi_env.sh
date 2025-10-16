#!/bin/bash

# ---
# This script creates a Python virtual environment using uv
# and installs a specific git tag or branch from a repository into it.
# Usage: ./deploy_imsi_env.sh [python_version] [tag_or_branch] [deploy_path]
# Defaults are taken from environment variables if arguments are not provided.
# ---

# 1. Parse command line arguments or fall back to environment variables
PYTHON_VER="${1:-${IMSI_DEPLOYED_PYTHON_VER}}"
TAG_OR_BRANCH="${2:-${CI_COMMIT_TAG}}"
DEPLOY_PATH="${3:-${IMSI_DEPLOY_PATH}}"

# 2. Generate the environment name based on variables and the current date
CURRENT_DATE=$(date +%Y-%m-%d)
ENV_NAME="pyenv_${PYTHON_VER}_imsi_${TAG_OR_BRANCH}_${CURRENT_DATE}"

# 3. Create the virtual environment
echo "Creating Python ${PYTHON_VER} environment named '$ENV_NAME'..."
${UV_BINARY} venv "$ENV_NAME" -p "python${PYTHON_VER}"

# 4. Install the package directly into the newly created environment
echo "Installing '${TAG_OR_BRANCH}' from '${CI_PROJECT_DIR}'..."
${UV_BINARY} pip install --python "$ENV_NAME/bin/python" "${CI_PROJECT_DIR}"

# 5. Softlink the new environment to 'latest'
ln -sfn "$ENV_NAME" "${DEPLOY_PATH}/latest"

# 6. Print success message
echo ""
echo "✅ Setup complete."
echo "To activate the new environment, run:"
echo "source $ENV_NAME/bin/activate"
