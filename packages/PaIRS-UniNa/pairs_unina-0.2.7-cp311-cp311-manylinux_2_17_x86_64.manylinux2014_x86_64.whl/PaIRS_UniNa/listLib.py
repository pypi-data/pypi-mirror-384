from .PaIRS_pypacks import pri
import copy

def list_item_at(lst,ind):
        if ind[0]<len(lst):
            p=lst[ind[0]]
        else: 
            p=None
        if p:
            for i in range(1,len(ind)):
                if ind[i]<len(p):
                    p=p[ind[i]]
                else:
                    p=None
                    break
        return p

def deep_duplicate(lst):
    
    # Recursive function to copy the list
    def recursive_duplicate(sub_lst):
        if isinstance(sub_lst, list):
            copied_sub_lst = []
            for item in sub_lst:
                if isinstance(item, list):
                    # If the item is a list, call recursively on it
                    copied_sub_lst.append(recursive_duplicate(item))
                else:
                    # Check if the item has a 'duplicate' attribute and if it is callable
                    if hasattr(item, 'duplicate') and callable(item.duplicate):
                        copied_sub_lst.append(item.duplicate())
                    else:
                        copied_sub_lst.append(item)
            return copied_sub_lst
        else:
            item=sub_lst
            if hasattr(item, 'duplicate') and callable(item.duplicate):
                return item.duplicate()
            else: return item

    # Call the recursive function on the original input
    return recursive_duplicate(lst)

def copy_at_depth(lst, depth, indexes):
    """Recursively copy elements at the specified depth using given indexes."""
    global error_printed
    error_printed = False
    if not isinstance(indexes,list): indexes=list([indexes])
    
    def recursive_copy(lst, depth, indexes, current_depth=0):
        global error_printed
        if depth < 0:
            if not error_printed:
                pri.Coding.red(f"Error [copy_at_depth]: Depth cannot be negative.")
                error_printed = True
            return None
        elif depth == current_depth:
            copied_elements = []
            error_printed_for=False
            for index in indexes:
                if index < len(lst):
                    copied_elements.append(deep_duplicate(lst[index]))
                else:
                    if not error_printed: pri.Coding.yellow(f"Warning [copy_at_depth]: Index {index} out of range for list at depth {current_depth}.")
                    error_printed_for=True
            error_printed=error_printed_for
            return copied_elements
        elif not any(isinstance(sublist, list) for sublist in lst):
            if not error_printed:
                pri.Coding.red(f"Error [copy_at_depth]: Cannot go deeper into list structure at depth {current_depth}.")
                error_printed = True
            return None
        return [recursive_copy(sublist, depth, indexes, current_depth + 1) for sublist in lst]
    
    return recursive_copy(lst, depth, indexes)

def pop_at_depth(lst, depth, indexes):
    """Recursively pop elements at the specified depth using given indexes."""
    global error_printed
    error_printed = False
    
    def recursive_pop(lst, depth, indexes, current_depth=0):
        global error_printed
        if depth < 0:
            if not error_printed:
                pri.Coding.red(f"Error [pop_at_depth]: Depth cannot be negative.")
                error_printed = True
            return None
        elif depth == current_depth:
            popped_elements = []
            error_printed_for=False
            for index in sorted(indexes, reverse=True):
                if index < len(lst):
                    popped_elements.append(lst.pop(index))
                else:
                    if not error_printed: 
                        pri.Coding.yellow(f"Warning [pop_at_depth]: Index {index} out of range for list at depth {current_depth}.")
                    error_printed_for = True
            error_printed=error_printed_for
            return popped_elements[::-1]  # Reverse to restore original order
        elif not any(isinstance(sublist, list) for sublist in lst):
            if not error_printed:
                pri.Coding.red(f"Error [pop_at_depth]: Cannot go deeper into list structure at depth {current_depth}.")
                error_printed = True
            return None
        return [recursive_pop(sublist, depth, indexes, current_depth + 1) for sublist in lst]
    
    return recursive_pop(lst, depth, indexes)

def insert_at_depth(lst, depth, indexes, values):
    """Recursively insert a value at the specified depth using given indexes."""
    global error_printed, gllst
    error_printed = False
    gllst=lst

    def recursive_insert(lst, depth, indexes, values, current_depth=0):
        global error_printed, gllst
        if depth < 0:
            if not error_printed:
                pri.Coding.red(f"Error [insert_at_depth]: Depth cannot be negative.")
                error_printed = True
            return None
        elif depth == current_depth:
            if isinstance(indexes, list):
                error_printed_for=False
                sorted_data = sorted(zip(indexes, values), key=lambda x: x[0], reverse=True)
                for idx, val in sorted_data:
                    if idx <= len(lst):
                        lst.insert(idx, val)
                    else:
                        lst.append(val)
                        if not error_printed: pri.Coding.yellow(f"Warning [insert_at_depth]: Index {idx} out of range for list at depth {current_depth}.")
                        error_printed_for = True
                error_printed=error_printed_for
            elif isinstance(indexes, int):
                error_printed_for=False
                for val in values:
                    if indexes <= len(lst):
                        lst.insert(indexes, val)
                        indexes += 1
                    else:
                        lst.append(val)
                        if not error_printed: pri.Coding.yellow(f"Warning [insert_at_depth]: Index {indexes} out of range for list at depth {current_depth}.")
                        error_printed_for = True
                error_printed=error_printed_for
        elif not any(isinstance(sublist, list) for sublist in lst):
            if not error_printed:
                pri.Coding.red(f"Error [insert_at_depth]: Cannot go deeper into list structure at depth {current_depth}.")
                error_printed = True
            return None
        else:
            for sublist, val in zip(lst, values):
                recursive_insert(sublist, depth, indexes, val, current_depth + 1)
    
    recursive_insert(lst, depth, indexes, values)

