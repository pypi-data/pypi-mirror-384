#############################################################################
##
#W  gapbibl.g             GAP 4 package `browse'                Thomas Breuer
##
##  <#GAPDoc Label="Bibliography_section">
##  <Section Label="sec:gapbibl">
##  <Heading>Overview of Bibliographies</Heading>
##
##  The function <Ref Func="BrowseBibliography"/> can be used to turn the
##  contents of bibliography files in BibTeX or BibXMLext format
##  (see <Ref Sect="The BibXMLext Format" BookName="gapdoc"/>)
##  into a Browse table,
##  such that one can scroll in the list, search for entries, sort by year,
##  sort and categorize by authors etc.
##  <P/>
##  The default bibliography used by <Ref Func="BrowseBibliography"/> is the
##  bibliography of &GAP; related publications,
##  see&nbsp;<Cite Key="GAPBibliography"/>.
##  The &Browse; package contains a (perhaps outdated) version of this
##  bibliography.
##  One can get an updated version as follows.
##  <P/>
##  <C>wget -N http://www.gap-system.org/Doc/Bib/gap-publishednicer.bib</C>
##  <P/>
##  The columns of the Browse table that is shown by
##  <Ref Func="BrowseBibliography"/> can be customized,
##  two examples for that are given by the functions
##  <Ref Func="BrowseBibliographySporadicSimple" BookName="atlasrep"/>
##  and <Ref Func="BrowseBibliographyGapPackages"/>.
##  <P/>
##  The function <Ref Func="BrowseMSC"/> shows an overview of the
##  AMS Mathematics Subject Classification codes.
##
##  <#Include Label="BrowseBibliography">
##  <#Include Label="BrowseBibliographyGapPackages">
##  <#Include Label="BrowseMSC">
##
##  </Section>
##  <#/GAPDoc>
##


if not IsBound( HeuristicTranslationsLaTeX2XML ) then
  HeuristicTranslationsLaTeX2XML:= 0;
fi;


#############################################################################
##
#F  BrowseData.LoadMSCData()
##
##  reads the files `bibl/mscdata2010.txt', `bibl/mscdata2020.txt',
##  `bibl/mscdiffs2000to2010.txt', and `bibl/mscdiffs2010to2020.txt' of the
##  package and sets the components of the records
##  `BrowseData.MSCData.mscdata2010',
##  `BrowseData.MSCData.mscdata2020',
##  `BrowseData.MSCData.mscdiffs2000to2010', and
##  `BrowseData.MSCData.mscdiffs2010to2020'.
##
##  The component names of these records are the valid MSC codes,
##  the values are their descriptions according to the `.txt' files.
##
##  If one of the source files is not available then `false' is returned,
##  otherwise `true'.
##
BrowseData.LoadMSCData:= function()
    local dir, name, file, len, data, pos1, pos2;

    if not IsBound( BrowseData.MSCData ) then
      BrowseData.MSCData:= rec();
    fi;
    dir:= DirectoriesPackageLibrary( "browse", "bibl" );
    for name in [ "mscdata2010", "mscdata2020", "mscdiffs2000to2010",
                  "mscdiffs2010to2020" ] do
      file:= Filename( dir, Concatenation( name, ".txt" ) );
      if file = fail then
        return false;
      fi;
      file:= StringFile( file );
      Add( file, '\n' );
      len:= Length( file );
      data:= rec();
      pos1:= 1;
      pos2:= Position( file, '\n' );
      while pos2 <> fail do
        if pos1 + 5 < len and file[ pos1 + 5 ] = ' '
                          and file[ pos1 ] <> '%' then
          data.( file{ [ pos1 .. pos1+4 ] } ):= file{ [ pos1+6 .. pos2-1 ] };
        fi;
        pos1:= pos2+1;
        pos2:= Position( file, '\n', pos2 );
      od;
      BrowseData.MSCData.( name ):= data;
    od;

    return true;
end;


#############################################################################
##
#F  BrowseData.CompareMSCcode( <mrcode1>, <mrcode2> )
##
##  The codes have length five,
##  the first two entries are digits,
##  the third entry is '-' (comes first) or an uppercase letter,
##  the last two entries are "XX" or "xx" (come first) or two digits.
##  So we can replace 'x' and 'X' by '*' (these two cannot compete) and then
##  compare with GAP's standard function '\<'.
##
BrowseData.CompareMSCcode:= function( mrcode1, mrcode2 )
    if mrcode1[4] in "xX" then
      mrcode1:= Concatenation( mrcode1{ [ 1 .. 3 ] }, "**" );
    fi;
    if mrcode2[4] in "xX" then
      mrcode2:= Concatenation( mrcode2{ [ 1 .. 3 ] }, "**" );
    fi;
    return mrcode1 < mrcode2;
end;


#############################################################################
##
#F  BrowseData.MSCDescription( <mrclass> )
##
BrowseData.MSCDescription:= function( mrclass )
    local data, descr, pos;

    # Secondary classifications are enclosed in brackets.
    mrclass:= ReplacedString( mrclass, "(", "" );
    mrclass:= ReplacedString( mrclass, ")", "" );

    # If the descriptions are not yet loaded then read the file.
    if not BrowseData.LoadMSCData() then
      return [ mrclass, "MSC descriptions not available" ];
    fi;
    data:= BrowseData.MSCData;
    if IsBound( data.mscdata2020.( mrclass ) ) then
      # known in MSC 2020
      return [ mrclass, data.mscdata2020.( mrclass ) ];
    elif IsBound( data.mscdata2010.( mrclass ) ) then
      # known in MSC 2010
      return [ Concatenation( mrclass, "*" ),
               data.mscdata2010.( mrclass ) ];
    elif IsBound( data.mscdiffs2000to2010.( mrclass ) ) then
      # known only in MSC 2000
      descr:= data.mscdiffs2000to2010.( mrclass );
      pos:= PositionNthOccurrence( descr, '|', 2 );
      return [ Concatenation( mrclass, "*" ),
               descr{ [ pos+2 .. Length( descr ) ] } ];
    else
      return [ mrclass, "unknown MSC code" ];
    fi;
