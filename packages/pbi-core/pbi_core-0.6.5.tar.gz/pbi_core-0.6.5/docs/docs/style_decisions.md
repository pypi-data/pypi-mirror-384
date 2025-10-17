# Printing pbi_core Elements

1. We use `__repr__` to print basic identifying information about an object. This is typically:
   1. The object's type 
   2. single user-friendly identifying field (generally `name`)
   3. The object's `id` (if it has one)
2. We use `__str__` to print all meaningful information about an object. It's based on the `__repr__` implementation in [attrs](https://www.attrs.org/en/stable/examples.html) and includes all fields except those that are:
   1. `repr=False`. We apply this to metadata fields such as modified_time-type fields and lineage-type fields that are not useful for general PowerBI work.
   2. Fields where the value is set to the default value for that field.