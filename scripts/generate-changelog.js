#!/usr/bin/env node
/**
 * Generate CHANGELOG.md from git commit history
 * Parses commits since last tag, organizes by type (feat/fix/etc)
 * Run: node scripts/generate-changelog.js
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const CHANGELOG_FILE = path.join(__dirname, '..', 'CHANGELOG.md');

function getLastTag() {
  try {
    return execSync('git describe --tags --abbrev=0', { encoding: 'utf8' }).trim();
  } catch {
    return null;
  }
}

function getCommitsSinceTag(tag) {
  const cmd = tag
    ? `git log ${tag}..HEAD --pretty=format:"%h|%s|%b"`
    : 'git log --pretty=format:"%h|%s|%b" | head -50';

  try {
    const output = execSync(cmd, { encoding: 'utf8' });
    return output
      .split('\n')
      .filter(Boolean)
      .map(line => {
        const [hash, subject] = line.split('|');
        return { hash: hash.trim(), subject: subject.trim() };
      });
  } catch {
    return [];
  }
}

function categorizeCommit(subject) {
  const lower = subject.toLowerCase();
  if (subject.match(/^feat(\(.+\))?[:(]/i)) return 'Features';
  if (subject.match(/^fix(\(.+\))?[:(]/i)) return 'Fixes';
  if (subject.match(/BREAKING CHANGE/i)) return 'Breaking Changes';
  if (subject.match(/^perf(\(.+\))?[:(]/i)) return 'Performance';
  if (subject.match(/^refactor(\(.+\))?[:(]/i)) return 'Refactoring';
  if (subject.match(/^docs?(\(.+\))?[:(]/i)) return 'Documentation';
  if (subject.match(/^style(\(.+\))?[:(]/i)) return 'Styling';
  if (subject.match(/^test(\(.+\))?[:(]/i)) return 'Tests';
  if (subject.match(/^chore(\(.+\))?[:(]/i)) return 'Maintenance';
  return 'Other';
}

function formatCommitMessage(subject) {
  // Remove conventional commit prefix for cleaner display
  return subject.replace(/^(feat|fix|perf|refactor|docs?|style|test|chore)(\(.+\))?:\s*/i, '');
}

function formatChangelogEntry(commits) {
  if (commits.length === 0) return '';

  const categories = {};

  commits.forEach(commit => {
    const category = categorizeCommit(commit.subject);
    if (!categories[category]) categories[category] = [];
    categories[category].push(commit);
  });

  let md = '';
  const order = [
    'Breaking Changes',
    'Features',
    'Fixes',
    'Performance',
    'Refactoring',
    'Documentation',
    'Styling',
    'Tests',
    'Maintenance',
    'Other'
  ];

  order.forEach(category => {
    if (categories[category] && categories[category].length > 0) {
      md += `\n### ${category}\n`;
      categories[category].forEach(commit => {
        const formatted = formatCommitMessage(commit.subject);
        md += `- ${formatted} ([\`${commit.hash}\`](https://github.com/oooAHOYooo/ahoy-little-platform/commit/${commit.hash}))\n`;
      });
    }
  });

  return md;
}

function getCurrentVersion() {
  const pkg = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'package.json'), 'utf8'));
  return pkg.version;
}

function main() {
  const lastTag = getLastTag();
  const currentVersion = getCurrentVersion();
  const commits = getCommitsSinceTag(lastTag);

  if (commits.length === 0 && lastTag) {
    console.log('ℹ️  No new commits since last tag.');
    return;
  }

  const releaseDate = new Date().toISOString().split('T')[0];
  let changelog = `# Changelog\n\n`;
  changelog += `## [${currentVersion}] - ${releaseDate}\n`;
  changelog += formatChangelogEntry(commits);

  // Append existing changelog if it exists
  if (fs.existsSync(CHANGELOG_FILE)) {
    const existing = fs.readFileSync(CHANGELOG_FILE, 'utf8');
    // Remove the header if it exists
    const existingContent = existing.replace(/^# Changelog\n\n/, '');
    changelog += `\n---\n\n${existingContent}`;
  }

  fs.writeFileSync(CHANGELOG_FILE, changelog);
  console.log(`✅ Generated CHANGELOG.md for v${currentVersion}`);
  console.log(`📝 ${commits.length} commits processed`);
}

main();
