# 📅 MonthEndDate & WeekendDate Utility

This module provides two lightweight, immutable date wrapper classes — **`MonthEndDate`** and **`WeekendDate`** — designed to normalize arbitrary dates to specific reference points in time (month-end or weekend).
Both classes support comparison (`==`, `<`, etc.) and hashing, allowing them to be used as dictionary keys or in sets.

---

## 🧩 Classes Overview

### **`MonthEndDate`**

A utility class that always represents **the last day of the given month**.

#### ✅ Behavior

* Any date or `(year, month)` input is normalized to that month’s **last calendar day**.
* Useful for financial or reporting systems where month-end aggregation is required.

#### 📘 Example

```python
from your_module import MonthEndDate
import datetime as dt

d = MonthEndDate(2025, 2, 10)
print(d)                # MonthEndDate(2025-02-28)
print(d.to_date())      # datetime.date(2025, 2, 28)

# From arbitrary date
d2 = MonthEndDate.from_date(dt.date(2025, 10, 1))
print(d2)               # MonthEndDate(2025-10-31)
```

#### ⚙️ Comparison

`MonthEndDate` instances can be compared or used interchangeably with `datetime.date`:

```python
MonthEndDate(2025, 3, 5) == dt.date(2025, 3, 31)   # True
MonthEndDate(2025, 3, 5) < MonthEndDate(2025, 4, 1) # True
```

---

### **`WeekendDate`**

A utility class that converts any given date into the **Saturday of that week**,
where the **week starts on Sunday**.

#### ✅ Behavior

* `weekday()` is adjusted so that Sunday = 0, Saturday = 6.
* The resulting date always represents **the Saturday within the same Sunday-starting week**.

#### 📘 Example

```python
from your_module import WeekendDate
import datetime as dt

# Convert arbitrary date to the Saturday of its week
WeekendDate(2025, 10, 12)  # Sunday → 2025-10-18 (Sat)
WeekendDate(2025, 10, 14)  # Tuesday → 2025-10-18 (Sat)
WeekendDate(2025, 10, 18)  # Saturday → 2025-10-18 (Sat)

d = WeekendDate.from_date(dt.date(2025, 10, 19))
print(d.to_date())  # 2025-10-25
```

#### ⚙️ Comparison

`WeekendDate` behaves like a regular `datetime.date` for equality and ordering:

```python
WeekendDate(2025, 10, 15) == dt.date(2025, 10, 18)  # True
WeekendDate(2025, 10, 15) < WeekendDate(2025, 10, 25)  # True
```

---

## 🧠 Design Notes

* Both classes are **immutable** (`__slots__` used, no attribute reassignment).
* Implemented with `functools.total_ordering`, providing rich comparison behavior.
* Fully compatible with Python’s standard `datetime` operations.

---

## 🧾 Typical Use Cases

* Financial data normalization (e.g., aligning transaction dates to month-end).
* Time-series aggregation by reporting period (month/week).
* Generating consistent reference dates for business analytics.

---

## 📦 Dependencies

* Python standard library only:

  * `datetime`
  * `calendar`
  * `functools.total_ordering`
