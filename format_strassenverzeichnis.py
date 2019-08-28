#!/usr/bin/env python3
import csv
import json
import re

with open('tabula-strassenverzeichnis_wahllokale_wb_wk.json', 'r') as texts_file:
    with open('tabula_specs-strassenverzeichnis_wahllokale_wb_wk.json', 'r') as specs_file:
        with open('tabula-strassenverzeichnis_wahllokale_wb_wk.tsv', 'w') as outfile:
            csvwriter = csv.writer(outfile, delimiter='\t', quotechar='"', lineterminator='\n', quoting=csv.QUOTE_MINIMAL)
            texts = json.load(texts_file)
            specs = json.load(specs_file)
            texts_by_index = {t['spec_index']: t for t in texts}
            specs_order = list(map(lambda s: s['spec_index'], sorted(specs, key=lambda s: (s['page'], s['x1'] > 130, s['spec_index']))))
            for specs_index in specs_order:
                text = texts_by_index[specs_index]
                for row in text['data']:
                    csvwriter.writerow(list([c['text'] for c in row]))

with open('tabula-strassenverzeichnis_wahllokale_wb_wk.tsv', 'r') as infile:
    with open('wahllokale.csv', 'w') as outfile_p:
        with open('strassenverzeichnis.csv', 'w') as outfile_s:
            csvreader = csv.reader(infile, delimiter='\t', quotechar='"')
            csvwriter_p = csv.writer(outfile_p, delimiter=',', quotechar='"', lineterminator='\n', quoting=csv.QUOTE_MINIMAL)
            csvwriter_s = csv.writer(outfile_s, delimiter=',', quotechar='"', lineterminator='\n', quoting=csv.QUOTE_MINIMAL)

            # Output file headers
            csvwriter_p.writerow(['Wahlkreis', 'Wahlbezirk', 'Name', 'Straße', 'PLZ+Ort', 'barrierefrei'])
            csvwriter_s.writerow(['Wahlbezirk', 'Straße', 'Hausnummern'])

            inside_polling_station = False
            block_line = 0
            station_attributes = []
            ward_id = ''
            district_id = ''
            street = ''
            housenumbers = ''

            for row in csvreader:
                if row[0].startswith('Straßenverzeichnis'):
                    pass # skip header row
                elif inside_polling_station:
                    block_line += 1
                    station_attributes.append(row[0])
                    # Block always 3 lines
                    if block_line == 3:
                        # Some rows are smashed together
                        match = re.match('(.*) barrierefrei', row[0])
                        if match:
                            del(station_attributes[-1])
                            station_attributes.append(match.group(1))
                            station_attributes.append('barrierefrei')
                        elif row[1] == 'barrierefrei':
                            station_attributes.append(row[1])
                        else:
                            station_attributes.append('')
                        inside_polling_station = False
                        block_line = 0
                        csvwriter_p.writerow(station_attributes)
                        station_attributes = []

                # Detect Wahllokal block
                elif row[0].startswith('Wahlbezirk'):
                    # Some rows are smashed together
                    match = re.match('Wahlbezirk (\d+) WK (\d+)', row[0])
                    if match:
                        district_id = match.group(1)
                        ward_id = match.group(2)
                    else:
                        match = re.match('Wahlbezirk (\d+)', row[0])
                        district_id = match.group(1)
                        match = re.match('WK (\d+)', row[1])
                        ward_id = match.group(1)
                    inside_polling_station = True
                    block_line = 0
                    station_attributes = [ward_id, district_id]
                elif ''.join(row).strip():
                    if row[0].strip():
                        # Output previous street, start new street
                        if street:
                            street_row = [district_id, street, housenumbers]
                            csvwriter_s.writerow(street_row)
                        street, housenumbers = row
                    else:
                        # Continue street with another set of housenumbers
                        housenumbers += ', ' + row[1]
            # Output last street
            street_row = [district_id, street, housenumbers]
            csvwriter_s.writerow(street_row)
