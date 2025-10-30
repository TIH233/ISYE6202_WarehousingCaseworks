# KeyError: Index Mismatch Due to Leading Whitespace

**Date:** 2025-10-30
**File:** `/case03/Task1/CapacityPlanning.ipynb`
**Cell:** Cell 10
**Error Type:** `KeyError: 'P1'`

---

## Error Output Traceback

```python
KeyError: 'P1'
---------------------------------------------------------------------------
KeyError                                  Traceback (most recent call last)
File ~/Documents/Working Projects/ISYE6202/venv/lib/python3.12/site-packages/pandas/core/indexes/base.py:3812, in Index.get_loc(self, key)
   3811 try:
-> 3812     return self._engine.get_loc(casted_key)
   3813 except KeyError as err:

File pandas/_libs/index.pyx:167, in pandas._libs.index.IndexEngine.get_loc()

File pandas/_libs/index.pyx:196, in pandas._libs.index.IndexEngine.get_loc()

File pandas/_libs/hashtable_class_helper.pxi:7088, in pandas._libs.hashtable.PyObjectHashTable.get_item()

File pandas/_libs/hashtable_class_helper.pxi:7096, in pandas._libs.hashtable.PyObjectHashTable.get_item()

KeyError: 'P1'

The above exception was the direct cause of the following exception:

KeyError                                  Traceback (most recent call last)
Cell In[13], line 8
      4 time_matrix = pd.DataFrame(index=timecost.index, columns=timecost.columns)
      7 for part in timecost.index: # use label indexing but can also use integer iloc
----> 8     time_matrix.loc[part] = timecost.loc[part] * part_demand.loc[part, 'Part_Weekly_Capacity']
     11 step_total_time = {}
     13 # Get unique steps (A, B, C, etc.) excluding NaN

File ~/Documents/Working Projects/ISYE6202/venv/lib/python3.12/site-packages/pandas/core/indexing.py:1184, in _LocationIndexer.__getitem__(self, key)
   1182     key = tuple(com.apply_if_callable(x, self.obj) for x in key)
   1183     if self._is_scalar_access(key):
-> 1184         return self.obj._get_value(*key, takeable=self._takeable)
   1185     return self._getitem_tuple(key)
   1186 else:
   1187     # we by definition only have the 0th axis

File ~/Documents/Working Projects/ISYE6202/venv/lib/python3.12/site-packages/pandas/core/frame.py:4232, in DataFrame._get_value(self, index, col, takeable)
   4226 engine = self.index._engine
   4228 if not isinstance(self.index, MultiIndex):
   4229     # CategoricalIndex: Trying to use the engine fastpath may give incorrect
   4230     #  results if our categories are integers that dont match our codes
   4231     # IntervalIndex: IntervalTree has no get_loc
-> 4232     row = self.index.get_loc(index)
   4233     return series._values[row]
   4235 # For MultiIndex going through engine effectively restricts us to
   4236 #  same-level tuples; see test_get_set_value_no_partial_indexing

File ~/Documents/Working Projects/ISYE6202/venv/lib/python3.12/site-packages/pandas/core/indexes/base.py:3819, in Index.get_loc(self, key)
   3814     if isinstance(casted_key, slice) or (
   3815         isinstance(casted_key, abc.Iterable)
   3816         and any(isinstance(x, slice) for x in casted_key)
   3817     ):
   3818         raise InvalidIndexError(key)
-> 3819     raise KeyError(key) from err
   3820 except TypeError:
   3821     # If we have a listlike key, _check_indexing_error will raise
   3822     #  InvalidIndexError. Otherwise we fall through and re-raise
   3823     #  the TypeError.
   3824     self._check_indexing_error(key)

KeyError: 'P1'
```

---

## Error Interpretation

### What Happened?

The error occurred when trying to access `part_demand.loc[part, 'Part_Weekly_Capacity']` where `part = 'P1'`. Pandas raised a `KeyError` indicating it could not find the index label `'P1'` in the `part_demand` DataFrame.

### Why Did It Happen?

The root cause was an **index mismatch due to leading whitespace**:

1. **`timecost.index`**: Contains clean part names without whitespace
   ```python
   Index(['P1', 'P2', 'P3', ..., 'P20'], dtype='object', name='Part')
   ```

2. **`part_demand.index`**: Contains part names with leading spaces
   ```python
   Index([' P1', ' P2', ' P3', ..., ' P20'], dtype='object')
   ```

3. When iterating through `timecost.index`, the loop variable `part` had the value `'P1'` (no space)

4. Attempting to access `part_demand.loc['P1', 'Part_Weekly_Capacity']` failed because the actual index value was `' P1'` (with leading space)

### Source of the Problem

The leading whitespace originated from the **BOM.csv file**, which was loaded in Cell 4:

```python
bom_df = pd.read_csv('../Data/BOM.csv', index_col=0).T
```

