# xmllens

Deep structural comparison for XML documents with per-path numeric
tolerance and XPath-like targeting.

## Overview

`xmllens` is a lightweight Python library for comparing two XML
documents with **fine-grained tolerance control**.

It supports:

- ✅ Global absolute (`abs_tol`) and relative (`rel_tol`) numeric
  tolerances
- ✅ Per-path tolerance overrides via XPath-like expressions
- ✅ Ignoring volatile or irrelevant XML elements
- ✅ Detailed debug logs that explain *why* two XMLs differ

It’s ideal for comparing configuration files, XML-based API payloads,
or serialized data models where small numeric drifts are expected.

## Installation

    pip install xmllens

## Supported Path Patterns

xmllens implements a simplified subset of XPath syntax:

| Pattern                | Description                    |
| ---------------------- | ------------------------------ |
| `/a/b/c`               | Exact element path             |
| `/items/item[1]/price` | Specific index                 |
| `/items/*/price`       | Any element name               |
| `//price`              | Recursive descent              |
| `/root/*`              | Wildcard for any child element |

## Full API

```
compare_xml(
    xml_a: str,
    xml_b: str,
    *,
    ignore_fields: list[str] = None,
    abs_tol: float = 0.0,
    rel_tol: float = 0.0,
    abs_tol_fields: dict[str, float] = None,
    rel_tol_fields: dict[str, float] = None,
    epsilon: float = 1e-12,
    show_debug: bool = False,
) -> bool
```

| Parameter       | Description                                   |
| --------------- | --------------------------------------------- |
| `xml_a, xml_b`  | XML documents as strings                      |
| `ignore_fields`  | XPath-like patterns to skip during comparison |
| `abs_tol`       | Global absolute numeric tolerance             |
| `rel_tol`       | Global relative numeric tolerance             |
| `abs_tol_fields` | Per-path absolute tolerances                  |
| `rel_tol_fields` | Per-path relative tolerances                  |
| `epsilon`       | Small float to absorb FP rounding errors      |
| `show_debug`    | Enable detailed comparison logs               |

## Examples

```python
from xmllens import compare_xml

xml1 = "<sensor><temp>21.5</temp><humidity>48.0</humidity></sensor>"
xml2 = "<sensor><temp>21.7</temp><humidity>48.5</humidity></sensor>"

# Default tolerances
res = compare_xml(xml1, xml2, abs_tol=0.05, rel_tol=0.01, show_debug=True)
print(res)  # False
```
```bash
### Output (debug)

[NUMERIC COMPARE] /sensor/temp: 21.5 vs 21.7 | diff=0.200000 | abs_tol=0.05 | rel_tol=0.01 | threshold=0.217000
[MATCH NUMERIC] /sensor/temp: within tolerance
[NUMERIC COMPARE] /sensor/humidity: 48.0 vs 48.5 | diff=0.500000 | abs_tol=0.05 | rel_tol=0.01 | threshold=0.485000
[FAIL NUMERIC] /sensor/humidity → diff=0.500000 > threshold=0.485000
[FAIL IN ELEMENT] /sensor/humidity
```

### Simple Value Mismatch

```python
xml1 = "<root><x>1</x></root>"
xml2 = "<root><x>2</x></root>"

result = compare_xml(xml1, xml2)
print(result)  # False
```

### Tag Mismatch

```python
xml1 = "<root><x>1</x></root>"
xml2 = "<root><y>1</y></root>"

result = compare_xml(xml1, xml2)
print(result)  # False
```

### Global Tolerances
#### Absolute Tolerance

```python
xml1 = "<sensor><temp>20.0</temp></sensor>"
xml2 = "<sensor><temp>20.05</temp></sensor>"

result = compare_xml(xml1, xml2, abs_tol=0.1)
print(result)  # True
```

#### Relative Tolerance

```python
xml1 = "<sensor><humidity>100.0</humidity></sensor>"
xml2 = "<sensor><humidity>104.0</humidity></sensor>"

result = compare_xml(xml1, xml2, rel_tol=0.05)
print(result)  # True  (5% tolerance)
```

### Per-Path Tolerances
#### Per-Path Absolute Tolerance

