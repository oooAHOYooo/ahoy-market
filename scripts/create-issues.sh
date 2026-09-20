#!/bin/bash
# create-issues.sh - quickly create multiple GitHub issues from natural language descriptions
# Usage: bash scripts/create-issues.sh "mobile=padding on shows" "desktop=events filtering"

set -e

if [ $# -eq 0 ]; then
  echo "Usage: bash scripts/create-issues.sh <issue1> <issue2> ..."
  echo "Example: bash scripts/create-issues.sh \"mobile=increase padding on shows\" \"desktop=better events filtering\""
  exit 1
fi

echo "📝 Creating $# issues..."
created=0

for issue in "$@"; do
  # Parse "platform=description" format
  platform=$(echo "$issue" | cut -d= -f1 | xargs)
  description=$(echo "$issue" | cut -d= -f2- | xargs)

  if [ -z "$platform" ] || [ -z "$description" ]; then
    echo "⚠️  Skipping invalid: $issue (use format: platform=description)"
    continue
  fi

  # Create the issue with platform label
  gh issue create \
    --title "$description" \
    --body "**Platform:** $platform" \
    --label "$platform" \
    --assignee @me \
    --no-editor

  echo "✅ [$platform] $description"
  ((created++))
done

echo ""
echo "🎉 Created $created issue(s)!"
