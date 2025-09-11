#!/bin/bash


# Initialize git-lfs and fetch/checkout LFS files
git lfs install
git lfs fetch --all
git lfs checkout


pip install --upgrade pip gunicorn
