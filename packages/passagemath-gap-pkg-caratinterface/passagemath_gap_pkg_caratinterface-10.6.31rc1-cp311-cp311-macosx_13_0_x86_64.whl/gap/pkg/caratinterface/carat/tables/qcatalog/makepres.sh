#!/bin/bash

DIRH=`pwd`
PRES=/usb/tilman/c/carat/Transform_to_good_base/scripts/PRES.sh
BASE=$DIRH/BASIS

PATH=$PATH:/usb/matrix/bin/momo/

for x in dir.* ; do

   cd $x

   for y in ordnung.* ; do
      cd $y

         for z in * ; do
            cd $z

            for zz in group.* min.* max.* ; do
               if [ -s $zz ] ; then
                  echo $zz
                  if [ $y == "ordnung.1" ] ; then
                     echo 1x1 > pres.$zz
                     echo 1 >> pres.$zz
                  else
                     $PRES $zz $BASE > pres.$zz
                  fi

               fi
            done

            cd ..
         done
      cd ..
   done

   cd $DIRH

done

rm -f $TMP $TMP2
