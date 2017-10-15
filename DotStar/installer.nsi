# name installer
OutFile "installer.exe"

# set desktop as install directory
InstallDir $PROGRAMFILES\DotStar
 
#    # call UserInfo plugin to get user info.  The plugin puts the result in the stack
#    UserInfo::getAccountType
#   
#    # pop the result from the stack into $0
#    Pop $0
# 
#    # compare the result with the string "Admin" to see if the user is admin.
#    # If match, jump 3 lines down.
#    StrCmp $0 "Admin" +3
# 
#    # if there is not a match, print message and return
#    MessageBox MB_OK "not admin: $0"
#    Return
# 
#    # otherwise, confirm and return
#    MessageBox MB_OK "is admin"

# default section start
Section
 
# define output path
SetOutPath $INSTDIR
 
# specify file to go in output path
File /r *
 
# define uninstaller name
WriteUninstaller $INSTDIR\uninstaller.exe

# default section end
SectionEnd

# create a section to define what the uninstaller does.
# the section will always be named "Uninstall"
Section "Uninstall"
 
# Always delete uninstaller first
Delete $INSTDIR\uninstaller.exe
 
# now delete installed file
Delete /r $INSTDIR\*
 
SectionEnd