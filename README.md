# Python script to retrieve data from Netatmo

## Installation

This package requires the Github version of `lnetatmo` from [philippelt/netatmo-api-python](https://github.com/philippelt/netatmo-api-python):

```bash
pip install git+https://github.com/philippelt/netatmo-api-python.git
```

## Usage

Make a copy of the `env.sh` file and fill in your Netatmo API keys.

Load the environment variables before running the script:

```bash
source YOUR_ENV_FILE.sh
```

## Example

The `netatmo-retrieve.py` script shows an example of how to retrieve data from Netatmo and output it JSON files and CSV files. The script can be run with:

```bash
python netatmo-retrieve.py
```

Edit the script to change the covered area and time range.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
