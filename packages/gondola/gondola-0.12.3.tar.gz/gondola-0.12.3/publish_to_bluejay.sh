#! /bin/sh 

maturin build --release
scp /srv/gaps/gaps-online-software/gondola-core/rust/gondola-core/target/wheels/gondola-0.11.7-cp311-abi3-manylinux_2_39_x86_64.whl bluejay:gaps-online-software/gander/