end;


#############################################################################
##
#F  BrowseData.MSCString( <mrclasses> )
##
BrowseData.MSCString:= function( mrclasses )
    local mscinfo, class, val, info, render, result, i;

    if not BrowseData.LoadMSCData() then
      return "MSC descriptions not available";
    fi;

    mscinfo:= [];
    for class in SplitString( mrclasses, " " ) do
      class:= ReplacedString( class, "(", "" );
      class:= ReplacedString( class, ")", "" );
      if Length( class ) = 5 then
        # There is always the first level.
        val:= BrowseData.MSCDescription(
                  Concatenation( class{ [ 1, 2 ] }, "-XX" ) );
        info:= [ Concatenation( String( val[1], -11 ), val[2] ) ];
        if class[4] <> 'X' then
          # There is another level.
          if class[3] = '-' then
            # There is level 3 but not 2.
            info[2]:= "";
            val:= BrowseData.MSCDescription( class );
            info[3]:= Concatenation( "    ", String( val[1], -7 ), val[2] );
          elif class[4] = 'x' then
            # There is level 2 but not 3.
            val:= BrowseData.MSCDescription( class );
            info[2]:= Concatenation( "  ", String( val[1], -9 ), val[2] );
            info[3]:= "";
          else
            # There are levels 2 and 3.
            val:= BrowseData.MSCDescription(
                      Concatenation( class{ [ 1 .. 3 ] }, "xx" ) );
            info[2]:= Concatenation( "  ", String( val[1], -9 ), val[2] );
            val:= BrowseData.MSCDescription( class );
            info[3]:= Concatenation( "    ", String( val[1], -7 ), val[2] );
          fi;
        fi;
        Add( mscinfo, info );
      fi;
    od;

    Sort( mscinfo );
    render:= l -> JoinStringsWithSeparator( Filtered( l, x -> x <> "" ), "\n" );

    result:= render( mscinfo[1] );
    for i in [ 2 .. Length( mscinfo ) ] do
      Append( result, "\n" );
      if mscinfo[i][1] = mscinfo[i-1][1] then
        if mscinfo[i][2] = mscinfo[i-1][2] then
          Append( result, mscinfo[i][3] );
        else
          Append( result, render( mscinfo[i]{ [ 2, 3 ] } ) );
        fi;
      else
        Append( result, render( mscinfo[i] ) );
      fi;
    od;

    return result;
end;


#############################################################################
##
#F  BrowseMSC( [<version>] )
##
##  <#GAPDoc Label="BrowseMSC">
##  <ManSection>
##  <Func Name="BrowseMSC" Arg="[version]"/>
##
##  <Returns>
##  nothing.
##  </Returns>
##
##  <Description>
##  This function shows the valid MSC codes in a browse table that
##  is categorized by the <C>..-XX</C> and the <C>...xx</C> codes.
##  (Use <B>X</B> for expanding all categories or <B>x</B> for expanding the
##  currently selected category.)
##  Due to the categorization, only two columns of the table are visible,
##  showing the codes and their descriptions.
##  <P/>
##  If <A>version</A> is given then it must be one of the numbers <M>2010</M>
##  or <M>2020</M>, meaning that the MSC2010 or MSC2020 codes are shown;
##  the default for <A>version</A> is <M>2020</M>.
##  </Description>
##  </ManSection>
##  <#/GAPDoc>
##
BindGlobal( "BrowseMSC", function( version... )
    local descrrec, winwidth, mrwidth, descrwidth, matrix, listtosort, data,
          mrclass, middle, top, descr, shortdescr, pos, r;

    if not BrowseData.LoadMSCData() then
      return;
    fi;
    descrrec:= rec();
    winwidth:= NCurses.getmaxyx( 0 )[2];
    mrwidth:= 5;
    descrwidth:= winwidth - mrwidth - 7;

    matrix:= [];
    listtosort:= [];
    if Length( version ) = 1 and version[1] = 2010 then
      data:= BrowseData.MSCData.mscdata2010;
      version:= "2010";
    else
      data:= BrowseData.MSCData.mscdata2020;
      version:= "2020";
    fi;
    for mrclass in RecNames( data ) do
      if mrclass[3] = '-' then
        middle:= Concatenation( mrclass{ [ 1 .. 3 ] }, "XX" );
      else
        middle:= Concatenation( mrclass{ [ 1 .. 3 ] }, "xx" );
      fi;
      top:= Concatenation( mrclass{ [ 1, 2 ] }, "-XX" );
      descr:= BrowseData.SimplifiedString(
                         HeuristicTranslationsLaTeX2XML.Apply(
                             data.( mrclass ) ) );
      if mrclass[4] in "xX" then
        shortdescr:= descr;
        pos:= PositionSublist( shortdescr, " {" );
        if pos <> fail then
          shortdescr:= shortdescr{ [ 1 .. pos - 1 ] };
        fi;
        pos:= PositionSublist( shortdescr, " [" );
        if pos <> fail then
          shortdescr:= shortdescr{ [ 1 .. pos - 1 ] };
        fi;
        descrrec.( mrclass ):= shortdescr;
      fi;
      descr:= rec( rows:= SplitString( ReplacedString( FormatParagraph(
                       descr, descrwidth, "left" ), "\n", " \n" ), "\n" ),
                   align:= "tl" );
      Add( matrix, [ mrclass, middle, top, descr ] );
      Add( listtosort, mrclass );
    od;
    SortParallel( listtosort, matrix, BrowseData.CompareMSCcode );

    # Create the default table.
    r:= rec(
      work:= rec(
        align:= "tl",
        header:= t -> BrowseData.HeaderWithRowCounter( t,
                        Concatenation( "MSC ", version, " classification" ),
                        Length( matrix ) ),
        widthCol:= [ , mrwidth,, mrwidth,, mrwidth,, descrwidth ],
        sepRow:= "-",
        sepCol:= [ "| ", " | ", " | ", " | ", " |" ],
        SpecialGrid:= BrowseData.SpecialGridLineDraw,
        main:= matrix,
        CategoryValues:= function( t, i, j )
          if   j = 2 then
            return [ Concatenation( t.work.main[ i/2 ][ j/2 ], " ",
                       Concatenation( t.work.main[ i/2 ][3].rows ) ) ];
          elif j in [ 4, 6 ] then
            return [ Concatenation( t.work.main[ i/2 ][ j/2 ], " ",
                       descrrec.( t.work.main[ i/2 ][ j/2 ] ) ) ];
          else
            return [ Concatenation( t.work.main[ i/2 ][ j/2 ].rows ) ];
          fi;
        end,
      ),
      dynamic:= rec(
        initialSteps:= "scrscXscrsc",
      ),
    );

    NCurses.BrowseGeneric( r );
end );


