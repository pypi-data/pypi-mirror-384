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
                  echo $zz
                  if ! Graph $zz > gg.$zz ; then
                     echo $x/$y/$z/$zz >> $DIRH/GRAPHFEHLER
                  fi
                  diff g.$zz gg.$zz
                  rm gg.$zz
                  echo
                  echo
               fi
            done

            cd ..
         done
      cd ..
   done

   cd $DIRH

done

