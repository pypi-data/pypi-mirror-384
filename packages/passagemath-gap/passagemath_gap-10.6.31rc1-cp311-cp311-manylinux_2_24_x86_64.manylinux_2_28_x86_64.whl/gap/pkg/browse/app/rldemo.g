#############################################################################
##
#W  rldemo.g           GAP 4 package 'Browse'       Frank Lübeck/Thomas Breuer
##
##  This files contains an application that can save a lot of typing
##  during demos of GAP code.
##  

##  <#GAPDoc Label="rldemo_section">
##  <Section Label="sec:rldemo">
##  <Heading>Utility for &GAP; Demos</Heading>
##  
##  This  application can  be  used with  &GAP; if  the  user interface  has
##  <C>readline</C> support. The purpose is  to simplify the typing during a
##  demonstration of &GAP; commands.
##  <P/>
##  The  file format  to  specify &GAP;  code for  a  demonstration is  very
##  simple: it contains blocks of lines with &GAP; input, separated by lines
##  starting with the sequence  <C>#%</C>. Comments in such a file can be added
##  to one or  several lines starting with <C>#%</C>. Here  is the content of
##  an example file <F>demo.demo</F>:
##  <P/>
##  <Verb>
##  #% Add comments after #% characters at the beginning of a line.
##  #% A comment can have several lines.
##  #% Here is a multi-line input block:
##  g := MathieuGroup(11);;
##  cl := ConjugacyClasses(g);
##  #% Calling a help page
##  ?MathieuGroup
##  #% The next line contains a comment in the GAP session:
##  a := 12;; b := 13;; # assign two numbers
##  #%
##  a*b;
##  #%
##  </Verb>
##  (Single <C>%</C> in the beginning of a line will also work as
##  separators.)<P/>
##  A demonstration can be loaded into a &GAP; session with the command
##  <ManSection>
##  <Func Name="LoadDemoFile" Arg="demoname, demofile[, singleline]" />
##  <Returns>Nothing.</Returns>
##  <Description>
##  This  function loads  a demo  file in  the format  described above.  The
##  argument <A>demoname</A> is a string containing a name for the demo, and
##  <A>demofile</A> is the file name containing the demo.
##  <P/>
##  If the  optional argument  <A>singleline</A> is given  and its  value is
##  <K>true</K>, the demo  behaves differently with respect  to input blocks
##  that span several lines. By default  full blocks are treated as a single
##  input line for <C>readline</C> (maybe spanning several physical lines in
##  the terminal). If <A>singleline</A> is  <K>true</K> then all input lines
##  of a  block except  the last  one are  sent to  &GAP; and  are evaluated
##  automatically before the last line of the block is displayed.
##  <Example>
##  gap> dirs := DirectoriesPackageLibrary("Browse");;
##  gap> demofile := Filename(dirs, "../app/demo.demo");;
##  gap> if IsBound(GAPInfo.UseReadline) and GAPInfo.UseReadline = true then
##  >   LoadDemoFile("My first demo", demofile);
##  >   LoadDemoFile("My first demo (single lines)", demofile, true);
##  > fi;
##  </Example>
##  </Description>
##  </ManSection>
##  
##  Many  demos can  be loaded  at the  same time.  They are  used with  the
##  <B>PageDown</B> and <B>PageUp</B> keys.
##  <P/>
##  The  <B>PageUp</B> key  leads to  a (Browse)  menu which  allows one  to
##  choose a  demo to start (if  several are loaded),  to stop a demo  or to
##  move to  another position  in the current  demo (e.g., to  go back  to a
##  previous point or to skip part of a demo).
##  <P/>
##  The next  input block  of the  current demo is  copied into  the current
##  input line  of the  &GAP; session by  pressing the  <B>PageDown</B> key.
##  This line  is not yet  sent to &GAP;, use  the <B>Return</B> key  if you
##  want to  evaluate the  input. (You  can also still  edit the  input line
##  before evaluation.)
##  <P/>
##  So,  in  the  simplest  case  a  demo  can  be  done  by  just  pressing
##  <B>PageDown</B> and <B>Return</B> in turns. But it is always possible to
##  type extra input during a demo by hand or to change the input lines from
##  the  demo file  before  evaluation. It  is no  problem  if commands  are
##  interrupted by  <B>Ctrl-C</B>. During a demo  you are in a  normal &GAP;
##  session, this  application only saves  you some typing. The  input lines
##  from the demo  are put into the  history of the session as  if they were
##  typed by hand.
##  <P/>
##  Try it  yourself with  the two  demos loaded in  the example.  This also
##  shows the different behaviour between default and single line mode.
##  
##  </Section>
##  <#/GAPDoc>

# a data structure to store demos and for the current state
BrowseData.Demos := rec(demos := [], curr := 0, pos := [0,0], cont := false);

