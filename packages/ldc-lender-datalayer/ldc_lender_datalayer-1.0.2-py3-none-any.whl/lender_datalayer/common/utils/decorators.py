"""
Data Layer Decorators Module

This module contains decorator functions used by data layer mappers.
Only includes decorators that are actually used in the data layer.
"""

import logging
from functools import wraps

logger = logging.getLogger('normal')


def data_dict_to_string_wrapper(query_conditions_arg, case_check=None):
    def data_dict_to_string(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            case_checks = kwargs.get(case_check, None)
            query_conditions = kwargs[query_conditions_arg]
            query_conditions_dict = {
                'params': query_conditions,
                'query_conditions_string': None
            }

            if not case_checks:
                query_conditions_dict['query_conditions_string'] = [f'{key} = %({key})s'
                     for key, value in query_conditions.items()]
            else:
                query_conditions_list = []
                for key, value in query_conditions.items():
                    if key in case_checks:
                        cast_value = case_checks[key]
                        query_conditions_list.append(f'{cast_value}({key}) = %({key})s')
                    else:
                        query_conditions_list.append(f'{key} = %({key})s')
                
                query_conditions_dict['query_conditions_string'] = query_conditions_list
            
            query_conditions_dict['query_conditions_string'] = ','.join(
                query_conditions_dict['query_conditions_string'])

            kwargs[query_conditions_arg] = query_conditions_dict
            return function(*args, **kwargs)
        return wrapper
    return data_dict_to_string

