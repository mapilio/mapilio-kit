set -e
mkdir -p bin
mkdir -p dependencies

#
# install EAC to Equirectangular conversion binary
#
git -C dependencies  clone https://github.com/mapilio/max2sphere-batch.git

make -C dependencies/max2sphere-batch -j4

cp dependencies/max2sphere-batch/MAX2spherebatch bin/
