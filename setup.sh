#!/bin/bash

# This script sets up the environment required for the tool to run.
usage()
{
	echo "Usage   : $0 [ -b <path_to_netbsd_src> ] [-s ] [-c ]"
	echo "Options :  "
	echo "     -b : Run bear, generate compile_command.json"
	echo "     -s : Setup"
	echo "     -c : Clean"
	exit 2
}

if [ $# -eq 0 ]
then
	usage
	exit
fi

while getopts "b:sc" opt ;
do
	case "${opt}" in
			b)
					SYS2SYZ_PATH=$(pwd)
					echo "Generating compile_commands.json"
					cd ${OPTARG}
					bear ./build.sh -j4 -m amd64 -u -U -T ../tool/ -O ../obj/ -R ../release -D ../dest/ modules
					mv compile_commands.json $SYS2SYZ_PATH/.
					cd $SYS2SYZ_PATH
					;;
			s)
					apt-get install -y bear
					;;
			c)
					rm compile_commands.json
					;;
			esac
done
