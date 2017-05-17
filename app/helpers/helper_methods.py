def extract_optional(data_dict, property_name):
    if property_name in data_dict and data_dict[property_name] is not None:
        return data_dict[property_name]
    else:
        return None


def add_quantity(new_quantity, old_quantity):
    if old_quantity is None:
        return new_quantity
    else:
        return old_quantity + new_quantity

def remove_quantity(new_quantity, old_quantity):
    if old_quantity is None:
        return -new_quantity
    else:
        return old_quantity - new_quantity