# PyO3 binding

## Local testing

```sh
python3 -m venv --system-site-packages venv
source venv/bin/activate.fish 

pip install maturin
maturin develop

# automatically does the install after a successful build
#pip install ../target/wheels/parse_int_py-0.9.1-cp311-cp311-manylinux_2_34_x86_64.whl 

./example.py
```
