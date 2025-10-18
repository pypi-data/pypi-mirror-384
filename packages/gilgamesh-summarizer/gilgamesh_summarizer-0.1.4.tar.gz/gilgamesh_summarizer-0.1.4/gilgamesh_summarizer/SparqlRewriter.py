from rdflib.plugins.sparql import parser
from rdflib.plugins.sparql.algebra import translateQuery
from rdflib.plugins.sparql.algebra import translateAlgebra
from rdflib.plugins.sparql.algebra import CompValue
from rdflib.term import Variable
from rdflib.term import Literal
from rdflib.term import URIRef
from rdflib import Graph
from pyparsing import ParseResults
from rdflib.plugins.sparql.parserutils import Expr


class ParseException(Exception):
    pass

class SparqlRewriter:
    def __init__(self):
        self.parse_tree = None
        #Return a query string
        self.keyValues = None
        
    def parse(self, queryString : str, keyValues : dict):
        self.parse_tree = parser.parseQuery(queryString)
        self.keyValues = keyValues
        visitor = _SparqlVisitor(keyValues)
        mapper = _MappingSparqlVisitor(visitor.variable_maps, visitor.mapping_heights, visitor.prefix_graph)

        #First perform the rewriting
        new_query_tree = visitor.visit(self.parse_tree, 0, 0)
        #Map the changed variables to filters,projections,triples etc
        final_query_tree = mapper.visit(new_query_tree, 0, 0)

        final_query = translateQuery(final_query_tree)
 
        #Return a query string
        return translateAlgebra(final_query)
        

