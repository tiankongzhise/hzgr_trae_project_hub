def filter_data(source_data: list, compare_data: list, compare_cols: dict) -> list:
    """
    Filters source_data by removing elements that match any element in compare_data
    on ALL specified columns.
    
    Args:
        source_data: List of elements to filter (must have get() method)
        compare_data: List of elements to compare against (must have get() method)
        compare_cols: Dictionary specifying columns to compare {source_col: compare_col}
        
    Returns:
        List of elements from source_data that don't match ANY element in compare_data
        on ALL specified columns
    """
    new_data = []
    
    for source_item in source_data:
        is_new = True
        
        for compare_item in compare_data:
            # Check if ALL specified columns match
            all_match = True
            for src_col, cmp_col in compare_cols.items():
                print(f'source_item:{source_item}与compare_item:{compare_item}比较')
                if source_item.get(src_col) != compare_item.get(cmp_col):
                    print(f'all_match:{all_match}')
                    all_match = False
                    break
                print(f'all_match:{all_match}')
            if all_match:
                is_new = False
                break
        
        if is_new:
            new_data.append(source_item)
    
    return new_data

source = [

    {'id': 2, 'name': 'Bob', 'age': 25},
    {'id': 1, 'name': 'Alice', 'age': 30},
    {'id': 3, 'name': 'Charlie', 'age': 35}
]
compare = [
    {'user_id': 1, 'user_name': 'Alice'},
    {'user_id': 2, 'user_name': 'Bob'}
]
cols = {'id': 'user_id', 'name': 'user_name'}

result = filter_data(source, compare, cols)
print(result)
