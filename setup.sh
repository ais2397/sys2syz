#!/bin/bash

# This script sets up the environment required for the tool to run.

echo "Installing requirements for c2xml"
mkdir requirements && cd requirements
echo "[+] Installing bison"
wget ftp://ftp.gnu.org/gnu/m4/m4-1.4.10.tar.gz
tar -xvzf m4-1.4.10.tar.gz
cd m4-1.4.10
./configure --prefix=/usr/local/m4
make
sudo make install
cd ../
wget https://ftp.gnu.org/gnu/bison/bison-3.2.tar.gz
tar -xvzf bison-3.2.tar.gz
cd bison-3.2
PATH=$PATH:/usr/local/m4
./configure --prefix=/usr/local/bison --with-libiconv-prefix=/usr/local/libiconv/\n
make
sudo make install
cd  ..
echo "[+] Installing boost"
wget https://dl.bintray.com/boostorg/release/1.69.0/source/boost_1_69_0.tar.gz
tar -zxvf boost_1_69_0.tar.gz
cd boost_1_69_0
./bootstrap.sh
./b2 stage -j2 threading=multi link=shared
cd ..
echo "[+] Installing re2c"
wget http://archive.ubuntu.com/ubuntu/pool/main/r/re2c/re2c_1.3-1build1_amd64.deb
sudo dpkg -i re2c_1.3-1build1_amd64.deb
cd ../

PATH=/usr/local/bison/bin/:$PATH\n

echo "Installing c2xml"
git clone https://github.com/mizkichan/c2xml.git
cd c2xml
make 