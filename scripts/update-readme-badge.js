#!/usr/bin/env node
/**
 * Update version badge in README.md
 * Looks for: ![Version](https://img.shields.io/badge/version-...)
 * Run: node scripts/update-readme-badge.js
 */

const fs = require('fs');
const path = require('path');

const README_FILE = path.join(__dirname, '..', 'README.md');

function getCurrentVersion() {
  const pkg = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'package.json'), 'utf8'));
  return pkg.version;
}

function updateReadme(version) {
  if (!fs.existsSync(README_FILE)) {
    console.log('ℹ️  README.md not found, skipping badge update');
    return;
  }

  let content = fs.readFileSync(README_FILE, 'utf8');

  // Update various badge formats
  const patterns = [
    // Shields.io badge format
    /!\[Version\]\(https:\/\/img\.shields\.io\/badge\/version-[^)]+\)/g,
    /\[!\[Version\]\(https:\/\/img\.shields\.io\/badge\/version-[^)]+\)\]\([^)]+\)/g,
    // Plain text version
    /version\s+[0-9]+\.[0-9]+\.[0-9]+(\.[0-9]+)?/gi
  ];

  let updated = false;

  // Try shields.io badge first
  if (content.match(patterns[0]) || content.match(patterns[1])) {
    const newBadge = `![Version](https://img.shields.io/badge/version-${version}-blue)`;
    const newBadgeLinked = `[![Version](https://img.shields.io/badge/version-${version}-blue)](https://github.com/oooAHOYooo/ahoy-little-platform/releases)`;

    content = content.replace(patterns[0], newBadge);
    content = content.replace(patterns[1], newBadgeLinked);
    updated = true;
  }

  if (updated) {
    fs.writeFileSync(README_FILE, content);
    console.log(`✅ Updated README.md version badge to v${version}`);
  } else {
    console.log(`ℹ️  No version badge found in README.md`);
  }
}

const version = getCurrentVersion();
updateReadme(version);
