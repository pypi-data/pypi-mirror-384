#!/bin/bash

DIRH=`pwd`
ZW2=/usb/tilman/c/carat/Transform_to_good_base/scripts/zweite_zeile2
BASE=$DIRH/BASIS

PATH=$PATH:/usb/matrix/bin/momo/
TMP=/tmp/new.$RANDOM
TMP2=/tmp/new.$RANDOM.2

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

                     cat $zz > new.$zz
                  else
                     Orbit $BASE $zz > $TMP
                     $ZW2 $TMP $zz > $TMP2
                     gap4 -b < $TMP2
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
