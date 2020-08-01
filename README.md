# ofxstatement-dutch 

This project provides custom
[ofxstatement](https://github.com/kedder/ofxstatement) plugins for these dutch
financial institutions:
- DEGIRO trader platform, The Netherlands, CSV (https://www.degiro.nl/)
- ICSCards, The Netherlands, PDF (https://icscards.nl/)
- ING bank, The Netherlands, CSV (https://www.ing.nl/)
- KNAB Online Bank, The Netherlands, CSV (https://www.knab.nl/)

`ofxstatement` is a tool to convert a proprietary bank statement to OFX
format, suitable for importing into programs like GnuCash or Beancount. The
plugin for ofxstatement parses the bank statement and produces a common data
structure, that is then formatted into an OFX file.

The PDF is converted using the
[pdftotext](https://pypi.org/project/pdftotext/) utility.

## Installation using Miniconda (minimal conda)

This is a quick start guide meant for users on a Windows 10 platform.

These are the steps:

### 1. Install [Miniconda for Python 3.x](https://docs.conda.io/en/latest/miniconda.html)

### 2. Start the Anaconda prompt

Type Anaconda in the search box next to the Windows Start icon in the bottom left of your screen and click the Anaconda Prompt (Miniconda3).
A command line box will open now with (base) as the prompt.

### 3. Create an ofxstatement environment

In the command line box type "conda create -n ofxstatement":
```bash
(base) conda create -n ofxstatement
```
Please note that (base) is the command prompt, not a command to type.

### 4. Switch to the ofxstatement environment and show the installed packages (should be empty the first time)

```bash
(base) activate ofxstatement
(ofxstatement) conda list
```

### 5. Install Python in this environment

```bash
(ofxstatement) conda install python
```

### 6. Verify the location of pip

```bash
(ofxstatement) where pip
```
This should show something like C:\Users\%USERNAME%\Miniconda3\envs\ofxstatement\Scripts\pip.exe

### 7. Install ofxstatement-dutch

```bash
(ofxstatement) pip install ofxstatement-dutch
```

### 8. (optional) Install the Poppler library

Only if you need to read PDF files (ICSCards for example):
```bash
(ofxstatement) conda install -c conda-forge poppler
```

### 9. Test the installation

Now a small test to see everything works if you have a KNAB CSV file:

```bash
(ofxstatement) ofxstatement convert -t nl-knab "<CSV file>" -
```

The dash (-) at the end of the command ensures that the OFX output will be
sent to the terminal and not to a file.  The double quotes are needed for
files with spaces in its name like
"Knab transactieoverzicht spaarrekening XXXXXXXX - 2020-01-01 - 2020-05-01.csv".

### 10. Launching ofxstatement

Please remember to always start the Anaconda prompt and to activate the
ofxstatement environment first before launching ofxstatement itself, since it
is only installed in that Conda environment.

You may create a shortcut to combine both. The target of your shortcut should be something like:
```
C:\Windows\System32\cmd.exe /k C:\Users\%USERNAME%\Miniconda3\condabin\activate.bat ofxstatement
```

Please continue with the "Usage" section below.

## Installation

This section is meant for people who do not want to follow the "Installation
using Miniconda (minimal conda)" section above.

### Preconditions

For converting PDFs you have to install the poppler library first, see
[pdftotext](https://pypi.org/project/pdftotext/).

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
$ git clone https://github.com/gpaulissen/ofxstatement.git
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
  nl-knab          KNAB Online Bank, The Netherlands, CSV (https://www.knab.nl/)
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

#### KNAB Online Bank

Use something like this:

```
$ ofxstatement convert -t nl-knab <file>.csv <file>.ofx
```

### Configuration

For DEGIRO you need to set an account id, since the statement files do not
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

## Change history

See the Changelog (CHANGELOG.md).
