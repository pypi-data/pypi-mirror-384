
def build_category_tree_by_id(categories, root_id):
    lookup = {cat.id: cat for cat in categories}
    category = lookup.get(root_id)
    sub_level1 = []
    sub_level2 = []

    if not category:
            return None

    if category.sub_categories:
            for sub_id1 in category.sub_categories:
                sub_category1 = lookup.get(sub_id1)
                print("sub_category1 - ",sub_category1)
                sub_level1.append(sub_category1)

                for sub_id2 in sub_category1.sub_categories:
                    sub_category2 = lookup.get(sub_id2)
                    print("sub_category2 - ",sub_category2)
                    sub_level2.append(sub_category2)


    return category


def build_category_tree(categories, category_id):
    tree = []

    if category_id is not None and category_id != "":
        # Build tree for the given category_id
        node = build_category_tree_by_id(categories, category_id)
        print("node - ", node)
        tree.append(node)
    else:
        # Build tree for all root categories
        for category in categories:
            node = build_category_tree_by_id(categories, category.id)
            print("node - ", node)
            tree.append(node)

    return tree

