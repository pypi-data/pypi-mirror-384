#!/bin/bash

# Check if an argument is provided
if [ $# -eq 0 ]; then
    echo "Please provide an argument: patch, minor, major, or custom-branch"
    exit 1
fi

INIT_FILE="src/sagemaker_studio_dataengineering_extensions/__init__.py"
META_YAML_FILE="meta.yaml"

# Get the version type from the argument
VERSION_TYPE=$1

# Function to execute the publish commands
publish() {
    local type=$1
    git pull --rebase
    if [ -n "$type" ]; then
        NEW_VERSION=$(semantic-release version --$type --print)
        semantic-release version --$type
    else
        NEW_VERSION=$(semantic-release version --print)
        semantic-release version
    fi
    # clear build number
    sed -i '' "s/__version__=\".*\"/__version__=\"$NEW_VERSION\"/" "$INIT_FILE"
    sed -i '' "s/set version = \".*\"/set version = \"$NEW_VERSION\"/" "$META_YAML_FILE"
    git add $INIT_FILE $META_YAML_FILE
    # Get the last commit message
    LAST_COMMIT_MSG=$(git log -1 --pretty=%B)

    # Amend the previous commit
    git commit --amend -m "$LAST_COMMIT_MSG"

    cr --new-review
 
    git push -d origin $NEW_VERSION

    # Remove the existing tag locally
    git tag -d $NEW_VERSION

    # Tag the last commit with the same tag name
    git tag $NEW_VERSION
    
    git push origin $NEW_VERSION
}

# Execute the appropriate commands based on the version type
case $VERSION_TYPE in
    patch)
        publish "patch"
        ;;
    minor)
        publish "minor"
        ;;
    major)
        publish "major"
        ;;
    custom-branch)
        publish
        ;;
    *)
        echo "Invalid argument. Please use patch, minor, major, or custom-branch."
        exit 1
        ;;
esac

echo "Version updated to $NEW_VERSION in $INIT_FILE and $META_YAML_FILE"

# Optional: Display the updated line
grep "__version__" "$INIT_FILE"
grep "set version" "$META_YAML_FILE"
