@echo off

REM Script to install anaconda distribution, EBC Python packages (uesgraphs, TEASER, pyCity...) and their dependencies.
REM Before you start the script you have to:
REM 1. Add your pathes and file names to ALL sections holding ## User Input Start ##
REM 2. Uncomment Pause and Exit statement at beginning of script (with REM)
REM 3. Run script via double click.
REM Important: Please do NOT add commands, which might harm your system or intallation, such as automatic deleting of files and folders!
REM If you need to delete files or folders, do so manually after running the script.

REM ##############################################################
REM Uncomment exit, if you want to run the script (please check the corresponding pathes, first)
echo Uncomment Exit statment in source code, 
echo if you want to run the script (please check the corresponding pathes, first)
Pause
REM Uncomment here:
echo Going to exit script, now.
Pause
Exit
REM Uncomment end

REM ## User Input Start ##
REM ##############################################################
REM Define Python path for specific installation (used to install anaconda distribution)
SET py_path=D:\Remote-User\jsc\Python\anaconda_36_64_bit
REM ## User Input End ##
REM ##############################################################

REM generate path, if not existent
if not exist "%py_path%" mkdir "%py_path%"

REM ##############################################################
REM Define what you would like to install

REM ## User Input Start ##
REM ##############################################################
set install_anaconda=1
REM install_anaconda=0: Do NOT install anaconda
REM install_anaconda=1: Do install anaconda (requires path to anaconda distribution)
REM As anaconda is installed manually, you have to define the same installation path
REM within anaconda installer as py_path, which is set above.

set update_conda_pip=1
REM update_conda_pip=0: Do NOT update conda and pip
REM update_conda_pip=1: Update conda and pip

set install_gurobi=1
REM install_gurobi=0: Do NOT install gurobi
REM install_gurobi=1: Do install gurobi (with conda)

set pycity_install=1
REM pycity_install=0: Only install pycity (with egglink to specific path)
REM pycity_install=1: Clone all pycity repos AND install them with specific pathes)

set use_v_env=0
REM use_v_env=0: Use root anaconda environment
REM use_v_env=1: Generate new conda environment and use this one for installation

REM ## User Input End ##
REM ##############################################################


REM ##############################################################
REM Install anaconda

REM ## User Input Start ##
REM ##############################################################
REM Define path to your anaconda.exe folder (folder, where anaconda.exe is stored)
REM Only necessary if install_anaconda == 1
set anaconda_path=D:\ICT\Downloads
REM Define anaconda.exe name
set anaconda_fname=Anaconda3-4.4.0-Windows-x86_64.exe
REM ## User Input End ##
REM ##############################################################

REM combine path and name
set anac_exe_path=%anaconda_path%\%anaconda_fname%

IF %install_anaconda%==1 (
echo Install anaconda
start "" "%anac_exe_path%"
echo Please go through the installation process
echo Please wait until anaconda has been installed, before you continue this batch script!
echo You need to install anaconda into Python path "%py_path%"
Pause
)



REM ###########################################################################
REM Go to conda path (if conda cannot be set as system Python path)
cd /d %py_path%\Scripts

IF %update_conda_pip%==1 (
REM Update conda
echo Update conda
conda update conda

REM Update pip
echo Update pip
start "" "%py_path%\Python.exe" -m pip install --upgrade pip
)



REM ###########################################################################
REM Virtual conda environment

REM ## User Input Start ##
REM ##############################################################
REM Define virtual env. name
REM Only necessary, if you want to install a virtual environment in conda distribution
REM e.g. when you need to use Gurobi, which currently only holds Python 3.5 interface, 
REM but you had to install anaconda 3.6 distribution. In this case you can install a
REM virtual environment with Python 3.5 to perform the gurobipy installation.
set v_env_name=py35
REM Define your Python version
set py_v_version=3.5
REM ## User Input End ##
REM ##############################################################


REM Generate virtual environment
IF %use_v_env%==1 (
echo Generate virtual conda environment
REM Define your virtual environment here!
conda create --name %v_env_name% python=%py_v_version% anaconda

cd %py_path%\envs\%v_env_name%\Scripts
Call activate %v_env_name%
REM Re-define python installation path to virtual environment
set py_path_new=%py_path%\envs\%v_env_name%
echo Set installation python path to virtual environment %v_env_name%
)

REM If no virtual environment should be used, 
IF %use_v_env%==0 (
set py_path_new=%py_path%
)

REM Install some python dependencies
REM ##############################################################
echo Beginn installing special Python packages
echo Thus, some Python cmd windows are going to be opened
echo Please wait, until specific Python package is installed (Python cmd window is closed)
echo before you continue (as some packages depend on other packages)


echo Install mako
REM conda install mako (for TEASER)
start "" "%py_path_new%\Python.exe" -m pip install mako
Pause

echo Install pyxb
REM conda install pyxb (for TEASER)
start "" "%py_path_new%\Python.exe" -m pip install pyxb
Pause

echo Install pyomo
REM conda install pyomo (for pyCity_opt)
start "" "%py_path_new%\Python.exe" -m pip install pyomo
Pause

