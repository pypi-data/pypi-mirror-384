#!/bin/bash

DIRH=`pwd`



for x in dir.* ; do
   cd $x

   for y in ordnung.* ; do
      cd $y

         for z in * ; do
            cd $z

            for zz in group.* min.* max.* ; do
               if [ -s $zz ] ; then
                  rm g.$zz gg.$zz $zz.*
               fi
            done

            cd ..
         done
      cd ..
   done

   cd $DIRH

done

