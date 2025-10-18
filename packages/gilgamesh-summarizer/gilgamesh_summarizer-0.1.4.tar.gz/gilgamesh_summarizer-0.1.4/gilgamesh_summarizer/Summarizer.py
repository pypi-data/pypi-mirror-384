from rdflib import Graph, Namespace, RDF, RDFS, OWL, term, XSD
from unsloth import FastLanguageModel
from transformers import AutoTokenizer
import torch
from typing import List, Dict, Tuple
import rdflib
from rdflib.namespace import split_uri


class Summarizer:
    def __init__(self,kg):
        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name="Kwts/OntologySummarizer",
            max_seq_length=2048,
            dtype=None,
            load_in_4bit=True,
        )

        self.kg = kg
        self.mappings = {}
        self.result_domains = {}
        self.results = []
        self.kvpairs = set()
        self.model.eval()
        self.template = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
Determine whether the given RDF triple set represents a KeyValuePair. Prove which predicate is the key and which the value. Your answer must have the following form:
Yes/No:<key>:<value>

### Input:
{}

### Response:
"""

    def format_triples(self, node: rdflib.term.URIRef, triples: List[Tuple]) -> str:
        lines = []
        for predicate, obj in triples:
            pred_str = f"<{predicate}>"
            obj_str = f"<{obj}>" if isinstance(obj, rdflib.term.URIRef) else f'"{obj}"'
            lines.append(f"<{node}> {pred_str} {obj_str} .")
        return "\n".join(lines)

    def classify_node(self, triples: str) -> str:
        prompt = self.template.format(triples) + self.tokenizer.eos_token
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(**inputs, max_new_tokens=20, do_sample=False)
        decoded = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Parse only the last response segment
        if "### Response:" in decoded:
            response = decoded.split("### Response:")[-1].strip().split("\n")[0]
        else:
            response = decoded.strip()
        return response

    def classify_clusters(
        self,
        clusters: List[List[rdflib.term.URIRef]],
        triples_dict: Dict[rdflib.term.URIRef, List[Tuple]]
    ):
        results = {}
        for cluster in clusters:
            for node in cluster:
                if node in triples_dict:
                    if triples_dict.get(node,-1)!=-1:
                        formatted = self.format_triples(node, triples_dict[node])
                        classification = self.classify_node(formatted)
                        results[str(node)] = classification

        for (k,v) in results.items():
            if 'yes' in str(v.lower()) or 'yes'==str(v.lower()):
                tokens = v.split(":")
                key = tokens[1]
                value = tokens[2]
                type = self.__find_type(term.URIRef(k),key,value,triples_dict)
                if type != None:
                    self.kvpairs.add(type)


        self.results = results
        return self.kvpairs

    def remove_classes_and_collect_range_predicates(self, target_uris: set):
        removed_predicates = set()
        graph = self.kg.ontology

        for uri_str in target_uris:
            class_uri = term.URIRef(uri_str[0])

            # Find predicates where the class is used as a range
            for pred in graph.subjects(RDFS.range, class_uri):
                if isinstance(pred, term.URIRef):
                    #store the domains of each removed predicate for the ontology rewriting step
                    domains = list(graph.objects(pred, RDFS.domain))
                    self.result_domains[pred] = domains

                    removed_predicates.add(pred)
                    for triple in list(graph.triples((pred, None, None))):
                        graph.remove(triple)

            # Remove the class definition and related triples
            for triple in list(graph.triples((class_uri, None, None))):
                graph.remove(triple)

            for triple in list(graph.triples((None, None, class_uri))):
                graph.remove(triple)


        self._collect_mappings(removed_predicates)
        return removed_predicates, self.mappings

    def get_summarized_ontology(self):
        if self.mappings == {}:
            raise Exception("No mappings found. Run remove_classes_and_collect_range_predicates() before generating summarized ontology")
        else:
            ontology = self.kg.ontology

            for (kv,k,v) in self.results:
                prefix , localname_kv = split_uri(kv)
                _ , localname_k = split_uri(k)
                _ , localname_v = split_uri(v)

                entry = self.mappings.get(localname_kv,None)
                if entry != None:
                    for removed_preds, new_preds in entry[2].items():
                        domains = self.result_domains.get(term.URIRef(prefix+removed_preds),None)
                        if domains != None:
                            for new_pred in new_preds:
                                for domain in domains:
                                    ontology.add((term.URIRef(prefix + new_pred), RDFS.domain, domain))
                                ontology.add((term.URIRef(prefix + new_pred),RDFS.range, XSD.string))

            return ontology

    def _collect_mappings(self, removed_predicates):
        graph = self.kg.graph
        candidates = {}

        #collect candidate entities
        for s, p, o in graph:
            if p in removed_predicates:
                candidates[o] = p

        #search and store mappings
        for s, p, o in graph:
            res = candidates.get(s,None)
            if s != None:
                candidate_mapping = self._check_results(self, p)
                if candidate_mapping != None:
                    self._update_mappings(candidate_mapping, res, o)


    def _update_mappings(self, candidate_mapping, old_pred, o):
        (kv,k,v) = candidate_mapping
        _,kv = split_uri(kv)
        _,k = split_uri(k) 
        _,v = split_uri(v) 

        entry = self.mappings.get(kv,None)
        if entry == None:
            entry_dict = {}
            entry_set = set()
            entry_set.add(o)
            entry_dict[old_pred] = entry_set
            self.mappings[kv] = (k,v,entry_dict)
        else:
            (_k,_v,_entry_dict) = entry
            _entry_set = _entry_dict.get(old_pred,None)

            if _entry_set == None:
                _entry_set = set()

            _entry_set.add(o)
            _entry_dict[old_pred] = _entry_set

            self.mappings[kv] = (_k,_v,_entry_dict)

    def _check_results(self, predicate):
        for (kv,k,v) in self.results:
            if k == predicate:
                return (kv,k,v)
        return None

    def __find_type(self,node,key,value,triples_dict):
        edges = triples_dict.get(node,-1)
        if edges==-1:
            return None
        else:
            type=""
            k=""
            v=""
            for (p,o) in edges:
                if p == RDF.type:
                    type = o
                if key==str(o):
                    k = p
                if value==str(o):
                    v = p

            return (type,k,v)

