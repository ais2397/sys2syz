#!/usr/bin/env sh

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

SYS2SYZ_PATH=$(pwd)
COMPILE_COMMANDS_PATH=$SYS2SYZ_PATH/compile_commands
TAGS_PATH=$SYS2SYZ_PATH/tags
OUT_PATH=$SYS2SYZ_PATH/out


# if b option is set then there must be a command line argument to define type of os and another one should be the path to the source code

while getopts "b:sc" opt && opt=-${opt} ;
do
	case "${opt}" in
			-b)
				    echo "[+] Running bear and ctags"
					echo "======================"
				    # if b option is set, get the os type and also the path to the source code
					OS_TYPE=$OPTARG
					shift
					SRC_PATH=$2
					shift
				    # Run bear, generate compile_command.json according to the os type
					OS_TYPE=$(echo $OS_TYPE | tr '[:upper:]' '[:lower:]')
					if [ "$OS_TYPE" = "netbsd" ]
					then 
						echo "[+] NetBSD source code path: $SRC_PATH"
						cd $SRC_PATH
						bear -- ./build.sh -j4 -m amd64 -u -U -T ../tools/ -O ../obj/ -R ../release -D ../dest release
						#move compile_commands.json to compile_commands folder and rename it to compile_commands_netbsd.json
						mv compile_commands.json $COMPILE_COMMANDS_PATH/compile_commands_netbsd.json
						echo "[+] compile_commands_netbsd.json generated successfully in $COMPILE_COMMANDS_PATH"
						cd $SYS2SYZ_PATH
					# create ctags file for netbsd src in tags folder
						ctags -R $SRC_PATH > $TAGS_PATH/tags_netbsd
						echo "[+] tags_netbsd generated successfully in $TAGS_PATH"
					elif [ "$OS_TYPE" = "linux" ]
					then
						echo "[+] Linux "
						cd $SRC_PATH
						bear -- make -j4
						#move compile_commands.json to compile_commands folder and rename it to compile_commands_linux.json
						mv compile_commands.json $COMPILE_COMMANDS_PATH/compile_commands_linux.json
						echo "[+] compile_commands_linux.json generated successfully in $COMPILE_COMMANDS_PATH"
						cd $SYS2SYZ_PATH
					# create ctags file for linux src in tags folder
						ctags -R $SRC_PATH > $TAGS_PATH/tags_linux
						echo "[+] tags_linux generated successfully in $TAGS_PATH"
					else
						echo "Operating system ($OS_TYPE) not supported yet !"
						exit
					fi
					;;
			-s)
					# if setup fails dispaly error message to tell user to run with sudo
					echo "Setting up environment"
					echo "======================"
					echo "===> Installing dependencies"
					

					#install apt-get packages required for the tool if not already installed
					#check if bear is installed
					if ! [ -x "$(command -v bear)" ]; then
						echo "Error: bear is not installed." >&2
						echo "[+] Installing bear"
						sudo apt-get install bear
					fi

					#check if ctags is installed
					if ! [ -x "$(command -v ctags)" ]; then
						echo "Error: ctags is not installed." >&2
						echo "[+] Installing universal-ctags"
						sudo apt-get install universal-ctags
					fi
					echo "---------------------------------"

					#install the python environment
					echo "===> Installing python environment"
					python3 -m venv venv
					source venv/bin/activate
					pip install -r requirements.txt
					echo "---------------------------------" 

					#Setup directories
					echo "===> Setting up directories"
					mkdir $COMPILE_COMMANDS_PATH
					mkdir $TAGS_PATH
					mkdir $OUT_PATH
					cd $SYS2SYZ_PATH
					echo "---------------------------------"
					echo "[+] All the compile_commands.json files will be stored in $COMPILE_COMMANDS_PATH"
					echo "[+] All the tags files will be stored in $TAGS_PATH"
					echo "[+] All the output files will be stored in $OUT_PATH"
					echo "Setup complete"
					;;
			-c)
					echo "Cleaning environment"
					echo "======================"
					#remove the python environment
					echo "===> Removing python environment"
					rm -rf venv
					echo "---------------------------------"

					#remove directories
					echo "===> Removing directories"
					read -p "Do you want to remove the compile_commands directory? (y/n) " -n 1 -r
					# if user input is y then remove the directory
					if [[ $REPLY =~ ^[Yy]$ ]]
					then
						rm -rf $COMPILE_COMMANDS_PATH
					fi
					rm -rf $TAGS_PATH
					rm -rf $OUT_PATH
					echo "---------------------------------"
					echo "[+] Cleaned up environment"
					;;
			esac
done
