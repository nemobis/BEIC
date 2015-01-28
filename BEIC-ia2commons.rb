#!/usr/bin/env ruby
# encoding: utf-8
##################################################################################
# Script to read a list of BEIC.it PIDs and upload archive.org books to Commons  #
# via the https://tools.wmflabs.org/ia-upload tool, adding {{BEIC|pid= X }}.     #
# Scrapes some data from digitool's MetadataManager (webclient), which is in     #
# MARC21 (http://www.loc.gov/MARC21/slim).                                       #
#                                                                                #
# How to use:                                                                    #
# * write the list of BEIC PIDs in a file BEIC-pids.txt in same directory;       #
# * "login" to ia-upload with OAuth and get the PHPSESSID cookie;                #
# * pass the cookie value as only argument to this script.                       #
#                                                                                #
# MIT license, (C) Federico Leva e Fondazione BEIC, 2014                         #
#                                                                                #
##################################################################################

require 'rubygems'
require 'mechanize'
require 'uri'

# You have to manually set the ia-upload PHPSESSID cookie as commandline argument for now
a = Mechanize.new { |agent|
	agent.user_agent_alias = 'Linux Firefox'
}
cookie = Mechanize::Cookie.new :domain => ".tools.wmflabs.org", :name => "PHPSESSID", :value => ARGV[0], :path => "/"
a.cookie_jar << cookie

pids = Array.new

File.foreach("BEIC-pids.txt", "\n") do |pid|
	metadata = a.get("http://131.175.183.1/webclient/MetadataManager?descriptive_only=true&pid=" + pid)
	if metadata.search("//td[contains(text(),'CaSfIA')]").empty?
		puts "Nothing to do with " + pid
		next
	end
	puts "There is hope for " + pid
	pids << pid
	# http://www.w3.org/TR/xpath/#path-abbrev
	ia = metadata.parser.xpath('//td[text()="Other ID"]/../td[5]').text
	title = metadata.parser.xpath('//td[text()="Main Title"]/../td[5]').text
	# The pseudo-field "a" is not always in the same position (row)
	# For following-sibling etc. see http://www.w3.org/TR/xpath/#section-Location-Steps
	if metadata.parser.xpath('//td[text()="Personal Name"]/../td[4]').text == 'a'
		name = metadata.parser.xpath('//td[text()="Personal Name"]/../td[5]').text
	else
		name = metadata.parser.xpath('//td[text()="Personal Name"]/../following::td[text()="a"][1]/../td[last()]').text
	end
	year = metadata.parser.xpath('//td[text()="Imprint"]/../following-sibling::tr[position()=2]/td[3]').text 
	# We can finally produce a filename it.wikisource likes!
	commons = name.split(/(,| :)/)[0] + " - " + title + ", " + year
	# Ensure the title isn't invalid
	commons = commons.gsub(/[<>\[\]|{}]/, "")

	tool = URI.escape("https://tools.wmflabs.org/ia-upload/commons/init?iaId=" + ia + "&commonsName=" + commons)
	puts "Will try: " + tool
	begin
	upload = a.get(tool).form

	confirm = a.submit(upload, upload.buttons.first)
	form = confirm.forms.first
	
	description = form['description'].sub! "{{IA|", "{{BEIC|pid = " + pid.strip! + "}} {{IA|"
	form['description'] = description
	form.submit
	rescue
		puts "Something went wrong for PID: " + pid
	end

end