#############################################################################
##
#F  BrowseBibliography( [<bibfiles>] )
##
##  <#GAPDoc Label="BrowseBibliography">
##  <ManSection>
##  <Func Name="BrowseBibliography" Arg="[bibfiles]"/>
##
##  <Returns>
##  a record as returned by
##  <Ref Func="ParseBibXMLExtFiles" BookName="gapdoc"/>.
##  </Returns>
##
##  <Description>
##  This function shows the list of bibliography entries in the files
##  given by <A>bibfiles</A>, which may be a string or a list of strings
##  (denoting a filename or a list of filenames, respectively)
##  or a record (see below for the supported components).
##  <P/>
##  If no argument is given then the file <F>bibl/gap-publishednicer.bib</F>
##  in the &Browse; package directory is taken,
##  and <C>"GAP Bibliography"</C> is used as the header.
##  <P/>
##  Another perhaps interesting data file that should be available in the
##  &GAP; distribution is <F>doc/manualbib.xml</F>.
##  This file can be located as follows.
##  <P/>
##  <Example><![CDATA[
##  gap> file:= Filename( DirectoriesLibrary( "doc" ), "manualbib.xml" );;
##  ]]></Example>
##  <P/>
##  Both &BibTeX; format and the &XML; based extended format provided by the
##  &GAPDoc; package are supported by <Ref Func="BrowseBibliography"/>, see
##  Chapter&nbsp;<Ref Chap="Utilities for Bibliographies" BookName="gapdoc"/>.
##  <P/>
##  In the case of &BibTeX; format input, first a conversion to the extended
##  format takes place, via <Ref Func="StringBibAsXMLext" BookName="gapdoc"/>
##  and <Ref Func="ParseBibXMLextString" BookName="gapdoc"/>.
##  Note that syntactically incorrect entries are rejected in this conversion
##  &ndash;this is signaled with <Ref Var="InfoBibTools" BookName="gapdoc"/>
##  warnings&ndash; and that only a subset of the possible &LaTeX; markup is
##  recognized &ndash;other markup appears in the browse table except that
##  the leading backslash is removed.
##  <P/>
##  In both cases of input, the problem arises
##  that in visual mode, currently we can show only ASCII characters
##  (and the symbols in <C>NCurses.lineDraw</C>, but these are handled
##  differently, see Section&nbsp;<Ref Subsect="ssec:ncursesLines"/>).
##  Therefore, we use the function
##  <Ref Func="SimplifiedUnicodeString" BookName="gapdoc"/>
##  for replacing other unicode characters by ASCII text.
##  <P/>
##  The return value is a record as returned by
##  <Ref Func="ParseBibXMLExtFiles" BookName="gapdoc"/>,
##  its <C>entries</C> component corresponds to the bibliography entries
##  that have been <Q>clicked</Q> in visual mode.
##  This record can be used as input for
##  <Ref Func="WriteBibFile" BookName="gapdoc"/> or
##  <Ref Func="WriteBibXMLextFile" BookName="gapdoc"/>,
##  in order to produce a bibliography file,
##  or it can be used as input for
##  <Ref Func="StringBibXMLEntry" BookName="gapdoc"/>,
##  in order to produce strings from the entries, in various formats.
##  <P/>
##  The full functionality of the function
##  <Ref Func="NCurses.BrowseGeneric"/> is available.
##  <P/>
##  <Example><![CDATA[
##  gap> # sort and categorize by year, scroll down, expand a category row
##  gap> BrowseData.SetReplay( "scrrscsedddddxdddddQ" );
##  gap> BrowseBibliography();;
##  gap> # sort & categorize by authors, expand all category rows, scroll down
##  gap> BrowseData.SetReplay( "scscXseddddddQ" );
##  gap> BrowseBibliography();;
##  gap> # sort and categorize by journal, search for a journal name, expand
##  gap> BrowseData.SetReplay( Concatenation( "scrrrsc/J. Algebra",
##  >        [ NCurses.keys.ENTER ], "nxdddQ" ) );
##  gap> BrowseBibliography();;
##  gap> BrowseData.SetReplay( false );
##  ]]></Example>
##  <P/>
##  <E>Implementation remarks</E>:
##  The browse table has a dynamic header (showing the number of entries,
##  which can vary when the table is restricted), no footer and row labels;
##  one row of column labels is given by the descriptions of the table
##  columns (authors, title, year, journal, MSC code).
##  <P/>
##  Row and column separators are drawn as grids
##  (cf.&nbsp;<Ref Func="NCurses.Grid"/>) composed from the special characters
##  described in Section&nbsp;<Ref Subsect="ssec:ncursesLines"/>,
##  using the component <C>work.SpecialGrid</C> of the browse table,
##  see <Ref Var="BrowseData"/>.
##  <P/>
##  For categorizing by authors (or by MSC codes), the sort parameter
##  <C>"split rows on categorizing"</C> is set to <C>"yes"</C>,
##  so the authors (codes) are distributed to different category rows,
##  hence each entry appears once for each of its authors (or its MSC codes)
##  in the categorized table.
##  When a data row or an entry in a data row is selected,
##  <Q>click</Q> adds the corresponding bibliographhy entry to the result.
##  <P/>
##  The width of the title column is preset; usually titles are too long for
##  one line, and the contents of this column is formatted as a paragraph,
##  using the function <Ref Func="FormatParagraph" BookName="gapdoc"/>.
##  For the authors and journal columns, maximal widths are prescribed,
##  and <Ref Func="FormatParagraph" BookName="gapdoc"/> is used for longer
##  entries.
##  <P/>
##  For four columns, the sort parameters are defined as follows:
##  The <E>authors</E> and <E>MSC code</E> columns do not become hidden
##  when the table is categorized according to this column,
##  sorting by the <E>year</E> yields a <E>de</E>scending order,
##  and the category rows arising from these columns and the <E>journal</E>
##  column show the numbers of the data rows that belong to them.
##  <P/>
##  Those standard modes in <Ref Var="BrowseData"/> where an entry or a row
##  of the table is selected have been extended by three new actions,
##  which open a pager showing the &BibTeX;, HTML, and Text format of the
##  selected entry, respectively.
##  The corresponding user inputs are the <B>vb</B>, <B>vh</B>,
##  and <B>vt</B>.
##  If the <E>MSC code</E> column is available then also the user input
##  <B>vm</B> is admissible; it opens a pager showing the descriptions of the
##  MSC codes attached to the selected entry.
##  <P/>
##  This function requires some of the utilities provided by the
##  &GAP; package <Package>GAPDoc</Package>
##  (see&nbsp;<Cite Key="GAPDoc"/>),
##  such as <Ref Func="FormatParagraph" BookName="gapdoc"/>,
##  <Ref Func="NormalizeNameAndKey" BookName="gapdoc"/>,
##  <Ref Func="NormalizedNameAndKey" BookName="gapdoc"/>,
##  <Ref Func="ParseBibFiles" BookName="gapdoc"/>,
##  <Ref Func="ParseBibXMLextFiles" BookName="gapdoc"/>,
##  <Ref Func="ParseBibXMLextString" BookName="gapdoc"/>,
##  <Ref Func="RecBibXMLEntry" BookName="gapdoc"/>, and
##  <Ref Func="StringBibAsXMLext" BookName="gapdoc"/>.
##  <P/>
##  The code can be found in the file <F>app/gapbibl.g</F> of the package.
##  <P/>
##  The browse table can be customized by entering a record as the argument
##  of <Ref Func="BrowseBibliography"/>,
##  with the following supported components.
##  <List>
##  <Mark><C>files</C></Mark>
##  <Item>
##    a nonempty list of filenames containing the data to be shown;
##    there is no default for this component.
##  </Item>
##  <Mark><C>filesshort</C></Mark>
##  <Item>
##    a list of the same length as the <C>files</C> component,
##    the entries are strings which are shown in the <C>"sourcefilename"</C>
##    column of the table (if this column is present);
##    the default is the list of filenames.
##  </Item>
##  <Mark><C>filecontents</C></Mark>
##  <Item>
##    a list of the same length as the <C>files</C> component,
##    the entries are strings which are shown as category values when the
##    table is categorized by the <C>"sourcefilename"</C> column;
##    the default is the list of filenames.
##  </Item>
##  <Mark><C>header</C></Mark>
##  <Item>
##    is the constant part of the header shown above the browse table,
##    the default is the first filename.
##  </Item>
##  <Mark><C>columns</C></Mark>
##  <Item>
##    is a list of records that are valid as the second argument of
##    <Ref Func="DatabaseAttributeAdd"/>,
##    where the first argument is a database id enumerator created from the
##    bibliography entries in the files in question.
##    Each entry (and also the corresponding identifier) of this database id
##    enumerator is a list of records obtained from
##    <Ref Func="ParseBibXMLextFiles" BookName="gapdoc"/> and
##    <Ref Func="RecBibXMLEntry" BookName="gapdoc"/>,
##    or from <Ref Func="ParseBibFiles" BookName="gapdoc"/>,
##    such that the list elements are regarded as equal, in the sense that
##    their fingerprints (see below) are equal.
##    The records in the <C>columns</C> list are available for constructing
##    the desired browse table, the actual appearance is controlled by the
##    <C>choice</C> component described below.
##    Columns showing authors, title, year, journal, MSC code, and filename
##    are predefined and need not be listed here.
##  </Item>
##  <Mark><C>choice</C></Mark>
##  <Item>
##    a list of strings denoting the <C>identifier</C> components of those
##    columns that shall actually be shown in the table, the default is
##    <C>[ "authors", "title", "year", "journal", "mrclass" ]</C>.
##  </Item>
##  <Mark><C>fingerprint</C></Mark>
##  <Item>
##    a list of strings denoting component names of the entries of the
##    database id enumerator that is constructed from the data (see above);
##    two data records are regarded as equal if the values of these
##    components are equal; the default is
##    <C>[ "mrnumber", "title", "authorAsList", "editorAsList", "author" ]</C>.
##  </Item>
##  <Mark><C>sortKeyFunction</C></Mark>
##  <Item>
##    either <K>fail</K> or a function that takes a record as returned by
##    <Ref Func="RecBibXMLEntry" BookName="gapdoc"/> and returns a list
##    that is used for comparing and thus sorting the records;
##    the default is <K>fail</K>, which means that the rows of the table
##    appear in the same ordering as in the source files.
##  </Item>
##  </List>
##  </Description>
##  </ManSection>
##  <#/GAPDoc>
##
BindGlobal( "BrowseBibliography", function( arg )
    local columns, choice, fingerprint, sortKeyFunction, files, filesshort,
          filecontents, header, extend_entries, infocache, entries, mapping,
          entities, file, parse, r, result, identifier, ids, idenum, entry,
          id, pos, authorswidth, l, titlewidth, journalwidth, mrclasswidth,
          modes, newactions, showaction, mode, sel_action, table, ret;

    # Get the arguments.
    columns:= [];
    choice:= [ "authors", "title", "year", "journal", "mrclass" ];
    fingerprint:= [ "mrnumber", "title", "authorAsList", "editorAsList",
                    "author", "year", "pages" ];
    sortKeyFunction:= fail;
    if   Length( arg ) = 0 then
      files:= [ Filename( DirectoriesPackageLibrary( "browse", "bibl" ),
                          "gap-publishednicer.bib" ) ];
      filesshort:= [ BrowseData.StrippedPath( files[1] ) ];
      filecontents:= [ "gap-publishednicer.bib" ];
      header:= "GAP Bibliography";
    elif Length( arg ) = 1 and IsString( arg[1] ) then
      files:= arg;
      filesshort:= [ BrowseData.StrippedPath( files[1] ) ];
      filecontents:= filesshort;
      header:= files[1];
    elif Length( arg ) = 1 and IsList( arg[1] )
                           and not IsEmpty( arg[1] )
                           and ForAll( arg[1], IsString ) then
      files:= arg[1];
      filesshort:= List( files, BrowseData.StrippedPath );
      filecontents:= filesshort;
      header:= files[1];
      if 1 < Length( files ) then
        header:= Concatenation( header, ", ..." );
      fi;
    elif Length( arg ) = 1 and IsRecord( arg[1] )
                           and IsBound( arg[1].files ) then
      files:= arg[1].files;
      if not IsList( files ) or IsEmpty( files )
                             or not ForAll( files, IsString ) then
        Error( "<files> must be a nonempty list of strings" );
      fi;
      if IsBound( arg[1].filesshort ) then
        filesshort:= arg[1].filesshort;
      else
        filesshort:= List( files, BrowseData.StrippedPath );
      fi;
      if IsBound( arg[1].filecontents ) then
        filecontents:= arg[1].filecontents;
      else
        filecontents:= filesshort;
      fi;
      if IsBound( arg[1].header ) and IsString( arg[1].header ) then
        header:= arg[1].header;
      elif Length( files ) = 1 then
        header:= files[1];
      else
        header:= Concatenation( files[1], ", ..." );
      fi;
      if IsBound( arg[1].columns ) then
        columns:= ShallowCopy( arg[1].columns );
      fi;
      if IsBound( arg[1].choice ) then
        choice:= ShallowCopy( arg[1].choice );
      fi;
      if IsBound( arg[1].fingerprint ) then
        fingerprint:= ShallowCopy( arg[1].fingerprint );
      fi;
      if IsBound( arg[1].sortKeyFunction ) then
        sortKeyFunction:= arg[1].sortKeyFunction;
      fi;
    else
      Error( "usage: BrowseBibliography( [<bibfiles>] )" );
    fi;

    extend_entries:= function( entry, strings, file )
      local r;

      r:= RecBibXMLEntry( entry, "Text", strings );
      r.sourcefilename:= file;
      Add( entries, [ r, entry ] );
    end;

    # Switch off GAPDoc info messages.
    infocache:= List( [ InfoGAPDoc, InfoBibTools ],
                      c -> rec( class:= c, oldlevel:= InfoLevel( c ) ) );
    Perform( infocache, function( r ) SetInfoLevel( r.class, 0 ); end );

    # Parse the data files.
    entries:= [];
    mapping:= [];
    entities:= [];
    for file in files do
      if 3 < Length( file )
         and file{ [ Length( file )-3 .. Length( file ) ] } = ".xml" then
        # Convert the XML structure to records,
        # memorize the source.
        parse:= ParseBibXMLextFiles( file );
        if parse <> fail then
          for entry in parse.entries do
            extend_entries( entry, parse.strings, file );
          od;
          Append( mapping, parse.strings );
          Append( entities, parse.entities );
        fi;
      else
        # First convert the BibTeX format into XMLext format,
        # apply some heuristics in order to improve this,
        # and then create the records.
        parse:= ParseBibFiles( file );
        if parse <> fail then
          for entry in parse[1] do
            for r in RecNames( entry ) do
              if IsString( entry.( r ) ) then
                entry.( r ):= HeuristicTranslationsLaTeX2XML.Apply(
                                  entry.( r ) );
              fi;
            od;
            entry:= StringBibAsXMLext( entry, parse[2], parse[3]);
            if entry <> fail then
              entry:= ParseBibXMLextString( entry ).entries[1];
              extend_entries( entry, parse[2], file );
            fi;
          od;
          Append( mapping, TransposedMat( parse{ [ 2, 3 ] } ) );
        fi;
      fi;
    od;

    # Reset the changed GAPDoc info levels.
    Perform( infocache,
             function( r ) SetInfoLevel( r.class, r.oldlevel ); end );

    result:= rec( entries:= [],
                  strings:= [],
                  entities:= [], );
    if IsEmpty( entries ) then
      return result;
    fi;

    # Sort the entries if required.
    # (If no file argument is given then sort the entries by authors;
    # this was the behaviour before the source file was sorted.)
    if sortKeyFunction <> fail then
      SortParallel( List( entries, e -> sortKeyFunction( e[1] ) ), entries );
    elif Length( arg ) = 0 then
      SortParallel( List( entries, e -> e[1].author ), entries );
    fi;

    # Construct a database id enumerator from the contents.
    # (Deal with duplicates by collecting entries with the same identifier.)
    identifier:= function( entry )
      local id, fld;

      id:= rec();
      for fld in fingerprint do
        if IsBound( entry.( fld ) ) then
          id.( fld ):= entry.( fld );
        fi;
      od;
      return id;
    end;

    ids:= [];
    idenum:= [];
    for entry in entries do
      id:= identifier( entry[1] );
      pos:= Position( ids, id );
      if pos = fail then
        Add( ids, id );
        Add( idenum, [ entry ] );
      else
        Add( idenum[ pos ], entry );
      fi;
    od;
    idenum:= DatabaseIdEnumerator( rec(
        identifiers:= idenum,
        entry:= function( dbidenum, id ) return id; end,
      ) );

    # Construct database attributes for the columns to be displayed.
    authorswidth:= 35;
    DatabaseAttributeAdd( idenum, rec(
      identifier:= "authors",
      type:= "values",
      create:= function( attr, id )
        local normalize, auth;

        normalize:= true;
        id:= id[1][1];
        if   IsBound( id.authorAsList ) then
          auth:= id.authorAsList;
        elif IsBound( id.editorAsList ) then
          auth:= id.editorAsList;
        elif IsBound( id.author ) then
          auth:= id.author;
        elif IsBound( id.organization ) then
          auth:= id.organization;
          normalize:= false;
        elif IsBound( id.editor ) then
          auth:= id.editor;
        elif IsBound( id.publisher ) then
          auth:= id.publisher;
          normalize:= false;
        else
          auth:= "(no author, organization, editor, publisher)";
          normalize:= false;
        fi;
        if normalize and IsString( auth ) then
          # The value comes from a `.bib' file;
          # the value obtained from an `.xml' file need not be changed.
          auth:= NormalizedNameAndKey( auth )[4];
        fi;
        if IsString( auth ) then
          auth:= [ BrowseData.SimplifiedString( auth ) ];
        else
          auth:= List( auth, y -> BrowseData.SimplifiedString(
                                      Concatenation( y[1], ", ", y[2] ) ) );
        fi;
        auth:= List( auth, NormalizedWhitespace );
        if authorswidth < MaximumList( List( auth, Length ) ) then
          auth:= Concatenation( List( auth, l -> SplitString( FormatParagraph(
            BrowseData.SimplifiedString( l ), authorswidth, "left" ),
            "\n" ) ) );
        fi;
        return auth;
      end,
      viewValue:= x -> rec( rows:= x, align:= "tl" ),
      align:= "l",
      widthCol:= authorswidth,
      sortParameters:= [ "hide on categorizing", "no",
                         "add counter on categorizing", "yes",
                         "split rows on categorizing", "yes" ],
    ) );

    titlewidth:= 40;
    DatabaseAttributeAdd( idenum, rec(
      identifier:= "title",
      type:= "values",
      create:= function( attr, id )
        if   IsBound( id[1][1].title ) then
          return id[1][1].title;
        elif IsBound( id[1][1].booktitle ) then
          return id[1][1].booktitle;
        else
          return "(no title or booktitle)";
        fi;
        end,
      viewValue:= x -> rec(
              rows:= SplitString( ReplacedString( FormatParagraph(
                       BrowseData.SimplifiedString( x ),
                                titlewidth, "left" ), "\n", " \n" ), "\n" ),
              align:= "tl" ),
      align:= "l",
      widthCol:= titlewidth,
    ) );

    DatabaseAttributeAdd( idenum, rec(
      identifier:= "year",
      type:= "values",
      create:= function( attr, id )
        if IsBound( id[1][1].year ) then
          return id[1][1].year;
        else
          return "(no year)";
        fi;
        end,
      viewValue:= x -> rec( rows:= [ x ], align:= "tr" ),
      align:= "r",
      sortParameters:= [ "direction", "descending",
                         "add counter on categorizing", "yes" ],
    ) );

    journalwidth:= 35;
    DatabaseAttributeAdd( idenum, rec(
      identifier:= "journal",
      type:= "values",
      create:= function( attr, id )
        local jour;

        if IsBound( id[1][1].journal ) then
          jour:= id[1][1].journal;
        elif IsBound( id[1][1].Type ) then
          if id[1][1].Type in [ "incollection", "inproceedings" ]
             and IsBound( id[1][1].booktitle ) then
            jour:= Concatenation( "in: ", id[1][1].booktitle );
          else
            jour:= Concatenation( "(", id[1][1].Type, ")" );
          fi;
        else
          jour:= "(no journal)";
        fi;
        jour:= [ NormalizedWhitespace( BrowseData.SimplifiedString( jour ) ) ];
        if journalwidth < Length( jour[1] ) then
          jour:= SplitString( ReplacedString( FormatParagraph( jour[1],
                                journalwidth, "left" ), "\n", " \n" ),
                   "\n" );
        fi;
        return jour;
        end,
      viewValue:= x -> rec( rows:= x, align:= "tl" ),
      align:= "l",
      widthCol:= journalwidth,
      sortParameters:= [ "add counter on categorizing", "yes" ],
    ) );

    mrclasswidth:= 7;
    DatabaseAttributeAdd( idenum, rec(
      identifier:= "mrclass",
      type:= "values",
      create:= function( attr, id )
        if   IsBound( id[1][1].mrclass ) then
          return id[1][1].mrclass;
        else
          return "";
        fi;
        end,
      viewValue:= x -> rec(
              rows:= SplitString( x, " " ),
              align:= "t" ),
      viewSort:= BrowseData.CompareMSCcode,
      categoryValue:= value -> List( SplitString( value, " " ),
          function( x )
            x:= BrowseData.MSCDescription( x );
            return Concatenation( x[1], ": ", BrowseData.SimplifiedString(
                       HeuristicTranslationsLaTeX2XML.Apply( x[2] ) ) );
          end ),
      align:= "c",
      sortParameters:= [ "hide on categorizing", "no",
                         "add counter on categorizing", "yes",
                         "split rows on categorizing", "yes" ],
      widthCol:= mrclasswidth,
    ) );

    DatabaseAttributeAdd( idenum, rec(
      identifier:= "sourcefilename",
      viewLabel:= "filename",
      type:= "values",
      create:= function( attr, id )
        local rows, r;

        rows:= [];
        for r in id do
          if IsBound( r[1].sourcefilename ) and
             not r[1].sourcefilename in rows then
            Add( rows, r[1].sourcefilename );
          fi;
        od;
        return rows;
        end,
      viewValue:= value -> rec( rows:= DuplicateFreeList( List( value,
          x -> BrowseData.ReplacedEntry( x, files, filesshort ) ) ),
                                align:= "tl" ),
      categoryValue:= value -> List( value,
          x -> BrowseData.ReplacedEntry( x, files, filecontents ) ),
      align:= "l",
      sortParameters:= [ "hide on categorizing", "no",
                         "add counter on categorizing", "yes",
                         "split rows on categorizing", "yes" ],
    ) );

    # Add user defined columns.
    for l in columns do
      DatabaseAttributeAdd( idenum, l );
    od;

    # Construct the extended modes if necessary.
    if not IsBound( BrowseData.defaults.work.customizedModes.gapbibl ) then
      # Create a shallow copy of each default mode for `Browse', and add
      # new actions to those modes where a row or an entry is selected:
      # - vb: Show BibTeX format of the selected entry in a pager
      # - vh: Show HTML format of the selected entry in a pager
      # - vt: Show text format of the selected entry in a pager
      modes:= List( BrowseData.defaults.work.availableModes,
                    BrowseData.ShallowCopyMode );
      BrowseData.defaults.work.customizedModes.gapbibl:= modes;
      newactions:= [ [ "vb", "BibTeX" ],
                     [ "vh", "HTML" ],
                     [ "vt", "Text" ] ];
      showaction:= pair -> [ [ pair[1] ],
        rec( helplines:= [ Concatenation( "show ", pair[2],
                             " format of the selected entry in a pager" ) ],
             action:= function( t )
               local pos, disp;

               if t.dynamic.selectedEntry <> [ 0, 0 ] then
                 pos:= t.dynamic.indexRow[ t.dynamic.selectedEntry[1] ] / 2;
                 disp:= StringBibXMLEntry( t.work.entries[ pos ][1][2],
                                           pair[2], t.work.mapping );
                 disp:= SimplifiedUnicodeString( Unicode( disp ), "ASCII" );
                 disp:= Encode( disp, GAPInfo.TermEncoding );
                 if IsBound( t.dynamic.statuspanel ) then
                   NCurses.hide_panel( t.dynamic.statuspanel );
                 fi;
                 NCurses.Pager( disp );
                 if IsBound( t.dynamic.statuspanel ) then
                   NCurses.show_panel( t.dynamic.statuspanel );
                 fi;
               fi;
               t.dynamic.changed:= true;
             end ) ];
      newactions:= List( newactions, showaction );

      if "mrclass" in choice then
        Add( newactions, [ [ "vm" ], 
          rec( helplines:= [ "show MSC info of the selected entry in a pager" ],
               action:= function( t )
                 local pos, r, disp;
  
                 if t.dynamic.selectedEntry <> [ 0, 0 ] then
                   pos:= t.dynamic.indexRow[ t.dynamic.selectedEntry[1] ] / 2;
                   r:= t.work.entries[ pos ][1][1];
                   if IsBound( r.mrclass ) then
                     disp:= BrowseData.MSCString( r.mrclass );
                   else
                     disp:= "no MSC codes";
                   fi;
                   disp:= SimplifiedUnicodeString( Unicode( disp ), "ASCII" );
                   disp:= Encode( disp, GAPInfo.TermEncoding );
                   if IsBound( t.dynamic.statuspanel ) then
                     NCurses.hide_panel( t.dynamic.statuspanel );
                   fi;
                   NCurses.Pager( disp );
                   if IsBound( t.dynamic.statuspanel ) then
                     NCurses.show_panel( t.dynamic.statuspanel );
                   fi;
                 fi;
                 t.dynamic.changed:= true;
               end ) ] );
      fi;

      for mode in modes do
        if mode.name in [ "select_row", "select_entry",
                          "select_row_and_entry",
                          "select_column_and_entry" ] then
          BrowseData.SetActions( mode, newactions );
        fi;
      od;
    else
      modes:= BrowseData.defaults.work.customizedModes.gapbibl;
    fi;

    sel_action:= rec(
      helplines:= [ "add the BibTeX or XML entry to the result list" ],
      action:= function( t )
      if t.dynamic.selectedEntry <> [ 0, 0 ] then
        Add( t.dynamic.Return,
             t.dynamic.indexRow[ t.dynamic.selectedEntry[1] ] / 2 );
      fi;
    end );

    # Construct the browse table.
    table:= BrowseTableFromDatabaseIdEnumerator( idenum, [], choice,
                t -> BrowseData.HeaderWithRowCounter( t, header,
                          Length( idenum.identifiers ) ) );
    table.work.cacheEntries:= true;
    table.work.Click:= rec(
          select_entry:= sel_action,
          select_row:= sel_action,
        );
    table.work.availableModes:= modes;
    table.dynamic.Return:= [];
    table.dynamic.activeModes:= [ First( modes, x -> x.name = "browse" ) ];

    table.work.entries:= idenum.identifiers;
    table.work.mapping:= mapping;

    # Show the table.
    ret:= DuplicateFreeList( NCurses.BrowseGeneric( table ) );

    # Construct the return value.
    if not IsEmpty( ret ) then
      result.strings:= mapping;
      result.entities:= entities;
      result.entries:= List( idenum.identifiers{ ret }, x -> x[1][2] );
    fi;

    return result;
end );


