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

The PDF is converted using the
[pdftotext](https://pypi.org/project/pdftotext/) utility.

## Installation

### Preconditions

You have to install the poppler library first, see
[pdftotext](https://pypi.org/project/pdftotext/)

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

#### ICSCards

Use something like this:
```
$ ofxstatement convert -t nl-icscards <file>.pdf <file>.ofx
```

Or you can convert the PDF yourself and supply the text as input:

```
$ pdftotext -layout <file>.pdf <file>.txt
$ ofxstatement convert -t nl-icscards <file>.txt <file>.ofx
```

#### ING bank

Use something like this:

```
$ ofxstatement convert -t nl-ing <file>.csv <file>.ofx
```

