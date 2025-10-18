from rdflib import Graph, Namespace, RDF, RDFS, OWL, term
from collections import defaultdict, deque

import networkx as nx
import os
from tqdm import tqdm
import pandas as pd
from pyjedai.datamodel import Data
from pyjedai.block_building import StandardBlocking
from pyjedai.block_cleaning import BlockPurging
from pyjedai.block_cleaning import BlockFiltering
from pyjedai.matching import EntityMatching
from pyjedai.comparison_cleaning import WeightedEdgePruning
from pyjedai.clustering import ConnectedComponentsClustering


class KnowledgeGraph:
    def __init__(self, graph_file, ontology_file):
        self.graph = Graph()
        self.ontology = Graph()
        self.triple_dict = {}

        # Load N-Triples formatted files
        self.graph.parse(graph_file)
        self.ontology.parse(ontology_file)

    def create_clusters(self,prune_top_nodes=6,max_cluster_size=500):
        # convert RDFLib graph to Networkx MultiDiGraph
        nx_graph = nx.MultiDiGraph()

        for s, p, o in tqdm(self.graph):
            self.__add_triple(s,p,o)
            if p != RDF.type:
                if o.__class__ == term.Literal:
                    continue  
                nx_graph.add_edge(s, o, **{'key': p})

        # get the number of nodes, edges, and self-loops
        nodes = nx.number_of_nodes(nx_graph)
        edges = nx.number_of_edges(nx_graph)
        self_loops = nx.number_of_selfloops(nx_graph)

        print('There are {} nodes, {} edges, and {} self-loop(s)'.format(nodes, edges, self_loops))

        # get connected components -- have to convert MultiDiGraph to undirected graph
        nx_graph_und = nx_graph.to_undirected()

        # get connected components
        top_k_nodes = self.get_top_k_by_degree(nx_graph_und,prune_top_nodes)
        for node in top_k_nodes:
            nx_graph_und.remove_node(node[0])


        components = sorted(list(nx.connected_components(nx_graph_und)), key=len, reverse=True)

        new_components=[]
        for component in components:
            if len(component) > max_cluster_size:
                dataList = []
                for node in component:
                    edges = self.triple_dict.get(node,-1)
                    if edges != -1:
                        for (p,o) in edges:
                            if o.__class__ != term.URIRef:
                                dataList.append((node,p,o))
                df = pd.DataFrame(dataList, columns =['s', 'p', 'o'])

                # Create pyjedai data format
                attr=['s','p','o']
                data = Data(
                    dataset_1=df,
                    id_column_name_1='s',
                    attributes_1=attr,
                )

                # Build blocks from connected component
                bb = StandardBlocking()
                blocks = bb.build_blocks(data)

                # Block cleaning
                bp = BlockPurging()
                cleaned_blocks = bp.process(blocks, data, tqdm_disable=False)
                bc = BlockFiltering(ratio=0.75)
                cleaned_blocks = bc.process(cleaned_blocks, data)

                mb = WeightedEdgePruning(weighting_scheme='CBS')
                blocks = mb.process(cleaned_blocks, data)

                em = EntityMatching(
                    metric='jaccard',
                    similarity_threshold=0.4
                )

                pairs_graph = em.predict(blocks, data)

                ec = ConnectedComponentsClustering()
                clusters = ec.process(pairs_graph, data, similarity_threshold=0.3)

                
                for idx, cluster in enumerate(clusters):
                    c = set()
                    for item in cluster:
                        c.add(df.iloc[item]["s"])
                    new_components.append(list(c))

        components.extend(new_components)

        #Final cleaning steps for components - remove componenets with less than two literal properties
        filtered_components = []

        for component in components:
            new_component = []
            for node in component:
                edges = self.triple_dict.get(node, [])
                literal_count = sum(1 for _, o in edges if isinstance(o, term.Literal))
                if literal_count >= 2:
                    new_component.append(node)
            if new_component:
                filtered_components.append(new_component)

        # Optionally replace original components list
        components = filtered_components

        return components, self.triple_dict

    def get_top_k_by_degree(self, graph, k=10):
        if k==0:
            return []
        # Compute degree for all nodes
        degree_dict = dict(graph.degree())
        
        # Sort nodes by degree in descending order
        top_k = sorted(degree_dict.items(), key=lambda item: item[1], reverse=True)[:k]
        
        return top_k
    
    def __add_triple(self,s,p,o):
        l = self.triple_dict.get(s,-1)
        if l == -1:
            l = []
        l.append((p,o))
        self.triple_dict[s] = l


