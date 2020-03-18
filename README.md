# ofxstatement-dutch 

This project provides custom
[ofxstatement](https://github.com/kedder/ofxstatement) plugins for these dutch
financial institutions:
- DEGIRO trader platform, The Netherlands, CSV (https://www.degiro.nl/)
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

To run the tests from the development version you can use the py.test command:

```
$ py.test
```

You may need to install the required test packages first:

```
$ pip install -r test_requirements.txt
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
  nl-degiro        DEGIRO trader platform, The Netherlands, CSV (https://www.degiro.nl/)
  nl-icscards      ICSCards, The Netherlands, PDF (https://icscards.nl/)
  nl-ing           ING Bank, The Netherlands, CSV (https://www.ing.nl/)
  ...

```

### Convert

#### DEGIRO trader platform

The DEGIRO files do not only contain money statements but also the whole
security transaction history. This tool just emits the money statements coming
from or going to your associated (other) bank account. To be more specific the
deposits (description like "Storting" or "iDEAL storting") and transfers
("Terugstorting"). Maybe in the future the security transaction will be
emitted too, but currently
[ofxstatement](https://github.com/kedder/ofxstatement) only processes money
information.

See also the section configuration below.

Use something like this:

```
$ ofxstatement convert -t <configuration name> <file>.csv <file>.ofx
```

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

### Configuration

For DEGIRO you need to set an account id, since the statement files does not
contain account information.

```
$ ofxstatement edit-config
```

This is a sample configuration (do not forget to specify the plugin for each section):

```
[degiro:account1]
plugin = nl-degiro
account_id = account1

[degiro:account2]
plugin = nl-degiro
account_id = account2

```

