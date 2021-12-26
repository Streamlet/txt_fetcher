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

# conf（INI）文件格式定义
class TxtConfig:
	# [summary]
	# 目录页抓取配置
	class SummaryConfig:
		# 目录页 URL
		url = None
		# 如果有多个目录页，配置 [urlBegin, urlEnd)，url 里可用 {COUNTER} 占位
		urlBegin = 0
		urlEnd = 1
		# 目录页编码
		charset = 'utf-8'
		# 目录页有效内容起始和结束位置，抓取内容在“第一个 prefix 出现的位置”到“第一个 prefix 出现的位置之后的第一次 suffix 出现的位置”之间
		prefix = None
		suffix = None
		# 目录内容捕获，正则
		# 命名捕获组 NAME 表示该章节标题
		# 命名捕获组 URL 表示该章节内容地址，如果是相对 URL，会基于目录页 URL 计算绝对 URL
		pattern = None
		# 章节文件名，可用变量 {COUNTER}、{NAME}
		# 其中 {COUNTER} 是序号，位数由 counterLength 设定
		# {NAME} 是章节标题
		filename = '[{COUNTER}]{NAME}.txt'
		counterLength = 0
	# [content]
	# 内容也抓取配置
	class ContentConfig:
		# 内容页编码
		charset = 'utf-8'
		# 内容页有效内容起始和结束位置，含义同上
		prefix = None
		suffix = None
		# 正文内容捕获，正则
		# 有且只有一个捕获组表示一个段落，会循环抓取到结束位置
		pattern = None
		# 如果内容页含有下一页，需要继续抓
		# 表示跳几次下一页
		nextCount = 0
		# 抓取下一页 URL，可匹配当前页整个页面，不限于 prefix 和 suffix 之间
		nextUrlPattern = None
		# 下一页编码，如果为 None，与本页对应配置相同，下同
		nextCharset = None
		# 下一页有效内容起始和结束位置，含义同上
		nextPrefix = None
		nextSuffix = None
		# 下一页正文内容的捕获
		nextContentPattern = None
		# 调试
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
			ConfigVarMap(attr='nextCount', section='content', option='nextCount', default=TxtConfig.ContentConfig.nextCount),
			ConfigVarMap(attr='nextUrlPattern', section='content', option='nextUrlPattern', default=TxtConfig.ContentConfig.nextUrlPattern),
			ConfigVarMap(attr='nextCharset', section='content', option='nextCharset', default=TxtConfig.ContentConfig.nextCharset),
			ConfigVarMap(attr='nextPrefix', section='content', option='nextPrefix', default=TxtConfig.ContentConfig.nextPrefix),
			ConfigVarMap(attr='nextSuffix', section='content', option='nextSuffix', default=TxtConfig.ContentConfig.nextSuffix),
			ConfigVarMap(attr='nextContentPattern', section='content', option='nextContentPattern', default=TxtConfig.ContentConfig.nextContentPattern),
			ConfigVarMap(attr='debug', section='content', option='debug', default=TxtConfig.ContentConfig.debug),
		]):
			content.pattern = re.compile(content.pattern)
			if content.nextCount > 0:
				content.nextUrlPattern = re.compile(content.nextUrlPattern)
				if content.nextCharset is None:
					content.nextCharset = content.charset
				if content.nextPrefix is None:
					content.nextPrefix = content.prefix
				if content.nextSuffix is None:
					content.nextSuffix = content.suffix
				if content.nextContentPattern is None:
					content.nextContentPattern = content.pattern
				else:
					content.nextContentPattern = re.compile(content.nextContentPattern)
				
			self.content = content

	def OK(self):
		return hasattr(self, 'summary') and hasattr(self, 'content')

def FetchUrl(url, charset):
	print url
	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
	}
	request = urllib2.Request(url, None, headers)
	html = urllib2.urlopen(request).read()
	html = html.decode(charset, errors='ignore')
	return html

def TrimContent(html, prefix, suffix):
	start = 0
	if prefix is not None and prefix != '':
		start = html.find(prefix)
		if start < 0:
			return False
		start += len(prefix)
	end = len(html)
	if suffix is not None and suffix != '':
		end = html.find(suffix, start)
		if end < 0:
			return False
	return html[start:end]

def FetchUrlAndTrim(url, charset, prefix, suffix):
	html = FetchUrl(url, charset)
	return TrimContent(html, prefix, suffix)

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
	html = FetchUrl(url, config.charset)
	content = TrimContent(html, config.prefix, config.suffix)
	r = []
	# 抓本页
	for m in config.pattern.finditer(content):
		r += list(m.groups())
	# 循环抓下一页
	nextHtml = html
	for i in range(0, config.nextCount):
		nextUrls = config.nextUrlPattern.findall(nextHtml)
		nextUrl = urlparse.urljoin(url, nextUrls[0])
		nextHtml = FetchUrl(nextUrl, config.charset)
		nextContent = TrimContent(nextHtml, config.nextPrefix, config.nextSuffix)
		for m in config.nextContentPattern.finditer(nextContent):
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
		print filename,
		txt_path = os.path.join(txt_dir, filename)
		if os.path.exists(txt_path):
			print 'skipped'
		else:
			FetchContent(txt_path, url, c.content)
			if c.content.debug:
				break
	return True

def FetchAll(dir):
	if FetchTxt(dir):
		return
	for sub_dir in os.listdir(dir):
		sub_path = os.path.join(dir, sub_dir)
		if not os.path.isdir(sub_path):
			continue
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
