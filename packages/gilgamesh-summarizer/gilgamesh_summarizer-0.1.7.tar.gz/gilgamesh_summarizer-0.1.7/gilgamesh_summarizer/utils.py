from rdflib import RDF, term
import csv

def export_data(clusters, triples_dict):
    with open("test_training.csv", "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["triples", "label"])  # CSV header

        for cluster in clusters:
            result = ""
            label = "No"

            for node in cluster:
                edges = triples_dict.get(node, [])
                for p, o in edges:
                    # Build triple string
                    subj = f"<{node}>"
                    pred = f"<{p}>"
                    if isinstance(o, term.Literal):
                        obj = f'"{str(o)}"'
                    else:
                        obj = f"<{o}>"
                    result += f"{subj} {pred} {obj} .\n"

                    # Check if it's a KeyValuePair
                    if obj.find("KeyValue")!=-1:
                        label = "Yes"

            writer.writerow([result.strip(), label])