REM Install wheel data (Python)
REM #############################################################
REM Go to: http://www.lfd.uci.edu/~gohlke/pythonlibs/
REM Download shaeply and pyproj wheel data
REM D:\ICT\wheel_data\

REM ## User Input Start ##
REM ##############################################################
REM Define folder, where shapely and pyproj wheels are stored
set path_shp_proj=D:\example_path

REM Define shapely wheel file name
set shp_wheel=Shapely-1.5.17-cp36-cp36m-win_amd64.whl

REM Define shapely wheel file name
set pyproj_wheel=pyproj-1.9.5.1-cp36-cp36m-win_amd64.whl

REM ## User Input End ##
REM ##############################################################

REM Combine path and filename
set shp_load=%path_shp_proj%\%shp_wheel%

REM Combine path and filename
set pyproj_load=%path_shp_proj%\%pyproj_wheel%


echo Install Shapely wheel
start "" "%py_path_new%\Python.exe" -m pip install %shp_load%
Pause

echo Install pyproj wheel
start "" "%py_path_new%\Python.exe" -m pip install %pyproj_load%
Pause

REM Configuration Gurobi
REM #############################################################
IF %install_gurobi%==1 (
echo Install gurobi with conda

cd %py_path_new%\Scripts

call conda config --add channels http://conda.anaconda.org/gurobi
call conda install gurobi
)




REM define path to clone and install all relevant EBC Python GIT repos 
REM ##############################################################

REM ## User Input Start ##
REM ##############################################################
REM Set installation path for Python repositories
set path_git_install=D:\Remote-User\jsc\GIT
REM If you already have local repositories of uesgraphs, TEASER, pyCity,
REM e.g. cloned via PyCharm etc., you can just use the path, where these
REM repos are stored locally and define it as path_git_install. Moreover,
REM you MUST SET pycity_install=0, as you should prevent cloning all repos,
REM again!
REM If you have no repos cloned, so far, set pycity_install=1, then all
REM repos are going to be cloned into path_git_install, which should be 
REM an EMPTY folder path!
REM ## User Input End ##
REM ##############################################################


REM generate path, if not existent
if not exist "%path_git_install%" mkdir "%path_git_install%"


REM Change directory to install path
cd /d %path_git_install%

REM Install UESgraphs
REM ##############################################################

IF %pycity_install%==1 (
echo Clone uesgraphs
git clone git@github.com:RWTH-EBC/uesgraphs.git  
REM https://github.com/RWTH-EBC/uesgraphs.git
)


Pause

cd uesgraphs

echo %cd%
echo Install uesgraphs
start "" ""%py_path_new%"\Python.exe" -m pip install -e %cd%

cd ..

REM Install richardsonpy
REM ##############################################################

IF %pycity_install%==1 (
echo Clone richardsonpy
git clone git@github.com:RWTH-EBC/richardsonpy.git
REM https://github.com/RWTH-EBC/richardsonpy.git
)


Pause

cd richardsonpy

echo %cd%
echo Install richardsonpy
start "" ""%py_path_new%"\Python.exe" -m pip install -e %cd%

cd ..


REM Install pycity
REM ##############################################################

IF %pycity_install%==1 (
echo Clone pycity
git clone git@github.com:RWTH-EBC/pyCity.git 
REM https://github.com/RWTH-EBC/pyCity.git
)


Pause

cd pycity

echo %cd%
echo Install pycity
start "" ""%py_path_new%"\Python.exe" -m pip install -e %cd%

cd ..

REM TEASER
REM ##############################################################

IF %pycity_install%==1 (
echo Clone teaser
git clone git@github.com:RWTH-EBC/TEASER.git
REM https://github.com/RWTH-EBC/TEASER.git
)

Pause

cd teaser

git checkout issue297_vdi_core_dev_jsc
echo Switch to issue297_vdi_core_dev_jsc branch to enable VDI 6007 usage

echo %cd%
echo Install teaser
start "" ""%py_path_new%"\Python.exe" -m pip install -e %cd%

cd ..

REM Install PyCity_Calc
REM ##############################################################

IF %pycity_install%==1 (
echo Clone pycity_calc
git clone git@github.com:RWTH-EBC/pyCity_calc.git
REM https://github.com/RWTH-EBC/pyCity_calc.git
)

Pause

cd pycity_calc

git checkout development
echo Switch to development branch

echo %cd%
echo Install pycity_calc
start "" ""%py_path_new%"\Python.exe" -m pip install -e %cd%

cd ..

REM Install PyCity_Opt
REM ##############################################################

IF %pycity_install%==1 (
echo Clone pycity_opt
git clone git@github.com:RWTH-EBC/pyCity_opt.git
REM https://github.com/RWTH-EBC/pyCity_opt.git
)

Pause

cd pycity_opt

git checkout development

echo %cd%
echo Install pycity_opt
start "" ""%py_path_new%"\Python.exe" -m pip install -e %cd%

cd ..


REM Pause
PAUSE
