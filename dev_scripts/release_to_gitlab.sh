#!/bin/bash

# Configuration - set these paths according to your setup
GITHUB_REPO_PATH="${HOME}/projects/argo-proxy"
GITLAB_REPO_PATH="${HOME}/projects/argo-proxy-gitlab"
COMMIT_MESSAGE="Sync from dev upstream"

# Ensure both repositories exist
if [ ! -d "$GITHUB_REPO_PATH" ]; then
    echo "GitHub repository path not found: $GITHUB_REPO_PATH"
    exit 1
fi

if [ ! -d "$GITLAB_REPO_PATH" ]; then
    echo "GitLab repository path not found: $GITLAB_REPO_PATH"
    exit 1
fi

# Change to GitLab repo directory
cd "$GITLAB_REPO_PATH" || exit 1

# Ensure GitLab repo is clean (no uncommitted changes)
if [ -n "$(git status --porcelain)" ]; then
    echo "GitLab repository has uncommitted changes. Please commit or stash them first."
    exit 1
fi

# Copy all files from GitHub repo to GitLab repo, excluding .git directory
rsync -av --delete --exclude='.git/' --exclude='dev_scripts/release_to_gitlab.sh' "$GITHUB_REPO_PATH/" "$GITLAB_REPO_PATH/"

# Add all changes to GitLab repo
git add .

# Check if there are any changes to commit
if [ -z "$(git status --porcelain)" ]; then
    echo "No changes to commit - repositories are already in sync."
    exit 0
fi

# Commit the changes
git commit -m "$COMMIT_MESSAGE"
git push
echo "Successfully copied files and created commit in GitLab repository."