# loading demonstrations
BindGlobal("LoadDemoFile", function(title, fname, single...)
  local str, lines, blocks, bl, l;
  if Length(single) > 0 and single[1] = true then
    single := true;
  else
    single := false;
  fi;
  str:= StringFile( fname );
  if str = fail then
    Error( "the file '", fname, "' is not readable" );
  fi;
  lines := SplitString(str,"\n","");
  blocks := [];
  bl := [];
  for l in lines do
    if (Length(l) > 1 and l[1]='#' and l[2]='%') 
        or (Length(l) > 0 and l[1] = '%') then
      if Length(bl) > 0 then
        if single then
          Add(blocks, bl);
        else
          Add(blocks, [JoinStringsWithSeparator(bl, "\n")]);
        fi;
        bl := [];
      fi;
    else
      Add(bl, l);
    fi;
  od;
  if Length(bl) > 0 then
    if single then
      Add(blocks, bl);
    else
      Add(blocks, [JoinStringsWithSeparator(bl, "\n")]);
    fi;
  fi;
  Add(BrowseData.Demos.demos, [title, blocks]);
end);
# internal function to choose the current demo interactively
BindGlobal("ChooseDemo", function()
  BrowseData.Demos.curr := NCurses.Select(rec(border := true, 
      header := "Choose one of the loaded demos:", 
      items := List(BrowseData.Demos.demos, d-> d[1]), none := true));
  if BrowseData.Demos.curr = false then
    BrowseData.Demos.curr := 0;
  fi;
  BrowseData.Demos.pos := [1,1];
end);
# internal function to change the current position in the current demo
# interactively
BindGlobal("RewindDemoPosition", function()
  local items, poss, bls, hint, i, j;
  if BrowseData.Demos.curr = 0 then
    Print("No demo chosen.\n");
    return;
  fi;
  items := [];
  poss := [];
  bls := BrowseData.Demos.demos[BrowseData.Demos.curr][2];
  for i in [1..Length(bls)] do
    Add(items, [NCurses.ColorAttr("red", -1), bls[i][1]]);
    Add(poss, [i,1]);
    for j in [2..Length(bls[i])] do
      Add(items, bls[i][j]);
      Add(poss, [i,j]);
    od;
  od;
  hint := NCurses.Select(rec(items := items, border := true,
           header := "Choose new position of next command",
           select := [Position(poss, BrowseData.Demos.pos)]));
  BrowseData.Demos.pos := [poss[hint][1], 1];
end);

# the menu for demos
BindGlobal("SettingsDemo", function(l)
  local job;
  if Length(BrowseData.Demos.demos) = 0 then
    return "";
  fi;
  job := NCurses.Alert( [
     [NCurses.attrs.BOLD, "Press letter to choose:"],
     "",
     " r   Rewind current demo",
     " s   Stop demo",
     " c   Choose different demo",
     ], 0);
  if job in [INT_CHAR('r'), INT_CHAR('R')] then
    RewindDemoPosition();
  elif job in [INT_CHAR('s'), INT_CHAR('S')] then
    BrowseData.Demos.curr := 0;
  elif job in [INT_CHAR('c'), INT_CHAR('C')] then
    ChooseDemo();
  fi;
  return [2, "\015"];
end);

# the function that will be bound to the PageDown key
##  InstallReadlineMacro("NextDemoBlock",  function(l)
BindGlobal("NextDemoBlock", function(l)
  local blocks, pos, line;
  if BrowseData.Demos.curr = 0 then
    # first choose a demo
    if Length(BrowseData.Demos.demos) = 0 then
      return "";
    elif Length(BrowseData.Demos.demos) = 1 then
      BrowseData.Demos.curr := 1;
      BrowseData.Demos.pos := [1,1];
    else
      ChooseDemo();
    fi;
    return [2, "\015"];
  fi;
  blocks := BrowseData.Demos.demos[BrowseData.Demos.curr][2];
  pos := BrowseData.Demos.pos;
  if pos[1] > Length(blocks) then
     NCurses.Alert( [NCurses.attrs.BOLD, "Demo finished"], 1000,
                     NCurses.ColorAttr( "red", -1 ) + NCurses.attrs.BOLD );
     # reset to start new demo
     BrowseData.Demos.curr := 0;
     return [2, "\015"];
  fi;
  line := blocks[pos[1]][pos[2]];
  if pos[2] < Length(blocks[pos[1]]) and not BrowseData.Demos.cont then
    # this is <Return><PageDown>
    BrowseData.Demos.cont := true;
    return [2, "\034\015\034"];
  fi;
  BrowseData.Demos.cont := false;
  if pos[2] = Length(blocks[pos[1]]) then
    pos[1] := pos[1]+1;
    pos[2] := 1;
  else
    pos[2] := pos[2]+1;
  fi;
  return [1, Length(l[3]), line, Length(line)+1];
end);

# this does not work nicely because of the next char hacking of
# NextDemoBlock:
##  InstallReadlineMacro("nextdemoblock", NextDemoBlock);
##  # bind to PageDown
##  ReadlineInitLine(Concatenation("\"\033[6~\":\"", 
##          InvocationReadlineMacro("nextdemoblock"), "\""));

GAPInfo.CommandLineEditFunctions.Functions.(INT_CHAR('\\') mod 32) :=
  NextDemoBlock;
BindKeysToGAPHandler("\034");
# PageDown
ReadlineInitLine("\"\033[6~\":\"\034\"");

# PageUp key leads to the menu
InstallReadlineMacro("settingsdemo", SettingsDemo);
ReadlineInitLine(Concatenation("\"\033[5~\":\"", 
           InvocationReadlineMacro("settingsdemo"), "\""));

