def is_child_concept(type, parent_type, ontology):
    return type == parent_type or parent_type in ontology["concepts"][type]["parents"]

def get_label_keys(type, ontology):
    parents = set(ontology["concepts"][type]["parents"])
    parents.add(type)
    parents = list(parents)
    parents.reverse()
    label_keys = {} # for guaranteed insertion order
    for parent in parents:
        for label_key in ontology["concepts"][parent]["labelKeys"]:
            if not label_key:
                continue
            label_keys[label_key] = None
    return list(label_keys.keys())