def delete_at_depth(lst, depth, indexes):
    """Recursively delete elements at the specified depth using given indexes."""
    global error_printed
    error_printed = False
    
    def recursive_delete(lst, depth, indexes, current_depth=0):
        global error_printed
        if depth < 0:
            if not error_printed:
                pri.Coding.red(f"Error [delete_at_depth]: Depth cannot be negative.")
                error_printed = True
            return None
        elif depth == current_depth:
            error_printed_for=False
            for index in sorted(indexes, reverse=True):
                if index < len(lst):
                    del lst[index]
                else:
                    if not error_printed: pri.Coding.yellow(f"Warning [delete_at_depth]: Index {index} out of range for list at depth {current_depth}.")
                    error_printed_for = True
            error_printed=error_printed_for
        elif not any(isinstance(sublist, list) for sublist in lst):
            if not error_printed:
                pri.Coding.red(f"Error [delete_at_depth]: Cannot go deeper into list structure at depth {current_depth}.")
                error_printed = True
            return None
        else:
            for sublist in lst:
                recursive_delete(sublist, depth, indexes, current_depth + 1)
    
    recursive_delete(lst, depth, indexes)

def expand_level(lst, level=0, target_length=0):
    """Recursively expand the specified level of depth to the target length."""
    current_depth = get_list_dimension(lst)
    if level >= current_depth:
        pri.Coding.yellow("Warning [expand_level]: Target level exceeds current depth of the list.")
        return
    
    global error_printed
    error_printed = False

    def recursive_expand(lst, level, target_length):
        global error_printed
        if level == 0:
            error_printed=expand_to_length(lst, level, target_length, error_printed)
        else:
            for sublist in lst:
                if isinstance(sublist, list):
                    recursive_expand(sublist, level - 1, target_length)
        return
    recursive_expand(lst, level, target_length)
    return

def expand_to_length(lst:list, level, target_length, error_printed):
    """Expand the length of a list to the target length."""
    
    current_length = len(lst)
    if current_length >= target_length:
        if not error_printed:
            pri.Coding.yellow(f"Warning [expand_to_length]: Target length ({target_length}) is lower than or equal to current length ({current_length}) of the list at the target level ({level}).")
            error_printed=True
    else:
        last_element = lst[-1]
        for _ in range(target_length-current_length):
            lst.append(copy.deepcopy(last_element))
    return error_printed

def create_empty_list_of_dimension(dimension):
    """Create an empty list with the specified depth."""
    if dimension < 1:
        pri.Coding.red("Error [create_empty_list]: Dimension cannot be zero or negative.")
        return None
    
    if dimension == 1:
        return []
    
    return [create_empty_list_of_dimension(dimension - 1)]

def get_list_dimension(lst):
    """Recursively determine the depth of a list."""
    if not isinstance(lst, list):
        return 0
    
    if not lst:
        return 1
    
    return 1+max(get_list_dimension(sublist) for sublist in lst)

def measure_depth_length(lst, depth):
    """Measure the length of a list at a certain depth."""
    if depth == 0:
        return len(lst)
    
    length = 0
    for sublist in lst:
        if isinstance(sublist, list):
            length = max(length,measure_depth_length(sublist, depth - 1))
    return length


if __name__ == "__main__":  
    pri.Time.blue('Start')
    # Esempio di utilizzo
    lst = [
        [['a', 'b', 'c'], ['d', 'e', 'f'], ['1','2','3']], 
        [['g', 'h', 'i'], ['j', 'k', 'l'], ['4','5','6']]
    ]
    depth = 2

    dimension = get_list_dimension(lst)
    print("Dimension of the list:", dimension)

    # Copia
    indexes = [0, 2, 10]
    copied_sublist = copy_at_depth(lst, depth, indexes)
    print("Copied Sublist:", copied_sublist)

    # Pop
    indexes = [1, 2, 11]
    popped_elements = pop_at_depth(lst, depth, indexes)
    print("Popped Elements:", popped_elements)
    print("List after Pop:", lst)

    # Insert
    indexes = [0, 12]
    insert_at_depth(lst, depth, indexes, ['x','y'])
    print("List after Insert:", lst)

    empty_list = create_empty_list_of_dimension(dimension)
    print("Empty List:", empty_list)
    print("Dimension of the list:", get_list_dimension(empty_list))
    insert_at_depth(empty_list, depth, indexes, copied_sublist)
    print("List after Insert:", empty_list)

    # Delete
    indexes = [1, 2, 20]
    delete_at_depth(lst, depth, indexes)
    print("List after Delete:", lst)

    #Expand
    expand_level(lst,level=2,target_length=5)
    print("List after Expand:", lst)

    print("List after Expand: lenght of level 1:", measure_depth_length(lst,1))
    print("List after Expand: lenght of level 2:", measure_depth_length(lst,2))
    pri.Time.blue('End')