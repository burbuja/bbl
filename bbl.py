#!/usr/bin/env python3

import json, os, re, sys, urllib, urllib.request, zipfile
from lxml import etree
from pathlib import Path
from shutil import copyfile

'''
Get arguments and show help if necesary
'''
sw = {
	2: 'get',
	3: 'merge',
}
if sw.get(len(sys.argv)):
	action = sw.get(len(sys.argv))
else:
	print()
	print('Usage:')
	print(str(sys.argv[0]), ' <script_name>')
	print(str(sys.argv[0]), ' <script_name> <translation_source>')
	print()
	print('To get some more information, please visit: https://github.com/burbuja/bbl.')
	sys.exit(1)

'''
Validate if project name is supported
'''
projects = [
	'digitalocean/netbox',
]
project = sys.argv[1]
if project not in projects:
	print('This project name is not supported!')
	sys.exit(1)

'''
Get the version number from GitHub
'''
def getVersion(project):
	f = urllib.request.urlopen('https://github.com/' + project + '/releases/latest')
	c = f.read()
	html = etree.HTML(c)
	etree.tostring(html, pretty_print=True, method='html')
	values = html.xpath("//div[contains(@class,'label-latest')]/div/div/ul/li/a/span/text()")
	version = values[0]

	if version:
		return version
	else:
		url = urllib.request.urlopen("https://api.github.com/repos/digitalocean/netbox/releases/latest")
		data = json.loads(url.read().decode())
		version = data['tag_name']   
		return version

versionString = getVersion(project)
version = versionString.replace('v', '')

print('Fetching the version', version)

'''
Download the zip file from GitHub and uncompress it
'''
fn = 'netbox-' + version + '.zip'
if not Path(fn).is_file():
	print('Downloading the ZIP file.')
	z = urllib.request.urlopen('https://github.com/digitalocean/netbox/archive/' + versionString + '.zip')
	c = z.read()
	f = open(fn, 'wb')  
	f.write(c)
	f.close()
else:
	print('The ZIP file was already downloaded.')

dn = 'netbox-' + version
if not Path(dn).is_dir():
	print('Extracting the files.')
	f = zipfile.ZipFile(fn, 'r')
	f.extractall('.')
	f.close()
else:
	print('The files were already extracted.')

'''
Create a list of the files extracted
'''
fl = []
for root, dirs, files in os.walk(dn, topdown=False):
	for name in files:
		fl.append(os.path.join(root, name))

'''
Declare the patterns
'''
po_patterns = [
	r'msgid\s"(.+)"\nmsgstr\s"(.+)"\n',
]
if project == 'digitalocean/netbox':
	patterns = [
		r'[\s\(]help_text\s?=\s?[\'"]([^\'].+)[\'"][,\n]',
		r'[\s\(]null_label\s?=\s?[\'"]([^\'].+)[\'"][,\n]',
		r'[\s\(]label\s?=\s?[\'"]([^\'].+)[\'"][,\n]',
		r'[\s\(]default_label\s?=\s?[\'"]([^\'].+)[\'"][,\n]',
		r'[\s\(]verbose_name\s?=\s?[\'"]([^\'].+)[\'"][,\n]',
		r'[\s\(]messages\.(?:info)?(?:success)?\((?:.+)?[\'"]([^\"].+)[\'"]',
		r'[\s\(]forms\.ValidationError\("([^\"].+)"\)',
	]
	array_patterns = [
		r'(?s)\slabels\s?=\s?\{\n(.+?)\}',
		r'(?s)\serror_messages\s?=\s?\{\n(.+?)\}',
		r'(?s)\shelp_texts\s?=\s?\{\n(.+?)\}',
		r'(?s)[OBJ_TYPE|COLOR]_CHOICES\s?=\s?\(\n(.+?)\n\)\n',
	]
	in_array_patterns = [
		r'[\s\(][\'"].+?[\'"]:\s?\'([^\'].+)[\'"][,\n]',
		r'\(\'(.+?)\',\s\(\n',
		r'\'\',\s\'(.+?)\'\),\n',
		r',\s\'((?![a-z])[A-Z0-9].+?)\'\),\n',
	]
	html_patterns = [
		r'<a\s.+?>\s?([^(\n|?:{{|<)].+?[^(?:}}|>|\n)])</a>',
		r'<th>\s?([^(\n|?:{{|<)].+?[^(?:}}|>)])</th>',
		r'<th\s.+?>\s?([^(\n|?:{{|<)].+?[^(?:}}|>)])</th>',
		r'<td>\s?([^(\n|?:{{|<|")].+?[^(?:}}|>|")])</td>',
		r'<td\s.+?>\s?([^(\n|?:{{|<|")].+?[^(?:}}|>|")])</td>',
		r'\splaceholder="(.+?)"',
		r'\stitle="([^(?:\.ui\-icon\-|?:{{)].+?)"',
		r'<p(?:\s.+)?>(?!{[{\%])(?!<a)(.+?[^>])(?!</a>)(?!}[\%}])<\/p>',
		r'<h\d(?:\s.+)?>(?!{[{\%])(?!<a)(.+?[^(?:</a>])(?!}[\%}])<\/h\d>',
		r'<button\s?.*?>(?!{{)(.+?[^>])(?!}})</button>',
		r'</span>\s+(.+?[^>])\n\s*?</button>',
		r'</span>\s+(.+?[^>])\n\s*?</a>',
		r'{% block title %}(?!{{)(.+?){% endblock %}',
		r'<title\s?.*?>(?!{{)(.+?)(?!}})</title>',
		r'<label\s?.*?>(?!{{)(.+?)(?!}})</label>',
		r'<strong\s?.*?>(?!{{)(.+?[^>])(?!}})</strong>',
		r'<li(?:.+)?>(?!<a)(?!<span)(?!{{)(.+?[^>])(?!}})</li>',
	]

