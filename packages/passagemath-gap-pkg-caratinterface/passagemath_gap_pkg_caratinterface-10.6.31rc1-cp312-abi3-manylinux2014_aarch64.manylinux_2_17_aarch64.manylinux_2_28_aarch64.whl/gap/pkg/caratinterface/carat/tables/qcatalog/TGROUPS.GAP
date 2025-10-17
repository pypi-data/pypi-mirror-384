# bis auf die letzte Funktion ist alles von Tilman uebernommen
# (dabei habe ich seine letzte Funktion abgeaendert):
# =============================================================
minimalgeneratingset := function(G)

local POT,
      flag,
      CON,
      i,
      ERG,
      K;


    if (IsSolvable(G)) then
       return MinimalGeneratingSet(G);
    fi;

    flag := true;
    CON := Set(List(ConjugacyClasses(G),x->Representative(x)));
    i := 1;

    while (flag) do

       i:=i+1;

       POT := Combinations(CON,i);

       for K in POT do
          if (Index (G,Subgroup(G,K)) = 1) then
             return K;
             ERG := K;
             flag := false;
          fi;
       od;

    od;

return ERG;

end;;

print_list:=function(file,l,n)
# druckt eine liste, wobei die klammern weggelassen werden, und die
# kommatas durch " " ersetzt werden, und genau n teile der liste
local i,
      s,
      x;

for i in [1..n] do
  if (i < Length(l) ) then
     AppendTo(file,l[i]," ");
  else
     Print("0 ");
  fi;
  if ((i mod 30)=0) then
    AppendTo(file,"\n");
  fi;
od;
AppendTo(file,"\n");
return;
end;;

Print_mat := function(file,mat)


local l,
      N;

N := Length(mat);

AppendTo(file,N,"\n");

for l in mat do
    print_list(file,l,Length(l));
od;

return;

end;;

print_matrix_group := function(file,G)

local GEN,
      x,
      i,
      j,
      k,
      N;

GEN := GeneratorsOfGroup(G);

AppendTo(file,"#g",Length(GEN),"\n");

for k in [1..Length(GEN)] do
   x := GEN[k];
   N := Length(x);
   AppendTo(file,N,"\n");
   for i in [1..N] do
      for j in [1..N] do
         AppendTo(file,x[i][j]," ");
      od;
      AppendTo(file,"\n");
   od;
   AppendTo(file,"\n");
   AppendTo(file,"\n");
od;


end;;




word_to_myword:=function(w,E)
# w ist ein gapword
# E ist eine liste von erzeugern
# ausgegeben wird ein word in matrixschreibweise
local j,i,k,
      ww,
      list;

ww := ExtRepOfObj(w);

list:=[];

for i in [1..Length(ww)/2] do
   k := ww[2*i];
   if (k < 0) then
      for j in [1..-k] do
         list := Concatenation(list,[-ww[2*i-1]]);
      od;
   else
      for j in [1..k] do
         list := Concatenation(list,[ww[2*i-1]]);
      od;
   fi;
od;

return list;
end;;



print_relators:=function(file,relators,generators)

local m,
      n,
      lists,   #
      len,     # List of Lengths of the relators
      i;

lists:=List([1..Length(relators)],x->word_to_myword(relators[x],generators));
len:=List([1..Length(relators)],x->Length(lists[x]));

m:=Maximum(len);

AppendTo(file,Length(relators),"x",m,"\n");

for i in [1..Length(relators)] do
  print_list(file,lists[i],m);
od;

end;;

print_fpgroup:=function(file,group)

AppendTo(file,"\n");
if (IsFpGroup(group)) then
  print_relators(file,RelatorsOfFpGroup(group),GeneratorsOfGroup(group));
fi;

return true;

end;;

print_words := function(file,W,generators,zahl)

local A,
      i,
      j,
      x,
      max;

max := 1;

for x in W do
   if (Length(x)>max) then
      max := Length(x);
   fi;
od;

A:=List(W,x->word_to_myword(x,generators));

AppendTo(file,Length(W) + zahl,"x",max+1,"\n");

for i in [1..Length(W)] do
   AppendTo(file,Length(W[i])," ");
   for j in [1..max] do
      if (j <= Length(A[i])) then
         AppendTo(file,A[i][j]," ");
      else
         AppendTo(file,"0 ");
      fi;
   od;
   AppendTo(file,"\n");
od;

return max;

end;;


# ======================================================================================
# Berechne die Konjugiertenklassen der maximalen Untergruppen der endliche Gruppe G
# und gib fuer einen Vertreter jeder Konjugiertenklasse Worte fuer die Erzeuger in den
# Erzeugern von G an. Die Worte werden in Matrizen in file geschrieben bzw. an file
# angehaengt, falls file schon existiert.
# Die letzte Zeile in den Matrizen gibt jeweils die Anzahl der Elemente in der
# Konjugiertenklasse an sowie die Ordnung der Gruppen in der Konjugiertenklasse!
# ======================================================================================
SubgroupWords := function(G, file)
   local i, j, subs, gen, group, worte, w, max;

   subs := ConjugacyClassesMaximalSubgroups(G);
   group := Group(GeneratorsOfGroup(G));
   AppendTo(file, "#", Size(subs),"\n");
   for i in [1..Size(subs)] do
      worte := [];
      for j in [1..Size(GeneratorsOfGroup(Representative(subs[i])))] do
         w:=Factorization(group, GeneratorsOfGroup(Representative(subs[i]))[j]);
         Append(worte, [w]);
      od;
      max := print_words(file, worte, GeneratorsOfGroup(G),1);
      AppendTo(file, Size(subs[i]));
      AppendTo(file, " ", Order(Representative(subs[i])));
      for j in [1..max - 1] do
         AppendTo(file, " 0");
      od;
      AppendTo(file, "\n");
      Print(worte,"\n");
   od;
end;














