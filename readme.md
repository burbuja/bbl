# bbl - A simple script that helps you create translations
## Usage
```bash
bbl.py  <script_name>
bbl.py  <script_name> <translation_source>
```
## Examples for Python version
```bash
./bbl.py  netbox-community/netbox
./bbl.py  netbox-community/netbox your_local_file.po
./bbl.py  netbox-community/netbox https://example.com/glotpress/projects/netbox/es-cl/default/
```
## Warning for Python version
The main goal is to show that NetBox can be translated, but this script may break the database. Please don't use it under production environments!
## Examples for PHP version
```bash
./bbl.php get opencart -d /path/to/opencart
./bbl.php merge opencart -d /path/to/opencart -p /path/to/opencart.po -l es-cl
./bbl.php merge opencart -d /path/to/opencart -p https://example.com/glotpress/projects/opencart/es-cl/default/ -l es-cl
```
## License
This software is licensed under LGPLv2+.