class _SparqlVisitor:
    def __init__(self, keyValues : dict):
        self.value = None
        self.graph_pattern_names = {"OptionalGraphPattern","MinusGraphPattern","GraphGraphPattern","ServiceGraphPattern","InlineData","GroupOrUnionGraphPattern"}
        self.graph_sub_pattern = {"GroupGraphPatternSub"}
        self.variable_maps = {}
        self.mapping_heights = {}
        self.keyValues = keyValues
        self.varCount = 0
        self.prefix_graph = Graph()

    def visit(self, parse_tree : CompValue, height : int, branch : int):
        #Collect the queries prologue
        prologue = parse_tree[0]
        
        for prefix in prologue:
            pre = prefix.get("prefix")
            iri = prefix.get("iri")
            self.prefix_graph.bind(pre,iri)

        rest = parse_tree[1]
        projection = rest.get("projection")
        body = rest.get("where")

        #After the collecting the new body of the query rebulild it
        new_body = self.visitGroupGraphPattern(body, height, branch)

        #Collect limit,groupby and orderby
        limit = rest.get("limitoffset")
        if limit == "limitoffset":
            limit = None
        groupby = rest.get("groupby")
        if groupby == "groupby":
            groupby = None
        orderby = rest.get("orderby")
        if orderby == "orderby":
            orderby = None        

        kwargs = {
            "limitoffset": limit,
            "groupby": groupby,
            "orderby": orderby
        }
        # Filter out None values
        filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

        #Change variables from mappings
        query=None
        if projection != "projection":
            query = CompValue(rest.name,projection=projection,where=new_body,**filtered_kwargs)
        else:
            query = CompValue(rest.name,where=new_body,**filtered_kwargs)

        return ParseResults([prologue,query])


    def visitGroupGraphPattern(self, graph_pattern: CompValue, height: int, branch: int):
        if graph_pattern.name in self.graph_sub_pattern:
            #Get the body of a graph pattern
            part = graph_pattern.get("part")

            #Initialize the re-construction of the query
            partList = []
            local_branch = branch
            for subpart in part:
                # Triples block detected. Check for possible transformation
                if subpart.name == "TriplesBlock":
                    triples = subpart.get("triples")
                    triple_list = []
                    for triple in triples:
                        # Path with ; in triple. Breaking it up into triples
                        if len(triple)==3:
                            #CompValue case
                            if isinstance(triple[1],CompValue):
                                kv = self._check_pred_for_key_value(triple[1])
                                #Newly generated triples
                                if kv!=None:
                                    new_triples = self._revert_summarized_triple(kv,triple,height,local_branch)
                                    if new_triples!=None:
                                        triple_list += new_triples
                                    else:
                                        triple_list += [triple]
                                else:
                                    triple_list += [triple]
                            else:
                                triple_list += [triple]
                        else:
                            n = 3
                            triplets = [ParseResults(triple[i:i+n]) for i in range(0, len(triple), n)]
                            for t in triplets:
                                #CompValue case
                                if isinstance(t[1],CompValue):
                                    kv = self._check_pred_for_key_value(t[1])
                                    #Newly generated triples
                                    if kv!=None:
                                        new_triples = self._revert_summarized_triple(kv,t,height,local_branch)
                                        if new_triples!=None:
                                            triple_list += new_triples
                                        else:
                                            triple_list += [t]
                                    else:
                                        triple_list += [t]
                                else:
                                    triple_list += [t]

                    #Create the new triples part for the GroupGraphPatternSub block
                    partList += [CompValue("TriplesBlock",triples=triple_list)]
                elif subpart.name == "Filter":
                    partList += [subpart]
                elif subpart.name == "InlineData":
                    partList += [subpart]
                elif subpart.name in self.graph_pattern_names:
                    partList += [self.visitGraphPattern(subpart,height+1,branch+1)]
                    branch+=1

            #Reconstruct the GroupGraphPatternSub
            groupGraphPatternSub = CompValue("GroupGraphPatternSub",part=partList)
            return groupGraphPatternSub


    def visitGraphPattern(self, graph_pattern: CompValue, height: int, branch: int):
        name = graph_pattern.name
        graph = graph_pattern.get("graph")
        new_graph = None
        if isinstance(graph,list):
            new_graph = []
            for g in graph:
                if g.name == "SubSelect":
                    _, query = self.visit([[],g], height, branch)
                    new_graph += [query]
                if g.name in self.graph_sub_pattern:
                    group = self.visitGroupGraphPattern(g, height, branch)
                    new_graph += [group]
                    branch+=1
        elif isinstance(graph,CompValue):
            new_graph = self.visitGroupGraphPattern(graph, height, branch)
        return CompValue(name,graph=new_graph)

    def _check_pred_for_key_value(self, path_alternative: CompValue):
        part = path_alternative.get("part")
        for subpart in part:
            if subpart.name == "PathSequence":
                subpart = subpart.get("part")
                for s in subpart:
                    if s.name == "PathElt" :
                        triple_part = s.get("part")
                        if isinstance(triple_part,CompValue):
                            mod = s.get("mod")
                            prefix = triple_part.get("prefix")
                            localname = triple_part.get("localname")
                        elif isinstance(triple_part,URIRef):
                            mod = "mod"
                            prefix, _, localname = self.prefix_graph.namespace_manager.compute_qname(triple_part)

                        check = self._check_localname_for_key_value(localname)
                        if check != None:
                            return (check[0], check[1], prefix, localname, mod)
                        else:
                            return None
        return None
            
    def _check_localname_for_key_value(self, localname):
        for k,v in self.keyValues.items():
            (keyName,valueName,mappings) = v
            for key,value in mappings.items():
                if str(localname) in value:
                    return (key,k)
        return None
    
    def _revert_summarized_triple(self, kv, triple, height, branch):
        if kv != None:
            o = triple[2]
            # The summarized triple is of the form:
            #
            # ?s ex:quo ?o .
            #
            # The reverted triples generated will be of the form:
            #
            # ?s ex:hasKV ?kv .
            # ?kv ex:key "quo" .
            # ?kv ex:value ?v .
            #
            if isinstance(o,Variable):
                path_alt = self._construct_path_alternative(kv)
                new_var_name = "__kv" + str(self.varCount)
                self.varCount += 1
                new_var = Variable(new_var_name)
                results = [ParseResults([triple[0],path_alt,new_var])]

                # Create triple for key access
                keyPredicate, valuePredicate, _ = self.keyValues[kv[1]]

                path_alt_key = self._construct_path_alternative((keyPredicate, None, kv[2], None, "mod"))
                #create a literal for the key string
                keyLiteral = CompValue("literal",string = Literal(kv[3]))
                results += [ParseResults([new_var,path_alt_key,keyLiteral])]

                # Create triple for value query
                path_alt_value = self._construct_path_alternative((valuePredicate, None, kv[2], None, "mod"))
                new_value_access_var_name = "__v" + str(self.varCount)
                self.varCount += 1
                new_value_access_var = Variable(new_value_access_var_name)
                results += [ParseResults([new_var,path_alt_value,new_value_access_var])]


                #update the variables map
                self.variable_maps[o] = new_value_access_var
                self.mapping_heights[o] = (height,branch)
                return results
            
            # The summarized triple is of the form:
            #
            # ?s ex:quo "lorum" .
            #
            # The reverted triples generated will be of the form:
            #
            # ?s ex:hasKV ?kv .
            # ?kv ex:key "quo" .
            # ?kv ex:value "lorum" .
            #
            elif o.name == "literal":
                path_alt = self._construct_path_alternative(kv)
                new_var_name = "__kv" + str(self.varCount)
                self.varCount += 1
                new_var = Variable(new_var_name)
                results = [ParseResults([triple[0],path_alt,new_var])]

                # Create triple for key access
                keyPredicate, valuePredicate, _ = self.keyValues[kv[1]]

                path_alt_key = self._construct_path_alternative((keyPredicate, None, kv[2], None, "mod"))
                #create a literal for the key string
                keyLiteral = CompValue("literal",string = Literal(kv[3]))
                results += [ParseResults([new_var,path_alt_key,keyLiteral])]

                # Create triple for value query
                path_alt_value = self._construct_path_alternative((valuePredicate, None, kv[2], None, "mod"))
                results += [ParseResults([new_var,path_alt_value,o])]

                return results



    def _construct_path_alternative(self, kv: tuple):
        (pre_summarized_pred,_,prefix,_,mod) = kv
        part = CompValue("pname",prefix=prefix,localname=pre_summarized_pred)
        path_elt = None
        if mod=="mod":
            path_elt = CompValue("PathElt",part=part)
        else:
            path_elt = CompValue("PathElt",part=part,mod=mod)
        path_seq = CompValue("PathSequence",part=[path_elt])
        path_alt = CompValue("PathAlternative",part=[path_seq])
        return path_alt
        



