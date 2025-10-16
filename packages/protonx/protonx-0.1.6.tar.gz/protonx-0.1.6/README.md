## Cài đặt công cụ build
```
!pip install build twine
```
## Build package
```
python -m build
```
## Cài đặt thử package local
```
pip install dist/protonx-0.1.3-py3-none-any.whl
```
## Test 

```
import protonx
print(protonx.__version__)
```
