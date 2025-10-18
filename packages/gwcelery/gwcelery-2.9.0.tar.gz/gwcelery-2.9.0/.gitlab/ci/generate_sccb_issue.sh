#!/bin/bash

# Generate SCCB issue description from template and create GitLab issue
# This script replicates the functionality of the original SCCB workflow template

set -e

# Configuration variables
PROJECT="computing/sccb"

# Get metadata for project
VERSION="$(python -c "from build.util import project_wheel_metadata; print(project_wheel_metadata('.')[\"Version\"])")"
export VERSION
CHANGES_FILENAME="$(echo CHANGES.*)"
export CHANGES_FILENAME

# Version comparison logic to find last version (handle v prefix and newlines)
LAST_VERSION="$(git tag -l |
python -c 'from packaging.version import Version;
import sys;
current_version = Version(sys.argv[1]);
versions = [];
for line in sys.stdin:
    line = line.strip();
    if line.startswith("v"):
        try:
            versions.append(Version(line[1:]));
        except:
            pass;
    else:
        try:
            versions.append(Version(line));
        except:
            pass;
matching_versions = [v for v in versions if v < current_version];
print(max(matching_versions) if matching_versions else "")' "$VERSION" 2>/dev/null || echo "")"
export LAST_VERSION

MAJOR_MINOR_VERSION=$(echo "$VERSION" | cut -d . -f 1,2)
export MAJOR_MINOR_VERSION
PATCH_VERSION=$(echo "$VERSION" | cut -d . -f 3)
LAST_MAJOR_MINOR_VERSION=$(echo "$LAST_VERSION" | cut -d . -f 1,2)
export LAST_MAJOR_MINOR_VERSION
TITLE="$CI_PROJECT_NAME-$VERSION"

PROJECT_SLUG="$(
python -c 'import urllib.parse, sys;
print(urllib.parse.quote(sys.argv[1], safe=""))' "$PROJECT"
)"

# Process template to generate issue description using Jinja2
python ./.gitlab/ci/render_sccb_template.py

echo "SCCB Issue Title: $TITLE"
echo "Generated description saved to: rendered_sccb_template.md"

# Create issue if this is a tagged build with numeric patch version
if [ -n "$CI_COMMIT_TAG" ] && [[ $PATCH_VERSION =~ ^[0-9]+$ ]]; then
    echo "Creating SCCB issue..."
    curl --silent --show-error --fail \
    --request POST --header "Private-Token: $GITLAB_ACCESS_TOKEN" \
    --data-urlencode "title=$TITLE" \
    --data-urlencode "description@rendered_sccb_template.md" \
    "$CI_API_V4_URL/projects/$PROJECT_SLUG/issues"
    echo "SCCB issue created successfully"
else
    echo "Not creating issue - either not a tag or invalid patch version"
    echo "CI_COMMIT_TAG: ${CI_COMMIT_TAG:-'(not set)'}"
    echo "PATCH_VERSION: $PATCH_VERSION"
fi