After transposing, the row indices (which became column names, then later used as index for `part_demand`) contained leading spaces like `' P1'`, `' P2'`, etc.

---

## Diagnosis Steps

### Step 1: Initial Error Observation
The error message pointed to line 8 in Cell 10:
```python
time_matrix.loc[part] = timecost.loc[part] * part_demand.loc[part, 'Part_Weekly_Capacity']
```

### Step 2: Verify DataFrame Structure
Added diagnostic code in Cell 9 to inspect the indices:
```python
print("Timecost index:", timecost.index)
print("Part_demand keys:", part_demand.keys())
print("Part_demand index:", part_demand.index)
```

**Output revealed:**
```
Timecost index: Index(['P1', 'P2', 'P3', ...], dtype='object', name='Part')
Part_demand index: Index([' P1', ' P2', ' P3', ...], dtype='object')
                          ↑ Notice the leading space!
```

### Step 3: Identify Root Cause
The diagnostic output clearly showed:
- `timecost.index` values: `'P1'`, `'P2'`, etc. (no spaces)
- `part_demand.index` values: `' P1'`, `' P2'`, etc. (with leading spaces)

This mismatch caused pandas to fail when looking up `'P1'` in an index that only contained `' P1'`.

---

## Troubleshooting & Solution

### Solution: Strip Whitespace from Index

Added one line to Cell 6, right after creating `part_demand`:

```python
# Fix: Strip whitespace from the index
part_demand.index = part_demand.index.str.strip()
```

### Complete Fixed Cell 6:

```python
# calculate the target capacity for products
Z_score = norm.ppf(0.995)

demand_df['Weekly_std'] = demand_df['Weekly_Mean'] * demand_df['Weekly_CV']
# round up to maintain integer
demand_df['Product_Capacity'] = np.ceil(demand_df['Weekly_Mean'] + demand_df['Weekly_std']*Z_score)

# Aggregate to parts demand
part_demand = pd.DataFrame()
part_demand['Part_Weekly_Capacity'] = bom_df.dot(demand_df['Product_Capacity'])
part_demand['Part_Weekly_Capacity'] = np.ceil(part_demand['Part_Weekly_Capacity'])

# Fix: Strip whitespace from the index
part_demand.index = part_demand.index.str.strip()

print('weekly capacity for each product:\n', demand_df['Product_Capacity'])
print('\nweekly capacity for each part:\n', part_demand)
```

### How It Works:

- `part_demand.index.str.strip()`: Uses pandas string accessor to strip leading and trailing whitespace from all index values
- The index transforms from `[' P1', ' P2', ...]` to `['P1', 'P2', ...]`
- Now both `timecost.index` and `part_demand.index` have matching values
- The lookup in Cell 10 succeeds: `part_demand.loc['P1', 'Part_Weekly_Capacity']` finds `'P1'` correctly

---

## Verification Steps

After applying the fix:

1. **Re-run Cell 6**: Apply the whitespace stripping fix
2. **Re-run Cell 9**: Verify the indices now match:
   ```python
   # Should now show:
   Part_demand index: Index(['P1', 'P2', 'P3', ...], dtype='object')
   # No more leading spaces!
   ```
3. **Re-run Cell 10**: The calculation should now complete without errors

---

## Key Takeaways

1. **Always inspect data sources**: CSV files can contain unexpected whitespace
2. **Use diagnostic prints**: When encountering KeyErrors with indices, print both the key being searched and the actual index values
3. **String methods are your friend**: Pandas `.str.strip()`, `.str.lstrip()`, `.str.rstrip()` are essential for cleaning string indices
4. **Preventive measures**: Consider adding `.str.strip()` routinely when loading CSV data with string indices:
   ```python
   df = pd.read_csv('file.csv', index_col=0)
   df.index = df.index.str.strip()  # Clean immediately after loading
   ```

---

## Alternative Solutions

### Option 1: Fix at Source (BOM.csv loading)
```python
bom_df = pd.read_csv('../Data/BOM.csv', index_col=0).T
bom_df.columns = bom_df.columns.str.strip()  # Clean column names
```

### Option 2: Use Integer Indexing
```python
# Instead of label-based indexing
for i, part in enumerate(timecost.index):
    time_matrix.iloc[i] = timecost.iloc[i] * part_demand.iloc[i, 0]
```

### Option 3: Clean the CSV File Itself
Edit the BOM.csv file to remove leading spaces from part names.

---

## Related Issues to Watch For

- Column name mismatches due to whitespace
- Case sensitivity issues (e.g., `'P1'` vs `'p1'`)
- Trailing whitespace (less common but possible)
- Tab characters or other non-visible whitespace
- Unicode spaces (non-breaking spaces, etc.)

---

**Resolution Status:** ✅ Resolved
**Solution Applied:** Added `part_demand.index = part_demand.index.str.strip()` to Cell 6
