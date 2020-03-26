# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2020-03-26

### Added

	- Added converter for:
		* DEGIRO trader platform, The Netherlands, CSV (https://www.degiro.nl/).
	- Added reference to the Changelog in the Readme.
	- The Readme mentions test_requirements.txt for installing test modules.
	- More checks concerning the content (dates with start and end
	date exclusive) that may result in a ValidationError exception.
	- Added Makefile for keeping the important operations together.

### Changed

	- The generation af a unique OFX id did only return a counter in
	case of duplicates.
	- The Readme mentions now my fork of the ofxstatement instead of
	https://github.com/kedder/ofxstatement.git.
	- The __about__.py file outputs the version number and that is
	used in the Makefile.
	- The Makefile depends now on GNU make for tagging a release.
	- MANIFEST.in now includes the Makefile and CHANGELOG.md.
	- Code refactoring.
	- Changed bank id (BIC) for ING from INGBNL2AXXX to INGBNL2A.
	- Added poppler library to the instructions.
	- Readme enhanced.

## [1.0.0] - 2020-03-15

### Added

	- First version to convert:
		* ICSCards, The Netherlands, PDF (https://icscards.nl/)
		* ING bank, The Netherlands, CSV (https://www.ing.nl/)

