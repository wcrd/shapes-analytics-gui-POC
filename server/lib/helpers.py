# Arbitrary depth flatten
# https://stackoverflow.com/questions/10823877/what-is-the-fastest-way-to-flatten-arbitrarily-nested-lists-in-python
def flatten(items, seqtypes=(list, tuple, set), copy=True):
    
    if not isinstance(items, seqtypes): return [items]

    if copy:
        new_items = items.copy()
    else:
        new_items = items
    try:
        for i, x in enumerate(new_items):
            while isinstance(x, seqtypes):
                new_items[i:i+1] = x
                x = new_items[i]
    except IndexError:
        pass
    return new_items

# PRINT DEBUG VERSION
# def flatten(items, seqtypes=(list, tuple, set), copy=True):
#     if not isinstance(items, seqtypes): 
#         print('Non-iterable: ', items)
#         return items

#     if copy:
#         new_items = items.copy()
#     else:
#         new_items = items
#     try:
#         for i, x in enumerate(new_items):
#             while isinstance(x, seqtypes):
#                 print("Iterable: ", x)
#                 new_items[i:i+1] = x
#                 x = new_items[i]
#     except IndexError:
#         pass
#     print("Result: ", new_items)
#     return new_items