import os
import rdflib
from rdflib.term import URIRef, Literal
from gilgamesh_summarizer.kvpair import KvPair

class Rewriter:

    def __init__(self, input_file, output_file, output_csv, uri, resource, summarized_triples, removedLinks):
        self.input_file = input_file
        self.output_file = output_file
        self.output_csv = output_csv
        self.key_value_map = {}
        self.metrics_map = {}
        self.temporal_attributes = {}
        self.URI = uri
        self.RESOURCE = resource
        self.summarized_triples = summarized_triples
        self.removedLinks = []
        for link in removedLinks:
            self.removedLinks.append(str(link))

    def parse(self, export_to_csv=False):
        self.collect_entities()

        graph = rdflib.Graph()
        graph.parse(self.input_file, format='nt')

        with open(self.output_file, 'w') as writer:
            csv_writer = open(self.output_csv, 'w') if export_to_csv else None

            for type, keyString, valueString in self.summarized_triples:
                for s, p, o in graph:
                    s_str, p_str, o_str = str(s), str(p), str(o)

                    if str(type) in o_str:
                        continue

                    if p_str == str(keyString):
                        self.set_kv_key(s_str, o_str.strip('"'))
                        continue
                    if p_str == str(valueString):
                        self.set_kv_value(s_str, o_str)
                        continue
                    if any(kw in p_str for kw in self.removedLinks):
                        self.set_kv_subject(o_str, s_str)
                        self.set_kv_old_predicate(o_str, p_str)
                        continue
                    if self.key_value_map.get(s_str) and p_str == "http://purl.org/dc/terms/issued":
                        self.metrics_map[s_str] = o_str
                        continue
                    if p_str == "http://purl.org/dc/terms/identifier" and o_str.strip('"') in s_str:
                        ostr = o_str.strip('\"')
                        writer.write(f"{s_str} {p_str} <{self.RESOURCE}{ostr}> ." "\n")
                        continue
                    if p_str == "http://xmlns.com/foaf/0.1/accountName":
                        identifier = o_str.strip('"')
                        writer.write(f"{s_str} {p_str} <{self.RESOURCE}{identifier}> ." "\n")
                        writer.write(f"{s_str} <http://purl.org/dc/terms/identifier> <{self.RESOURCE}{identifier}> ." "\n")
                        continue
                    if p_str == "http://purl.org/dc/terms/spatial":
                        if 'POLYGON((' in o_str:
                            geom_uri = f"<{s_str.strip('<>')}/geometry>"
                            writer.write(f"{s_str} <http://www.opengis.net/ont/geosparql#hasGeometry> {geom_uri} ." "\n")
                            writer.write(f"{geom_uri} <http://www.opengis.net/ont/geosparql#asWKT> {o_str} ." "\n")
                        else:
                            p_str = "http://www.opengis.net/ont/geosparql#hasGeometry"
                    elif p_str == "http://www.w3.org/ns/locn#geometry":
                        p_str = "http://www.opengis.net/ont/geosparql#asWKT"

                    writer.write(f"{s_str} {p_str} {o_str} ." "\n")

                props = set()

            for key, kv in self.key_value_map.items():
                if export_to_csv and key not in self.metrics_map and kv.getSubject():
                    csv_writer.write(kv.toCSVEntry(key) + "\n")
                if kv.getSubject():
                    writer.write(kv.getTriple())
                    props.add(kv.getDataProperty())

            for key, issued_val in self.metrics_map.items():
                kv = self.key_value_map.get(key)
                if kv and kv.getSubject():
                    if export_to_csv:
                        csv_writer.write(kv.toCsvEntryExtraProperties(key, [("http://purl.org/dc/terms/issued", issued_val)]) + "\n")
                    writer.write(f"{kv.getSubject()} <{self.URI}metricIssued> {issued_val} ." "\n")

            for prop in props:
                print(prop)

            if csv_writer:
                csv_writer.close()

    def collect_entities(self):
        graph = rdflib.Graph()
        graph.parse(self.input_file, format='nt')

        for s, _, o in graph:
            s_str, o_str = str(s), str(o)
            if 'KeyValuePair' in o_str:
                self.key_value_map[s_str] = KvPair()

    def set_kv_key(self, key, kv_key):
        if key in self.key_value_map:
            self.key_value_map[key].setKey(kv_key)

    def set_kv_value(self, key, kv_value):
        if key in self.key_value_map:
            self.key_value_map[key].setValue(kv_value)

    def set_kv_subject(self, key, subject):
        if key not in self.key_value_map:
            self.key_value_map[key] = KvPair()
        self.key_value_map[key].setSubject(subject)

    def set_kv_old_predicate(self, key, old_predicate):
        if key in self.key_value_map:
            self.key_value_map[key].setOldPredicate(old_predicate)

    def get_kv_subject(self, key):
        return self.key_value_map.get(key).getSubject()
