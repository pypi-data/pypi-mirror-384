Pappardelle
===========

Pappardelle is a Python module that provides helper functions for lists and dates.

![Test status](https://github.com/pockettheories/pappardelle/actions/workflows/python-app.yml/badge.svg)

# Getting Started

Install the Python module with
```commandline
python3 -m pip install pappardelle
```

Then, within your Python (.py) source code, like in this example:
```python
from pappardelle import compare_lists

# Call the imported function:
compare_lists(
    [1, 2, 3],
    [2, 3, 5]
)

# Returns the following
{
    '=': [2, 3],
    '+': [1],
    '-': [5]
}
```

# Change Log
* **Version 0.13**
  * Added value_or_default (because string_or_default only worked with strings)
* **Version 0.12**
  * Added if_whitespace_make_null
* **Version 0.11**
  * string_or_default accepts varargs, instead of only 2 parameters
* **Version 0.9**
  * Added list_first
* **Version 0.8**
  * Renamed deep_copy_dict_no_overwrite to deep_copy_dict
* **Version 0.7**
  * Added deep_copy_dict_no_overwrite
* **Version 0.6**
  * Added get_dict_path
* **Version 0.5**
  * Added make_dict_path, set_dict_path
* **Version 0.4**
  * Added a function decorator for measuring the function execution time
* **Version 0.3**
  * Use date as the default type for day/week/month/year relative functions, and datetime as the default type for hour/minute/second relative functions
* **Version 0.2**
  * compare_lists returns a dictionary with keys: =, +, - (instead of: matched, + -)
  * Added relative date functions
* **Version 0.1**
  * First release with compare_lists and lookup_lists functions

# References

## List Functions

`compare_lists(list1, list2, optional lambda comparator)`

`lookup_lists(list1, list2, optional lambda comparator)`

## Date Functions

`days_before(num_of_days, from_date)`

`days_ago(num_of_days)`

`days_after(num_of_days, from_date)`

`days_since(num_of_days, from_date)`

`tomorrow()`

`yesterday()`

`days_before_at_this_time(num_of_days, from_datetime)`

`days_ago_at_this_time(num_of_days, from_datetime)`

`days_after_at_this_time(num_of_days, from_datetime)`

`days_since_at_this_time(num_of_days, from_datetime)`

`tomorrow_at_this_time()`

`yesterday_at_this_time()`

`hours_before(num_of_hours, from_date)`

`hours_ago(num_of_hours)`

`hours_after(num_of_hours, from_date)`

`hours_since(num_of_hours, from_date)`

`minutes_before(num_of_minutes, from_date)`

`minutes_ago(num_of_minutes)`

`minutes_after(num_of_minutes, from_datee)`

`minutes_since(num_of_minutes, from_date)`

`seconds_before(num_of_seconds, from_date)`

`seconds_ago(num_of_seconds)`

`seconds_after(num_of_seconds, from_date)`

`seconds_since(num_of_seconds, from_date)`

`weeks_before(num_of_weeks, from_date)`

`weeks_ago(num_of_weeks)`

`weeks_after(num_of_weeks, from_date)`

`weeks_since(num_of_weeks, from_date)`

`weeks_before_at_this_time(num_of_weeks, from_datetime)`

`weeks_ago_at_this_time(num_of_weeks, from_datetime)`

`weeks_after_at_this_time(num_of_weeks, from_datetime)`

`weeks_since_at_this_time(num_of_weeks, from_datetime)`

`months_before(num_of_months, from_date)`

`months_ago(num_of_months)`

`months_after(num_of_months, from_date)`

`months_since(num_of_months, from_date)`

`months_before_at_this_time(num_of_months, from_datetime)`

`months_ago_at_this_time(num_of_months, from_datetime)`

`months_after_at_this_time(num_of_months, from_datetime)`

`months_since_at_this_time(num_of_months, from_datetime)`

`years_before(num_of_years, from_date)`

`years_ago(num_of_years)`

`years_after(num_of_years, from_date)`

`years_since(num_of_years, from_date)`

`years_before_at_this_time(num_of_years, from_datetime)`

`years_ago_at_this_time(num_of_years, from_datetime)`

`years_after_at_this_time(num_of_years, from_datetime)`

`years_since_at_this_time(num_of_years, from_datetime)`

## Dictionary Functions

`make_dict_path(a_dict, a_path)`

`set_dict_path(a_dict, a_path, a_val)`

`get_dict_path(a_dict, a_path)`

`deep_copy_dict(a_src, a_dest, optional overwrite)`

`are_dict_equal(first, second)`

## Function Decorators

`exec_time`

## String Functions

`string_or_default(primary_value, secondary_value)`

`is_null_or_whitespace(val)`

`is_null_or_empty(val)`

`str_ignorecase_equals(str1, str2)`

`str_ignorecase_index(str1, str2)`

## Value Functions

`value_or_default(primary_value, secondary_value)`

# Author

My name is Katkam Nitin Reddy. I am a former software developer living (mostly) in Dubai. I created this library for functionality that I find myself re-writing in my scripts.

# Acknowledgement

I would like to thank my mom, Katkam Nita Reddy, and my dad, Katkam Narsing Reddy, who have always motivated me to learn and contribute to the open-source community.

# Examples

## Example 1. Within a Server State Management application

```python
from pappardelle import compare_lists
from pprint import pprint

desired_state = [
  {"package_name": "net-tools"},
  {"package_name": "build-essential"},
  {"package_name": "bind9-dnsutils"}
]

current_state = [
  {"package_name": "build-essential"},
  {"package_name": "squid"}
]

change_plan = compare_lists(
  desired_state,
  current_state,
  lambda x, y: x['package_name'] == y['package_name']
)

pprint(change_plan)

# Output
# {'+': [{'package_name': 'net-tools'}, {'package_name': 'bind9-dnsutils'}],
# '-': [{'package_name': 'squid'}],
# '=': [{'package_name': 'build-essential'}]}
```
