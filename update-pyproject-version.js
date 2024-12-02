const fs = require('fs');
const path = require('path');

const updatePyprojectVersion = (version) => {
  const filePath = path.resolve(__dirname, 'pyproject.toml');
  let pyproject = fs.readFileSync(filePath, 'utf8');
  pyproject = pyproject.replace(/version = ".*"/, `version = "${version}"`);
  fs.writeFileSync(filePath, pyproject, 'utf8');
  console.log(`Updated pyproject.toml to version ${version}`);
};

const version = process.argv[2];
if (!version) {
  console.error('Version argument is required');
  process.exit(1);
}

updatePyprojectVersion(version);
