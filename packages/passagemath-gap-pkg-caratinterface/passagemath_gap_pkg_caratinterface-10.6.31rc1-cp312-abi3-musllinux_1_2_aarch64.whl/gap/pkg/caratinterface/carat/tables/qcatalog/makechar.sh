#!/bin/bash

DIRH=`pwd`
CHAR=/usb/tilman/c/carat/Qclasses/QClasses

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
                  $CHAR $zz > char.$zz

               fi
            done

            cd ..
         done
      cd ..
   done

   cd $DIRH

done

rm -f $TMP $TMP2
