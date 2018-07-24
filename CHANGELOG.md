# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## Unreleased
### Changed
- Datasets downloaded as XLSX files will now have timestamp, timestampz and
date type columns recognized as dates in Excel
## 1.2.1 - 2018-07-04
### Fixed
- Fixed an issue where a resources displayname would be truncated to a max
length of 50. See work item #46162 
