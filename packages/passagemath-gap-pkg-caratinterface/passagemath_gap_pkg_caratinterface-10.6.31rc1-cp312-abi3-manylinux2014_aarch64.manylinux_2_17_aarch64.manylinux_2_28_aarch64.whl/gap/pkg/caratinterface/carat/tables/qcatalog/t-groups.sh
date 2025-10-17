#!/bin/bash

DIRH=`pwd`


# Bereite File vor, in dem Befehle fuer GAP stehen
# Log-File: t-groups.log
echo LogTo\(\"t-groups.log\"\)\; > t-groups.out
echo RequirePackage\(\"carat\"\)\; >> t-groups.out
echo names := \[\]\; >> t-groups.out
echo GROUPS := \[\]\; >> t-groups.out
i=0;

# Wir wollen die Worte fuer alle Q-Klassen
for x in dir.* ; do
   cd $x

   for y in ordnung.* ; do
      cd $y

         for z in * ; do
            cd $z

            for zz in group.* min.* max.* ; do
               if [ -s $zz ] ; then
                  i=$[$i+1]
                  echo R := CaratReadBravaisFile\(\"$x/$y/$z/$zz\"\)\; >> $DIRH/t-groups.out
		  echo P$i := Group\(R.generators\)\; >> $DIRH/t-groups.out
		  echo Append\(names,\[\"$x/$y/$z/words.$zz\"\]\)\; >> $DIRH/t-groups.out
		  echo Append\(GROUPS,\[P$i\]\)\; >> $DIRH/t-groups.out
		  if [ -s words.$zz ] ; then
		     rm words.$zz
		  fi
               fi
            done

            cd ..
         done
      cd ..
   done

   cd $DIRH

done

# Nun sagen wir GAP noch, was es tun soll
echo "Print(GROUPS,\"\\n\");" >> t-groups.out
echo "Print(names,\"\\n\");" >> t-groups.out
echo "Size(GROUPS);" >> t-groups.out
echo "Size(names);" >> t-groups.out
echo Read\(\"..\/TGROUPS.GAP\"\)\; >> t-groups.out
echo "for i in [1..Size(GROUPS)] do" >> t-groups.out
echo "   SubgroupWords(GROUPS[i], names[i]);" >> t-groups.out
echo "od;" >> t-groups.out
echo "LogTo();" >> t-groups.out


# wir starten GAP und lassen es die Files mit den Worten
# fuer die Untergruppen anlegen
gap -o 1024m < t-groups.out


# Wir berechnen alle Raumgruppen und deren maximale translationengleiche
# Untergruppen bis auf Konjugation unter dem affinen Normalisator
# Dabei merken wir uns CARAT-Namen und Nummer eines Vertreters jeder Bahn
for x in dir.* ; do
   cd $x

   for y in ordnung.* ; do
      cd $y

         for z in * ; do
            cd $z

            for zz in group.* min.* max.* ; do
               if [ -s $zz ] ; then

                  QtoZ $zz -D ;
                  for a in $zz.* ; do
                     Extensions -S $a
                     for b in $a.* ; do
		        echo $b
                        if ! TSubgroups -g -p -c $b $a words.$zz >> words.$zz ; then
			   echo $x/$y/$z/$b >> $DIRH/FEHLER
			fi
                        rm ${b} ;
			echo 
			echo
			echo
                     done
                     rm $a ;
                  done

               fi
            done

            cd ..
         done
      cd ..
   done

   cd $DIRH

done
