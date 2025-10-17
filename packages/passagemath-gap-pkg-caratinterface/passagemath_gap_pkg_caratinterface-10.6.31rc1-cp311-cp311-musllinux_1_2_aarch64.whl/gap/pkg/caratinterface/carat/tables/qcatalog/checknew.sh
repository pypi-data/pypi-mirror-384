#!/bin/bash

DIRH=`pwd`
QC=/usb/klaus/hel-update/suche_kand

PATH=$PATH:/usb/matrix/bin/momo/
TMP=/tmp/check.$RANDOM

for x in dir.* ; do

   cd $x

   for y in ordnung.* ; do
      cd $y

         for z in * ; do
            cd $z

            for zz in group.* min.* max.* ; do
               if [ -s $zz ] ; then
                  $QC $zz new.$zz | grep "No matrix exists" > $TMP
                  if [ -s $TMP ] ; then
                     echo FEHLER bei $zz QEQUIV
                     exit
                  fi
                  if  Zass_main pres.$zz new.$zz ; then
                     echo $zz
                  else
                     echo FEHLER bei $zz COHO
                     exit
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