if action == 'get':
	'''
	Get the strings
	'''
	phrases = []
	for f in fl:
		fn, fe = os.path.splitext(f)
		if fe == '.py' and not 'migrations' in f:
			o = open(f, 'r')
			c = o.read()
			for p in patterns:
				match = re.findall(p, c)
				if not len(match) == 0:
					for m in match:
						if m not in phrases:
							phrases.append(m)		
			for p in array_patterns:
				array_phrases = []
				match = re.findall(p, c)
				if not len(match) == 0:
					for m in match:
						if m not in array_phrases:
							array_phrases.append(m)
				for c in array_phrases:
					for p in in_array_patterns:
						match = re.findall(p, c)
						if not len(match) == 0:
							for m in match:
								if m not in phrases:
									phrases.append(m)
		if fe == '.html' and not 'jquery-ui-' in fn:
			o = open(f, 'r')
			c = o.read()
			for p in html_patterns:
				match = re.findall(p, c)
				if not len(match) == 0:
					for m in match:
						if m not in phrases:
							phrases.append(m)
	print('There are', len(phrases), 'strings obtained.')

	'''
	Write a new PO file
	'''
	po = open('netbox-' + version + '.po', 'w')
	po.write('# Generated by bbl.py\n')
	po.write('msgid ""\n')
	po.write('msgstr ""\n')
	po.write('\n')
	for p in phrases:
		po.write('msgid "' + p.replace('"', '\\"') + '"\n')
		po.write('msgstr ""\n')
		po.write('\n')
	po.close()
	print('The file netbox-' + version + '.po, has been successfully created!')

if action == 'merge':
	'''
	Get the translations
	'''
	po = sys.argv[2]
	if 'http:' == po[:5] or 'https:' == po[:6]:
		o = urllib.request.urlopen(po + 'export-translations/?format=po')
	else:
		o = open(po, 'r', encoding='utf8')
	c = o.read()
	for p in po_patterns:
		m = re.findall(p, c)
	d = dict(m)

	'''
	Create the translated files
	'''
	for f in fl:
		fn, fe = os.path.splitext(f)
		if (fe == '.html' and 'jquery-ui-' in fn) or (fe == '.py' and 'migrations' in f) or fe != '.html' or fe != '.py':
			nf = f.replace('netbox-' + version, 'netbox-translated-' + version)
			os.makedirs(os.path.dirname(nf), exist_ok=True)
			copyfile(f, nf)
			if fe == '.py' and not 'migrations' in f:
				o = open(f, 'r')
				c = o.read()
				for p in patterns:
					matches = re.finditer(p, c)
					for m in matches:
						raw = m.group(0)
						if raw:
							orig = re.findall(p, raw)[0]
							tran = str(d.get(orig)).replace('\'', '\\\'')
							if d.get(orig):
								c = c.replace(raw, raw.replace(orig, tran))
				for ap in array_patterns:
					array_matches = re.finditer(ap, c)
					for am in array_matches:
						array_raw = am.group(0)
						if array_raw:
							for p in in_array_patterns:
								matches = re.finditer(p, array_raw)
								for m in matches:
									raw = m.group(0)
									if raw:
										orig = re.findall(p, raw)[0]
										tran = str(d.get(orig)).replace('\'', '\\\'')
										if d.get(orig):
											array_raw = array_raw.replace(raw, raw.replace(orig, tran))
							array_orig = am.group(0)
							array_tran = array_raw
							c = c.replace(array_orig, array_tran)
				nf = f.replace('netbox-' + version, 'netbox-translated-' + version)
				os.makedirs(os.path.dirname(nf), exist_ok=True)
				w = open(nf, 'w+')
				w.write(c)
				w.close()
			if fe == '.html' and not 'jquery-ui-' in fn:
				o = open(f, 'r')
				c = o.read()
				for p in html_patterns:
					matches = re.finditer(p, c)
					for m in matches:
						raw = m.group(0)
						if raw:
							orig = re.findall(p, raw)[0]
							tran = str(d.get(orig)).replace('"', '\\"')
							if d.get(orig):
								c = c.replace(raw, raw.replace(orig, tran))
				nf = f.replace('netbox-' + version, 'netbox-translated-' + version)
				os.makedirs(os.path.dirname(nf), exist_ok=True)
				w = open(nf, 'w+')
				w.write(c)
				w.close()
	print('The translated files have been successfully saved in the folder netbox-translated-' + version + '.')
