# ChatGPT Working Notes — Vision Bridge

## Purpose
Persistent working notes for the GitHub image-to-artifact → real-file → vision workflow. Read this file before continuing this workflow so the user does not need to repeat the setup history.

## Repository
- GitHub repository: 19REKo91/assistant-cloud-memory
- Default branch: main
- User works from an Android phone, so operational links should be suitable for opening in Chrome.

## Proven successful method
The successful 18/9 method was:
1. PNG is uploaded/placed in GitHub.
2. GitHub Actions processes the image.
3. actions/upload-artifact@v4 creates an artifact.
4. Download the artifact ZIP.
5. The downloaded artifact contains a real PNG file.
6. The real PNG can then be used for image/vision analysis.

The older successful artifact was named deepseek-image.

## Current generic workflow
Workflow: .github/workflows/image-to-artifact.yml

Its intended behavior:
- Automatically runs when an image file (.png, .jpg, .jpeg, .webp) is pushed to main.
- Detects image files changed by the latest commit.
- Can also be run manually with an optional image_path.
- Stages selected images and uploads them as artifact image-latest.
- Artifact retention is 7 days.
- Do not hard-code a specific DeepSeek filename into this generic workflow.

## Important distinction
There are multiple image workflows in this repository:
- image-to-artifact.yml = generic GitHub image → Actions artifact workflow.
- github-to-dropbox-vision-bridge.yml = older/specific Dropbox bridge and is intentionally separate.
- gemini-vision-bridge.yml = Gemini/Dropbox-related workflow.
Do not replace or confuse these workflows unless the user explicitly asks.

## Current state
- Generic workflow was added and then corrected.
- Latest known commit that updated it: bd76ae9c2e5aaca247f06e87303e37b4cd8dddb3.
- The generic workflow has not yet been validated end-to-end with a newly uploaded image after the correction.
- Next task: upload/use a new test image, run the generic workflow, inspect the workflow run, locate artifact image-latest, download it, and verify that the artifact contains a real image file.

## Operating rule
When continuing this project:
- Do not make the user repeat the history above.
- Verify repository state before changing files.
- Prefer the generic artifact workflow for the GitHub → real image test.
- Do not delete the old successful workflow or its artifacts merely to simplify things.
- If a workflow fails, inspect the job/logs and fix the actual cause before changing architecture.