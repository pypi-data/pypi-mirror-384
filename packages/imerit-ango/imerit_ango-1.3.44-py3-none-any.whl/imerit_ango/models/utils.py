from imerit_ango.models.annotate import Answer


def merge_annotations(available_annotations, new_annotations: Answer):
    classification_list = new_annotations.classifications
    object_list = new_annotations.objects
    relation_list = new_annotations.relations

    # Merge Classifications
    classification_schema_ids = []
    for classification in classification_list:
        classification_schema_ids.append(classification["schemaId"])
    classification_schema_ids = list(set(classification_schema_ids))

    for classification in available_annotations["classifications"]:
        if classification["schemaId"] not in classification_schema_ids:
            classification_list.append(classification)

    # Merge Tools
    for tool in available_annotations["tools"]:
            object_list.append(tool)

    # Merge Relations
    for relation in available_annotations["relations"]:
        relation_list.append(relation)

    annotation = Answer(objects=object_list, classifications=classification_list, relations=relation_list)
    return annotation