```python
xml1 = "<root><a>1.0</a><b>2.0</b></root>"
xml2 = "<root><a>1.5</a><b>2.9</b></root>"

abs_tol_fields = {"/root/b": 1.0}

result = compare_xml(xml1, xml2, abs_tol=0.5, abs_tol_fields=abs_tol_fields)
print(result)  # True
```

#### Per-Path Relative Tolerance

```python
xml1 = "<values><x>100</x><y>200</y></values>"
xml2 = "<values><x>110</x><y>210</y></values>"

rel_tol_fields = {"/values/x": 0.2}  # 20%

result = compare_xml(xml1, xml2, rel_tol=0.05, rel_tol_fields=rel_tol_fields)
print(result)  # True
```

### Ignoring fields
#### Simple Ignore Path

```python
xml1 = "<root><id>1</id><timestamp>now</timestamp></root>"
xml2 = "<root><id>1</id><timestamp>later</timestamp></root>"

ignore_fields = ["/root/timestamp"]

result = compare_xml(xml1, xml2, ignore_fields=ignore_fields)
print(result)  # True
```

### More Examples

#### Ignore multiple fields with different patterns:

- Exact path: /user/profile/updated_at

- Wildcard: /devices/*/debug

- Recursive: //trace

```python

xml1 = """
<data>
    <user>
        <id>7</id>
        <profile><updated_at>2025-10-14T10:00:00Z</updated_at><age>30</age></profile>
    </user>
    <devices>
        <device><id>d1</id><debug>alpha</debug><temp>20.0</temp></device>
        <device><id>d2</id><debug>beta</debug><temp>20.1</temp></device>
    </devices>
    <sessions>
        <session><events><event><meta><trace>abc</trace></meta><value>10.0</value></event></events></session>
        <session><events><event><meta><trace>def</trace></meta><value>10.5</value></event></events></session>
    </sessions>
</data>
"""

xml2 = """
<data>
    <user>
        <id>7</id>
        <profile><updated_at>2025-10-15T10:00:05Z</updated_at><age>30</age></profile>
    </user>
    <devices>
        <device><id>d1</id><debug>changed</debug><temp>20.05</temp></device>
        <device><id>d2</id><debug>changed</debug><temp>20.18</temp></device>
    </devices>
    <sessions>
        <session><events><event><meta><trace>xyz</trace></meta><value>10.01</value></event></events></session>
        <session><events><event><meta><trace>uvw</trace></meta><value>10.52</value></event></events></session>
    </sessions>
</data>
"""

ignore_fields = [
    "/data/user/profile/updated_at",
    "/data/devices/*/debug",
    "//trace",
]

result = compare_xml(
    xml1, xml2,
    ignore_fields=ignore_fields,
    abs_tol=0.05,
    rel_tol=0.02
)
print(result)  # True
```

#### combining absolute and relative tolerances for different fields.

```python

xml1 = """
<station>
    <id>ST-42</id>
    <location>Paris</location>
    <version>1.0</version>
    <metrics>
        <temperature>21.5</temperature>
        <humidity>48.0</humidity>
        <pressure>1013.2</pressure>
        <wind_speed>5.4</wind_speed>
    </metrics>
    <status><battery_level>96.0</battery_level></status>
</station>
"""

xml2 = """
<station>
    <id>ST-42</id>
    <location>Paris</location>
    <version>1.03</version>
    <metrics>
        <temperature>21.6</temperature>
        <humidity>49.3</humidity>
        <pressure>1013.5</pressure>
        <wind_speed>5.6</wind_speed>
    </metrics>
    <status><battery_level>94.8</battery_level></status>
</station>
"""

abs_tol_fields = {
    "/station/version": 0.1,
    "/station/metrics/humidity": 2.0,
    "/station/status/battery_level": 2.0,
}

rel_tol_fields = {
    "/station/metrics/wind_speed": 0.05,
}

result = compare_xml(
    xml1, xml2,
    abs_tol=0.05,
    rel_tol=0.01,
    abs_tol_fields=abs_tol_fields,
    rel_tol_fields=rel_tol_fields
)
print(result)  # True
```

## Tips

- Elements are compared in order.

- Attributes are compared strictly.

- Whitespace is trimmed before comparison.

- To ignore volatile elements (timestamps, UUIDs, etc.), use ignore_fields.

## License

Apache License 2.0 — © 2025 Mohamed Tahri Contributions welcome 🤝