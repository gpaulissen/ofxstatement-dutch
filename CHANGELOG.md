# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.3.3] - 2022-01-05

### Changed

  - Build and test behaviour reviewed

## [1.3.2] - 2020-08-02

### Removed

  - Dependency of pdftotext.

## [1.3.1] - 2020-08-01

### Changed

  - Layout of the README improved.
  - Contents of this CHANGELOG for version 1.3.0.

## [1.3.0] - 2020-08-01

### Added:

  - Added ability to parse ING balance statements.

### Changed

  - Improved installation guide using Miniconda3
  - Improved code quality by using pycodestyle and Python typing module

## [1.2.1] - 2020-05-01

### Changed

  - Fixed bug for KNAB converter when counterparty is empty (for
  interest for example)

## [1.2.0] - 2020-03-30

### Added

  - Added converter for:
    * KNAB Online Bank, The Netherlands, CSV (https://www.knab.nl/).

### Changed

  - Enhanced header handling for ING and DEGIRO.
  - Enhanced documentation.

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

## [1.0.1] - 2020-03-16

### Changed

  - Added poppler library to the instructions.
  - Readme enhanced.

## [1.0.0] - 2020-03-15

### Added

  - First version to convert:
    * ICSCards, The Netherlands, PDF (https://icscards.nl/)
    * ING bank, The Netherlands, CSV (https://www.ing.nl/)