if HeuristicTranslationsLaTeX2XML = 0 then
  Unbind( HeuristicTranslationsLaTeX2XML );
fi;


#############################################################################
##
#F  BrowseBibliographyGapPackages()
##
##  <#GAPDoc Label="BrowseBibliographyGapPackages">
##  <ManSection>
##  <Func Name="BrowseBibliographyGapPackages" Arg=""/>
##
##  <Returns>
##  a record as returned by <Ref Func="BrowseBibliography"/>.
##  </Returns>
##
##  <Description>
##  This function collects the information from the <C>*.bib</C> and
##  <C>*bib.xml</C> files in those subdirectories of installed &GAP; packages
##  which contain the package documentation,
##  and shows it in a Browse table, using the function
##  <Ref Func="BrowseBibliography"/>.
##  <P/>
##  <E>This function is experimental.</E>
##  The result is not really satisfactory, for the following reasons.
##  <P/>
##  <List>
##  <Item>
##    Duplicate entries may occur,
##    due to subtle differences in various source files.
##  </Item>
##  <Item>
##    The source files may contain more than what is actually cited
##    in the package manuals.
##  </Item>
##  <Item>
##    It may happen that some <C>*.bib</C> or <C>*bib.xml</C> file is
##    accidentally distributed with the package but is not intended to serve
##    as package bibliography.
##  </Item>
##  <Item>
##    The heuristics for rewriting &LaTeX; code is of course not perfect;
##    thus strange symbols may occur in the Browse table.
##  </Item>
##  </List>
##  </Description>
##  </ManSection>
##  <#/GAPDoc>
##
BindGlobal( "BrowseBibliographyGapPackages", function()
    local info, name, r1, path, r2, subdir, pos, len, dir, file;

    # Collect the '*.bib' and '*bib.xml' files from directories
    # of installed packages.
    info:= [];
    for name in RecNames( GAPInfo.PackagesInfo ) do
      # Run over the available versions of this package.
      for r1 in GAPInfo.PackagesInfo.( name ) do
        path:= r1.InstallationPath;
        # Run over the documentation books.
        for r2 in r1.PackageDoc do
          subdir:= r2.PDFFile;
          pos:= Positions( subdir, '/' );
          len:= Length( pos );
          if len <> 0 then
            subdir:= subdir{ [ 1 .. pos[ len ] - 1 ] };
            dir:= Concatenation( path, "/", subdir );
            if IsDirectoryPath( dir ) then
              dir:= Directory( dir );
              # Run over the files in the directory for this book.
              for file in Set( DirectoryContents( dir ) ) do
                len:= Length( file );
                if 7 < len and file{ [ len-6 .. len ] } = "bib.xml" then
                  Add( info, [ name, Filename( dir, file ) ] );
                elif 4 < len and file{ [ len-3 .. len ] } = ".bib" then
                  # Omit files of the form '<name>.xml.bib',
                  # they are assumed to be generated from '<name>.xml'.
                  if not ( 8 < len and file{ [ len-7 .. len ] }
                                       = ".xml.bib" ) then
                    Add( info, [ name, Filename( dir, file ) ] );
                  fi;
                fi;
              od;
            fi;
          fi;
        od;
      od;
    od;

    return BrowseBibliography( rec(
      filesshort:= List( info, x -> Concatenation( x[1], ": ",
                     Reversed( SplitString( x[2], "/" ) )[1] ) ),
      filecontents:= List( info, x -> Concatenation( "Package ", x[1] ) ),
      files:= List( info, x -> x[2] ),

      header:= "Bibliography of Gap Packages",
      choice:= [ "authors", "title", "year", "journal", "sourcefilename" ],
      sortKeyFunction:= BrowseData.SortKeyFunctionBibRec,
    ) );
end );


#############################################################################
##
##  Add the Browse applications to the list shown by `BrowseGapData'.
##
BrowseGapDataAdd( "AMS Math. Subject Classif.", BrowseMSC, "\
an overview of the AMS Mathematics Subject Classification codes (MSC 2020)" );

BrowseGapDataAdd( "GAP Bibliography", BrowseBibliography, "\
an overview of GAP related publications, in a browse table \
whose columns show authors, title, year, journal, and MSC code; \
the return value is a record encoding the clicked bibliography entries" );

BrowseGapDataAdd( "GAP Packages Bibliographies",
    BrowseBibliographyGapPackages, "\
the contents of the *bib and *bib.xml files of installed GAP packages, \
shown in a browse table with columns for authors, title, year, journal, \
and filename; \
the return value is a record encoding the clicked bibliography entries" );


#############################################################################
##
#E