class _MappingSparqlVisitor:
    def __init__(self, variable_maps : dict, mapping_heights : dict, prefix_graph : Graph):
        self.variable_maps = variable_maps
        self.mapping_heights = mapping_heights
        self.prefix_graph = prefix_graph
        self.graph_pattern_names = {"OptionalGraphPattern","MinusGraphPattern","GraphGraphPattern","ServiceGraphPattern","InlineData","GroupOrUnionGraphPattern"}
        self.graph_sub_pattern = {"GroupGraphPatternSub"}

    def visit(self, parse_tree : CompValue, height : int, branch : int):
        #Collect the queries prologue
        prologue = parse_tree[0]
        
        for prefix in prologue:
            pre = prefix.get("prefix")
            iri = prefix.get("iri")
            self.prefix_graph.bind(pre,iri)

        rest = parse_tree[1]
        projection = rest.get("projection")
        body = rest.get("where")

        #After the collecting the new body of the query rebulild it
        new_body = self.visitGroupGraphPattern(body, height, branch)

        #Collect limit,groupby and orderby
        limit = rest.get("limitoffset")
        if limit == "limitoffset":
            limit = None
        groupby = rest.get("groupby")
        if groupby == "groupby":
            groupby = None
        orderby = rest.get("orderby")
        if orderby == "orderby":
            orderby = None        

        kwargs = {
            "limitoffset": limit,
            "groupby": groupby,
            "orderby": orderby
        }
        # Filter out None values
        filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

        #Change variables from mappings
        query=None
        if projection != "projection":
            newVarList = []
            for var in projection:
                compVar = var.get("var")
                if compVar != "var" :
                    mapping = self.variable_maps.get(compVar,None)
                    if mapping == None:
                        newVarList += [var]
                    else:
                        newVarList += [CompValue("vars",var=mapping)]
                else:
                    newVarList += [self._rebuild_conditional(var)]
                    #newVarList += [var]
            query = CompValue(rest.name,projection=newVarList,where=new_body,**filtered_kwargs)
        else:
            query = CompValue(rest.name,where=new_body,**filtered_kwargs)


        return ParseResults([prologue,query])


    def visitGroupGraphPattern(self, graph_pattern: CompValue, height: int, branch: int):
        if graph_pattern.name in self.graph_sub_pattern:
            #Get the body of a graph pattern
            part = graph_pattern.get("part")

            #Initialize the re-construction of the query
            partList = []
            local_branch = branch
            for subpart in part:
                # Triples block detected. Check for possible transformation
                if subpart.name == "TriplesBlock":
                    triples = subpart.get("triples")
                    triple_list = []
                    for triple in triples:
                        s = triple[0]
                        p = triple[1]
                        o = triple[2]
                        
                        s = self._map_variable(s,height,local_branch)
                        o = self._map_variable(o,height,local_branch)

                        triple_list += [ParseResults([s,p,o])]
                    #Create the new triples part for the GroupGraphPatternSub block
                    partList += [CompValue("TriplesBlock",triples=triple_list)]
                elif subpart.name == "Filter":
                    partList += [self._rebuild_conditional(subpart)]
                elif subpart.name == "InlineData":
                    partList += [subpart]
                elif subpart.name in self.graph_pattern_names:
                    partList += [self.visitGraphPattern(subpart,height+1,branch+1)]
                    branch+=1

            #Reconstruct the GroupGraphPatternSub
            groupGraphPatternSub = CompValue("GroupGraphPatternSub",part=partList)
            return groupGraphPatternSub


    def visitGraphPattern(self, graph_pattern: CompValue, height: int, branch: int):
        name = graph_pattern.name
        graph = graph_pattern.get("graph")
        new_graph = None
        if isinstance(graph,list):
            new_graph = []
            for g in graph:
                if g.name == "SubSelect":
                    _, query = self.visit([[],g], height, branch)
                    new_graph += [query]
                if g.name in self.graph_sub_pattern:
                    group = self.visitGroupGraphPattern(g, height, branch)
                    new_graph += [group]
                    branch+=1
        elif isinstance(graph,CompValue):
            new_graph = self.visitGroupGraphPattern(graph, height, branch)
        return CompValue(name,graph=new_graph)

    def _rebuild_conditional(self, aggr : CompValue):
        aggr_name = aggr.name
        expr = aggr.get("expr")

        if isinstance(expr,Variable):
            mapping = self.variable_maps.get(expr,None)
            new_expr = expr
            if mapping != None:
                new_expr = mapping

            new_aggr = {}
            for k,v in aggr.items():
                if k=="expr":
                    new_aggr[k] = new_expr
                else:
                    new_aggr[k] = v
            return Expr(aggr_name,**new_aggr)
        
        elif isinstance(expr,CompValue):
            new_expr = self._rebuild_conditional(expr)
            new_aggr = {}
            for k,v in aggr.items():
                if k=="expr":
                    new_aggr[k] = new_expr
                else:
                    new_aggr[k] = v

            return Expr(aggr_name,**new_aggr)
            
        else:
            new_vars = self._rebuild_conditional(aggr.get("vars"))
            new_aggr = {}
            for k,v in aggr.items():
                if k=="vars":
                    new_aggr[k] = new_vars
                else:
                    new_aggr[k] = v
            if isinstance(aggr,CompValue):
                return CompValue(aggr_name,**new_aggr)
            else:
                return Expr(aggr_name,**new_aggr)
        
    def _map_variable(self, var, height, branch):
        if not isinstance(var,Variable):
            return var
        mapping_var = self.variable_maps.get(var,None)
        hb = self.mapping_heights.get(var,None)
        if mapping_var != None:
            if height < hb[0]: 
                var = mapping_var
            elif height == hb[0]:
                if branch == hb[1]:
                    var = mapping_var
        return var