# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## Unreleased
## 1.2.3 - 2017-14-09
### Changed
- When previewing data, all rows that have text values is limited to a max
length of the value of the size metadata
- Rephrased wording for the max rows downloaded
## 1.2.2 - 2018-07-30
### Changed
- Datasets downloaded as XLSX files will now have timestamp, timestampz and
date type columns recognized as dates in Excel
## 1.2.1 - 2018-07-04
### Fixed
- Fixed an issue where a resources displayname would be truncated to a max
length of 50. See work item #46162.
- Fixed the spelling in the  danish translation for "What are Organizations".
### Changed
- Changed wording on the dataset filtration button from "Filter & Extract" to
"Filter" (And subsequently also the danish translation) as per Communications
request.
- When previewing a dataset, data in columns named "year" (non-case sensitive)
is truncated to the first 4 characters, from the left.
- When previewing a dataset, data in columns named "month" (non-case sensitive)
is truncated to the first 7 characters, from the left.
