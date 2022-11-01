#!/usr/bin/env sh

# This script sets up the environment required for the tool to run.
usage()
{
	echo "Usage   : $0 [ -b <operating_system> <path_to_kernel_src> ] [-s ] [-c ]"
	echo "Options :  "
	echo "     -b : Run bear, generate compile_command.json, and generate ctags file for the kernel source"
	echo "     -s : Setup the environment for the tool"
	echo "     -c : Clean the environment"
	exit 2
}

if [ $# -eq 0 ]
then
	usage
	exit
fi

SYS2SYZ_PATH=$(pwd)
COMPILE_COMMANDS_PATH=$SYS2SYZ_PATH/compile_commands_dir
TAGS_PATH=$SYS2SYZ_PATH/tags_dir
OUT_PATH=$SYS2SYZ_PATH/out
LOG_PATH=$SYS2SYZ_PATH/logs


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
						#run bear command
						bear -- ./build.sh -j4 -m amd64 -u -U -T ../tools/ -O ../obj/ -R ../release -D ../dest release
						#if bear command is successful, move the compile_commands.json to the compile_commands folder
						if [ $? -eq 0 ]
						then
							echo "[+] Bear ran successfully"
							echo "[+] Moving compile_commands.json to compile_commands folder"
							mv compile_commands.json $COMPILE_COMMANDS_PATH/compile_commands_netbsd.json
							ctags -R 
							if [ $? -eq 0 ]
							then
								echo "[+] Ctags ran successfully"
								echo "[+] Moving tags to tags folder"
								mv tags $TAGS_PATH/tags_netbsd						
							else
								echo "[-] Ctags failed"
							fi	
						else
							echo "[-] Bear command failed"
							exit 1
						fi
						cd $SYS2SYZ_PATH
					# create ctags file for netbsd src in tags folder
					elif [ "$OS_TYPE" = "linux" ]
					then
						echo "[+] Linux "
						cd $SRC_PATH
						bear -- make -j4
						if [ $? -eq 0 ]
						then
							echo "[+] Bear ran successfully"
							echo "[+] Moving compile_commands.json to compile_commands folder"
							mv compile_commands.json $COMPILE_COMMANDS_PATH/compile_commands_linux.json
							ctags -R 
							if [ $? -eq 0 ]
							then
								echo "[+] Ctags ran successfully"
								echo "[+] Moving tags to tags folder"
								mv tags $TAGS_PATH/tags_linux
							else
								echo "[-] Ctags failed"
							fi	
						else
							echo "[-] Bear command failed"
							exit 1
						fi
						cd $SYS2SYZ_PATH
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
					mkdir $LOG_PATH
					mkdir $OUT_PATH
					cd $SYS2SYZ_PATH
					echo "---------------------------------"
					echo "[+] All the compile_commands.json files will be stored in $COMPILE_COMMANDS_PATH"
					echo "[+] All the tags files will be stored in $TAGS_PATH"
					echo "[+] All the log files will be stored in $LOG_PATH"
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
					#get user confirmation before removing the directories
					#delete the directories if they exist
					if [ -d "$COMPILE_COMMANDS_PATH" ]
					then	
						echo "Do you want to remove the compile_commands directory? (y/n) "
						read -r response
					# if user input is y then remove the directory
						if [ "$response" = "y" ]
						then
							rm -rf $COMPILE_COMMANDS_PATH
						fi
					fi
					if [ -d "$TAGS_PATH" ]
					then
						rm -rf $TAGS_PATH
					fi
					if [ -d "$LOG_PATH" ]
					then
						rm -rf $LOG_PATH
					fi
					if [ -d "$OUT_PATH" ]
					then
						rm -rf $OUT_PATH
					fi

					echo "---------------------------------"
					echo "[+] Cleaned up environment"
					;;
			esac
done
