#!/bin/bash

rm -f $2
QCLASSMAT=/usb2/tilman/c/carat/Qclasses/QClasses

(while read name degree symbol order discr zanz qanz tor matnumber ; do

   filename=dim$degree/dir.$symbol/ordnung.$order/$discr/$name

   echo $filename

   if [ -s $filename ] ; then
      $QCLASSMAT $filename > tmp3
      connumber=`LTM -c 1 tmp3 | grep x | sort -u | cut -f1-1 | sed "s/x1//g"`
      idemnumber=`LTM -r 1 tmp3 | head -n 1 | sed "s/#//"`
      idemnumber=$[ $idemnumber - 9 ]
      echo $read $name $degree $symbol $order $discr $zanz $qanz $tor  \
              $connumber $idemnumber >> $2
   else
      echo fehler
      exit 7
   fi

done ; ) < $1

rm -r tmp tmp2 tmp3
