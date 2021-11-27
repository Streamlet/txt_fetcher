#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os, sys, locale, re, urlparse, urllib2, ConfigParser

root_config_file = '.conf'
txt_config_file = '.conf'


class ConfigVarMap:
	def __init__(self, attr, section, option, default):
		self.attr = attr
		self.section = section
		self.option = option
		self.default = default

def ConfigToVar(var, file, map):
	if not os.path.exists(file):
		return False
	parser = ConfigParser.RawConfigParser()
	if len(parser.read(file)) == 0:
		return False
	for item in map:
		if parser.has_option(item.section, item.option):
			if type(item.default) is bool:
				value = parser.getboolean(item.section, item.option)
			elif type(item.default) is int:
				value = parser.getint(item.section, item.option)
			elif type(item.default) is float:
				value = parser.getfloat(item.section, item.option)
			else:
				value = parser.get(item.section, item.option).decode('utf-8')
			setattr(var, item.attr, value)
		else:
			setattr(var, item.attr, item.default)
	return True
		

class RootConfig:
	dataDir = '.'
	def __init__(self):
		ConfigToVar(self, root_config_file, [
		])


class TxtConfig:
	class SummaryConfig:
		url = None
		urlBegin = 0
		urlEnd = 1
		charset = 'utf-8'
		prefix = None
		suffix = None
		pattern = None
		filename = '[{NO}]{NAME}.txt'
		counterLength = 0
	class ContentConfig:
		charset = None
		prefix = 'utf-8'
		suffix = None
		pattern = None
		debug = False

	def __init__(self, txt_dir):
		conf_file = os.path.join(txt_dir, txt_config_file)
		if not os.path.exists(conf_file):
			self = None
			return
		summary = TxtConfig.SummaryConfig()

		if ConfigToVar(summary, conf_file, [
			ConfigVarMap(attr='url', section='summary', option='url', default=TxtConfig.SummaryConfig.url),
			ConfigVarMap(attr='urlBegin', section='summary', option='urlBegin', default=TxtConfig.SummaryConfig.urlBegin),
			ConfigVarMap(attr='urlEnd', section='summary', option='urlEnd', default=TxtConfig.SummaryConfig.urlEnd),
			ConfigVarMap(attr='charset', section='summary', option='charset', default=TxtConfig.SummaryConfig.charset),
			ConfigVarMap(attr='prefix', section='summary', option='prefix', default=TxtConfig.SummaryConfig.prefix),
			ConfigVarMap(attr='suffix', section='summary', option='suffix', default=TxtConfig.SummaryConfig.suffix),
			ConfigVarMap(attr='pattern', section='summary', option='pattern', default=TxtConfig.SummaryConfig.pattern),
			ConfigVarMap(attr='filename', section='summary', option='filename', default=TxtConfig.SummaryConfig.filename),
			ConfigVarMap(attr='counterLength', section='summary', option='counter_length', default=TxtConfig.SummaryConfig.counterLength),
		]):
			summary.pattern = re.compile(summary.pattern)
			self.summary = summary

		content = TxtConfig.ContentConfig()
		if ConfigToVar(content, conf_file, [
			ConfigVarMap(attr='charset', section='content', option='charset', default=TxtConfig.ContentConfig.charset),
			ConfigVarMap(attr='prefix', section='content', option='prefix', default=TxtConfig.ContentConfig.prefix),
			ConfigVarMap(attr='suffix', section='content', option='suffix', default=TxtConfig.ContentConfig.suffix),
			ConfigVarMap(attr='pattern', section='content', option='pattern', default=TxtConfig.ContentConfig.pattern),
			ConfigVarMap(attr='debug', section='content', option='debug', default=TxtConfig.ContentConfig.debug),
		]):
			content.pattern = re.compile(content.pattern)
			self.content = content

	def OK(self):
		return hasattr(self, 'summary') and hasattr(self, 'content')

def FetchUrlAndTrim(url, charset, prefix, suffix):
	html = urllib2.urlopen(url).read()
	html = html.decode(charset, errors='ignore')
	start = html.find(prefix)
	if start < 0:
		return False
	start += len(prefix)
	end = html.find(suffix, start)
	if end < 0:
		return False
	return html[start:end]

def FetchSummary(config):
	r = []
	for i in range(config.urlBegin, config.urlEnd):
		url = config.url.replace('{COUNTER}', str(i))
		content = FetchUrlAndTrim(url, config.charset, config.prefix, config.suffix)
		for m in config.pattern.finditer(content):
			g = m.groupdict()
			url = urlparse.urljoin(config.url, g['URL'])
			name = g['NAME']
			r.append((name, url))
		return r

def htmlTrans(html):
	html.replace('<br>', '\n')
	html.replace('<br>', '\n')

def FetchContent(txt_path, url, config):
	content = FetchUrlAndTrim(url, config.charset, config.prefix, config.suffix)
	r = []
	for m in config.pattern.finditer(content):
		r += list(m.groups())
	txt = '\n'.join(r)
	with open(txt_path, 'w') as f:
		f.write(txt.encode('utf-8'))

def FetchTxt(txt_dir):
	c = TxtConfig(txt_dir)
	if not c.OK():
		return False
	print 'Fetching %s ...' % txt_dir
	count = 0
	for (name, url) in FetchSummary(c.summary):
		count += 1
		filename = c.summary.filename.replace('{COUNTER}', str(count).zfill(c.summary.counterLength)).replace('{NAME}', name)
		txt_path = os.path.join(txt_dir, filename)
		if not os.path.exists(txt_path):
			print filename, url
			FetchContent(txt_path, url, c.content)
			if c.content.debug:
				break
	return True

def FetchAll(dir):
	for sub_dir in os.listdir(dir):
		sub_path = os.path.join(dir, sub_dir)
		if not os.path.isdir(sub_path):
			continue
		if not FetchTxt(sub_path):
			FetchAll(sub_path)

def main(argv):
	dirs = set(argv)
	if len(dirs) == 0:
		dirs.add('.')
	for dir in dirs:
		udir = dir.decode(locale.getdefaultlocale()[1])
		FetchAll(udir)

if __name__ == '__main__':
	main(sys.argv[1:])
