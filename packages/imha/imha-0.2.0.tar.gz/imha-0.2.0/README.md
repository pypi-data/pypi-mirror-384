imha
====

A more constrained and friendlier fork of ImageHash.

imha is constrained to not use numpy and keep dependencies to a minimum. This
keeps the package simpler and also easier to be installed on limited
environments. imha also offers more customization for parametrizing the hash
computation and a better engineered hash representation that can be easily
converted to different types and representations.

Usage
-----

As a Python package:

```python
>>> from PIL import Image
>>> import imha
>>> hash1 = imha.average_hash(Image.open("photo1.jpg"))
>>> hash1.bin()
'1111111111010111100100011000000110000001110010011111111111111111'
>>> hash1.hex()
'ffd7918181c9ffff'
>>> hash1.uint()
18435363585078722559
>>> bytes(hash1)
b'\xff\xd7\x91\x81\x81\xc9\xff\xff'
>>> int(hash1)
-11380488630829057
>>> len(hash1)  # hash length in bits
64
>>> hash2 = imha.average_hash(Image.open("photo2.jpg"))
>>> hash2.hex()
'9f172786e71f1e00'
>>> hash1 == hash2
False
>>> hash1 - hash2  # hamming distance between hashes
33
```

As a command-line tool:

```
$ imha --help
usage: imha [--size WIDTH HEIGHT] [--skip-corners] [--format FORMAT] ALGORITHM FILE [FILE ...]

A more constrained and friendlier fork of ImageHash.

positional arguments:
  ALGORITHM            one of: average_hash, dhash, dhash_vertical
  FILE                 input file(s)

options:
  -h, --help           show this help message and exit
  --version            show program's version number and exit
  --size WIDTH HEIGHT  dimensions to resize the image to (default: see API Reference)
  --skip-corners       ignore the four corners
  --format FORMAT      output format, one of: bin, hex, uint, int (default: hex)

$ imha average_hash *.jpg
ffd7918181c9ffff  photo1.jpg
9f172786e71f1e00  photo2.jpg
```

Goals
-----

* Generate the same hash values as ImageHash.
* Require only the pillow package.
* Be compatible with currently supported Python versions.

API Reference
-------------

### average\_hash

```python
def average_hash(
    image: Image.Image, size: tuple[int, int] = (8, 8), *, skip_corners: bool = False
) -> Hash
```

Compute [Average Hash].

Computes hash with `width*height` bits. Enabling `skip_corners` reduces the hash
length by 4 bits. This means a 64-bits hash can be generated with `size=(8, 8)`
or a 16-bit hash be generated with either `size=(4, 4)` or
`size=(5, 4), skip_corners=True` for example.

**Arguments**:

- `image`: Input image.
- `size`: Tuple with width and height to resize the image to. (default:
  `(8, 8)`)
- `skip_corners`: Ignore the four corners. (default: `False`)

### dhash

```python
def dhash(
    image: Image.Image, size: tuple[int, int] = (9, 8), *, skip_corners: bool = False
) -> Hash
```

Compute [Difference Hash] by row.

Computes row hash with `(width-1)*height` bits. Enabling `skip_corners `reduces
the hash length by 4 bits. This means a 64-bits hash can be generated with
`size=(9, 8)` or a 16-bit hash be generated with either `size=(5, 4)` or
`size=(6, 4), skip_corners=True` for example.

**Arguments**:

- `image`: Input image.
- `size`: Tuple with width and height to resize the image to. (default:
  `(9, 8)`)
- `skip_corners`: Ignore the four corners. (default: `False`)

### dhash\_vertical

```python
def dhash_vertical(
    image: Image.Image, size: tuple[int, int] = (8, 9), *, skip_corners: bool = False
) -> Hash
```

Compute [Difference Hash] by column.

Computes col hash with `width*(height-1)` bits. Enabling `skip_corners `reduces
the hash length by 4 bits. This means a 64-bits hash can be generated with
`size=(8, 9)` or a 16-bit hash be generated with either `size=(4, 5)` or
`size=(5, 5), skip_corners=True` for example.

**Arguments**:

- `image`: Input image.
- `size`: Tuple with width and height to resize the image to. (default:
  `(8, 9)`)
- `skip_corners`: Ignore the four corners. (default: `False`)


### Hash Objects

```python
class Hash()
```

Represents a hash object.

The hash value can be converted to various types and representations using the
built-in functions and provided methods. The hamming distance between hashes can
be computed by subtracting one hash from another.

### \_\_init\_\_

```python
def __init__(value: int, len_: int) -> None
```

Create hash object.

**Arguments**:

- `value`: The hash as an unsigned integer value.
- `len_`: The hash length in bits.

### bin

```python
def bin() -> str
```

Return the hash binary representation.

### hex

```python
def hex() -> str
```

Return the hash hexadecimal representation.

### uint

```python
def uint() -> int
```

Return the hash as an unsigned integer value.

### \_\_len\_\_

```python
def __len__() -> int
```

Return `len(self)`, the hash length in bits.

### \_\_sub\_\_

```python
def __sub__(other: Self) -> int
```

Return `self - other`, the hamming distance between hashes.

### \_\_eq\_\_

```python
def __eq__(other: Any) -> bool
```

Return `self == other`.

### \_\_hash\_\_

```python
def __hash__() -> int
```

Return `hash(self)`.

### \_\_bytes\_\_

```python
def __bytes__() -> bytes
```

Return `bytes(self)`, the hash as bytes.

### \_\_int\_\_

```python
def __int__() -> int
```

Return `int(self)`, the hash as a signed integer value.

### \_\_index\_\_

```python
def __index__() -> int
```

Return integer for `bin(self)`, `hex(self)` and `oct(self)`.

### \_\_repr\_\_

```python
def __repr__() -> str
```

Return `repr(self)`.

### \_\_str\_\_

```python
def __str__() -> str
```

Return `str(self)`.

[Average Hash]: https://www.hackerfactor.com/blog/index.php?/archives/432-Looks-Like-It.html
[Difference Hash]: https://www.hackerfactor.com/blog/index.php?/archives/529-Kind-of-Like-That.html
