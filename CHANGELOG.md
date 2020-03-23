# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2020-03-24

	- The Readme mentions test_requirements.txt for installing test modules
	- More checks concerning the content (dates with start and end
	date exclusive) that may result in a ValidationError exception
	- Added Makefile for keeping the important operations together

### Changed

	- The generation af a unique OFX id did only return a counter in
	case of duplicates
	- The Readme mentions now my fork of the ofxstatement instead of
	https://github.com/kedder/ofxstatement.git
	- The __about__.py file outputs the version number and that is
	used in the Makefile
	- The Makefile depends now on GNU make for tagging a release

## [1.0.1] - 2020-03-16

### Added

	- Added poppler library to the instructions.

### Changed

	- The date will now be the accounting date (DATE COMPTA) instead of operation date (DATE OPERATION).
	- Handling of 29 february improved
	- Improved handling of graphics in the PDF which transforms to a
	description starting with F and whitespace.
	- The BIC is also recognized if the line does not end with a BIC
	followed by only whitespace (hence BIC<ws><number><ws><.+> is now
	allowed)
	- Better determination of the statement header.

## [1.0.0] - 2020-03-15

### Added

	- Converting the French BanquePopulaire PDFs to an OFX file.
