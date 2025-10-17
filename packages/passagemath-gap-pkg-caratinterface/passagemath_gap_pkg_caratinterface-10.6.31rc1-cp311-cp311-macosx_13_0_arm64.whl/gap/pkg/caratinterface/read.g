#############################################################################
##
#W  read.g                 Interface to Carat                   Franz G"ahler
##
#Y  Copyright (C) 1999-2012,  Franz G"ahler, Mathematik, Bielefeld University
##

# location of CARAT binaries
BindGlobal( "CARAT_BIN_DIR", DirectoriesPackagePrograms( "CaratInterface" ) );

# directory for temporary files created by interface routines
BindGlobal( "CARAT_TMP_DIR", DirectoryTemporary() );

# low level CARAT interface routines
ReadPackage( "CaratInterface", "gap/carat.gi" );

# methods for functions declared in GAP library
ReadPackage( "CaratInterface", "gap/methods.gi" );


