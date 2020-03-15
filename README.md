# ofxstatement-dutch 

This project provides custom
[ofxstatement](https://github.com/kedder/ofxstatement) plugins for these dutch
financial institutions:
- ICSCards, The Netherlands, PDF (https://icscards.nl/)
- ING bank, The Netherlands, CSV (https://www.ing.nl/)

`ofxstatement` is a tool to convert a proprietary bank statement to OFX
format, suitable for importing into programs like GnuCash or Beancount. The
plugin for ofxstatement parses the bank statement and produces a common data
structure, that is then formatted into an OFX file.

## Installation

### Using pip

```
$ pip install ofxstatement-dutch
```

### Development version from source

```
$ git clone https://github.com/gpaulissen/ofxstatement-dutch.git
$ pip install -e .
```

### Troubleshooting

This package depends on ofxstatement with a version at least 0.6.5. This
version may not yet be available in PyPI so install that from source like
this:
```
$ git clone https://github.com/kedder/ofxstatement.git
$ pip install -e .
```

## Test

To run the tests you can use the py.test command:

```
$ py.test
```

## Usage

### Show installed plugins

This shows the all installed plugins, not only those from this package:

```
$ ofxstatement list-plugins
```

You should see at least:

```
The following plugins are available:

  ...
  nl-icscards      ICSCards, The Netherlands, PDF (https://icscards.nl/)
  nl-ing           ING Bank, The Netherlands, CSV (https://www.ing.nl/)
  ...

```

### Convert

Use something like this:

```
$ ofxstatement convert -t nl-ing ING.csv output.ofx
```

or this:

```

$ ofxstatement convert -t nl-icscards ICSCards.pdf output.ofx
```
