#!/usr/bin/env ruby
# encoding: utf-8
##################################################################################
# Script to read a list of BEIC APE BIDs, download UNIMARC records from OPAC SBN #
# and extract subjects.                                                          #
# Example: ./BEIC_records2subjecs.rb bids.txt subjects.csv                       #
#                                                                                #
# MIT license, (C) Federico Leva e Fondazione BEIC, 2018                         #
#                                                                                #
##################################################################################

require 'net/http'
require 'marc'

subjects = File.open(ARGV[1], "w")
subjects.write("Identificativo\tCampo\tSottocampi\n")

File.readlines(ARGV[0]).each do |bid|
    puts bid
    bid = bid.strip
    url = URI.parse('http://opac.sbn.it/opacsbn/opaclib?db=solr_iccu&select_db=solr_iccu&nentries=1&from=1&searchForm=opac/iccu/error.jsp&resultForward=opac/iccu/scarico_uni.jsp&do_cmd=search_show_cmd&format=unimarc&rpnlabel=+Identificativo+SBN+%3D+' + bid  + '+%28parole+in+AND%29+&rpnquery=%40attrset+bib-1++%40attr+1%3D1032+%40attr+4%3D6+%22' + bid  + '%22&totalResult=1&fname=none')
    req = Net::HTTP::Get.new(url.to_s)
    res = Net::HTTP.start(url.host, url.port) { |http|
        http.request(req)
                                              }
    reader = MARC::ForgivingReader.new(StringIO.new(res.body))
    for record in reader
        for subject in record.find_all {|field| ('606'..'676') === field.tag}
            subjects.write("%{id}\t%{field}\n" % { :id => bid, :field => subject.to_s.strip.gsub(/    /, "\t") } )
        end
    end
end

subjects.close
