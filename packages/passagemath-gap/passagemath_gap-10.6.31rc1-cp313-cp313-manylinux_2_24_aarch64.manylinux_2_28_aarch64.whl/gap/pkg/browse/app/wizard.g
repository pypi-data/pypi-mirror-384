#############################################################################
##
#W  wizard.g              GAP 4 package `Browse'                Thomas Breuer
##


#############################################################################
##
#F  BrowseData.IsQuestionnaire( <list> )
##
##  This function is called by 'BrowseWizard',
##  in order to check its argument.
##
BrowseData.IsQuestionnaire:= function( list )
    if not IsList( list ) or IsEmpty( list ) then
      Print( "#E  <list> must be a nonempty list\n" );
      return false;
    elif not ForAll( list, IsRecord ) then
      Print( "#E  all entries of <list> must be records\n" );
      return false;
    elif not ForAll( list, r -> IsBound( r.key ) and IsString( r.key ) ) then
      Print( "#E  all records in <list> must have a component 'key'",
             " (a string)\n" );
      return false;
    elif not ForAll( list, r -> IsBound( r.description ) and
                 ( IsString( r.description ) or
                   ( IsList( r.description ) and r.type = "ok" and
                     ForAll( r.description, IsString ) ) ) ) then
      Print( "#E  all records in <list> must have a component 'description'",
             " (a string\n",
             "#E  or in the case of type \"ok\" a list of strings)" );
      return false;
    elif not ForAll( list, r -> IsBound( r.type ) and
                 r.type in [ "editstring", "edittable", "key", "keys", "ok",
                             "okcancel", "submitcancelcontinue" ] ) then
      Print( "#E  all records in <list> must have a component 'type'\n",
             "#E  (one of \"editstring\", \"edittable\", \"key\", ",
             "\"keys\", \"ok\", \"okcancel\", \"submitcancelcontinue\")\n" );
      return false;
    elif ForAny( list, r -> r.type in [ "key", "keys" ] and
             not ( IsBound( r.keys ) and ( IsFunction( r.keys ) or
                   ( IsList( r.keys ) and
                     ForAll( r.keys, x -> Length( x ) = 2 and
                         IsString( x[1] ) ) ) ) ) ) then
      Print( "#E  all records of type \"key\" or \"keys\" in <list>\n",
             "#E  must have a component 'keys'\n",
             "#E  (a function or a list of [ key, alias ] pairs)\n" );
      return false;
    fi;

    return true;
end;


#############################################################################
##
#F  BrowseData.EditCurrentStep( <t> )
##
##  <t> is a browse table created by 'BrowseWizard'.
##  This function is called by the <Click> and <Down> actions of the mode
##  'BrowseData.WizardMode'.
##
BrowseData.EditCurrentStep:= function( t )
    local steps, defaults, result, i, curr, key, default, choices, keys,
          index, value, dispvalue, r, winwidth, field, header, hint, ncols,
          win, pan, isvalid, hide, next;

    steps:= t.context.steps;
    defaults:= t.context.defaults;
    result:= t.dynamic.Return;

    # Determine the default value for this step.
    i:= t.dynamic.selectedEntry[1] / 2;
    curr:= steps[i];
    key:= curr.key;

    default:= fail;
    if   IsBound( result.( key ) ) then
      default:= result.( key );
    elif IsBound( defaults.( key ) ) then
      default:= defaults.( key );
    fi;
    if default <> fail and
       BrowseData.ValidateStep( steps, result, i, default ) <> true then
      default:= fail;
    fi;
    if default = fail and IsBound( curr.default ) then
      if IsFunction( curr.default ) then
        default:= curr.default( steps, result );
      else
        default:= curr.default;
      fi;
    fi;

    # Ask for this step's information
    if   curr.type = "ok" then

      # Just show the message.
      if IsBound( t.dynamic.statuspanel ) then
        NCurses.hide_panel( t.dynamic.statuspanel );
      fi;
      BrowseData.AlertWithReplay( t, curr.description, NCurses.attrs.BOLD );
      if IsBound( t.dynamic.statuspanel ) then
        NCurses.show_panel( t.dynamic.statuspanel );
      fi;
      value:= "dummy";
      dispvalue:= "dummy";

    elif curr.type = "okcancel" then

      choices:= rec(
        header:= curr.description,
        items:= [ "OK", "Cancel" ],
        single:= true,
        none:= false,
        border:= NCurses.attrs.BOLD,
        align:= "c",
        size:= "fit",
        replay:= t.dynamic.replay,
        log:= t.dynamic.log,
      );
      if default = "OK" then
        choices.select:= [ 1 ];
      elif default = "Cancel" then
        choices.select:= [ 2 ];
      fi;
      if IsBound( t.dynamic.statuspanel ) then
        NCurses.hide_panel( t.dynamic.statuspanel );
      fi;
      index:= NCurses.Select( choices );
      if IsBound( t.dynamic.statuspanel ) then
        NCurses.show_panel( t.dynamic.statuspanel );
      fi;
      result.( curr.key ):= choices.items[ index ];
      if index = 2 then
        # The user canceled, quit the browse table.
        BrowseData.actions.QuitTable.action( t );
      fi;
      value:= "OK";
      dispvalue:= "OK";

    elif curr.type = "submitcancelcontinue" then

      choices:= rec(
        header:= curr.description,
        items:= [ "Submit", "Cancel", "Continue editing" ],
        single:= true,
        none:= false,
        border:= NCurses.attrs.BOLD,
        align:= "c",
        size:= "fit",
        replay:= t.dynamic.replay,
        log:= t.dynamic.log,
      );

      if default in choices.items then
        choices.select:= [ Position( choices.items, default ) ];
      fi;

      if IsBound( t.dynamic.statuspanel ) then
        NCurses.hide_panel( t.dynamic.statuspanel );
      fi;
      index:= NCurses.Select( choices );
      if IsBound( t.dynamic.statuspanel ) then
        NCurses.show_panel( t.dynamic.statuspanel );
      fi;
      value:= choices.items[ index ];
      dispvalue:= value;
      result.( curr.key ):= value;
      if   index = 1 then
        # The user submitted, quit the browse table.
        result.( curr.key ):= "Submit";
        BrowseData.actions.QuitTable.action( t );
      elif index = 2 then
        # The user canceled, quit the browse table.
        result.( curr.key ):= "Cancel";
        BrowseData.actions.QuitTable.action( t );
      else
        # Go to the last visible step in the table.
        while t.dynamic.isRejectedRow[ 2*i ] do
          i:= i - 1;
        od;
        t.dynamic.selectedEntry[1]:= 2 * i;
        return true;
      fi;

    elif curr.type = "key" or curr.type = "keys" then

      if IsFunction( curr.keys ) then
        keys:= curr.keys( steps, result );
      else
        keys:= curr.keys;
      fi;

      choices:= rec(
        header:= curr.description,
        items:= List( keys, pair -> pair[1] ),
        single:= curr.type = "key",
        none:= true,
        border:= NCurses.attrs.BOLD,
        align:= "c",
        size:= "fit",
        replay:= t.dynamic.replay,
        log:= t.dynamic.log,
      );

      if default <> fail then
        if curr.type = "key" then
          choices.select:= [ PositionProperty( keys, p -> p[2] = default ) ];
        else
          choices.select:= PositionsProperty( keys, p -> p[2] in default );
        fi;
      fi;

      if IsBound( t.dynamic.statuspanel ) then
        NCurses.hide_panel( t.dynamic.statuspanel );
      fi;
      index:= NCurses.Select( choices );
      if IsBound( t.dynamic.statuspanel ) then
        NCurses.show_panel( t.dynamic.statuspanel );
      fi;
      if index = false then
        return false;
      elif curr.type = "key" then
        value:= keys[ index ][2];
        dispvalue:= keys[ index ][1];
      else
        value:= List( keys{ index }, pair -> pair[2] );
        dispvalue:= JoinStringsWithSeparator(
                        List( keys{ index }, p -> p[1] ), ", " );
      fi;

    elif curr.type = "editstring" then

      # Let the user edit the value.
      if default <> fail then
        defaults:= [ default ];
      else
        defaults:= [ "" ];
      fi;
      if IsBound( t.dynamic.statuspanel ) then
        NCurses.hide_panel( t.dynamic.statuspanel );
      fi;
      value:= NCurses.EditFieldsDefault( curr.description, [ "" ], defaults,
                                         NCurses.getmaxyx( 0 )[2],
                                         t.dynamic.replay,
                        t.dynamic.log );
      if IsBound( t.dynamic.statuspanel ) then
        NCurses.show_panel( t.dynamic.statuspanel );
      fi;
      if value = fail then
        # The user canceled.
        return false;
      fi;
      value:= value[1];
      dispvalue:= value;

    elif curr.type = "edittable" then

      # Let the user edit a list of data records.
      if default = fail then
        default:= [];
      fi;

      r:= rec( title:= curr.title,
               list:= StructuralCopy( default ),
               rectodisp:= curr.rectodisp,
               mapping:= curr.mapping );
      if IsBound( curr.choices ) then
        if IsFunction( curr.choices ) then
          r.choices:= curr.choices( steps, result );
        else
          r.choices:= curr.choices;
        fi;
      fi;
      if IsBound( t.dynamic.statuspanel ) then
        NCurses.hide_panel( t.dynamic.statuspanel );
      fi;
      value:= NCurses.EditTable( r );
      if IsBound( t.dynamic.statuspanel ) then
        NCurses.show_panel( t.dynamic.statuspanel );
      fi;
      if value = false then
        # Nothing was done.
        return false;
      fi;
      if IsBound( t.dynamic.statuspanel ) then
        NCurses.hide_panel( t.dynamic.statuspanel );
      fi;
      repeat
        value:= NCurses.EditTable( r );
      until value = false;
      if IsBound( t.dynamic.statuspanel ) then
        NCurses.show_panel( t.dynamic.statuspanel );
      fi;
      value:= r.list;
      dispvalue:= List( value, curr.rectodisp );

    else
      Error( "unknown type" );
    fi;

    # Validate the result.
    isvalid:= BrowseData.ValidateStep( steps, result, i, value );
    if isvalid <> true then

      BrowseData.ShowValidationMessage( t, isvalid );
      return false;

    elif not IsBound( result.( curr.key ) ) or
         result.( curr.key ) <> value then

      # Enter the changed value in the result record.
      result.( curr.key ):= value;

      # Make the chosen values visible in the table.
      if curr.type = "edittable" then
        # The number of rows may have changed, so clear the cached value.
        t.work.main[i][1].rows:= Concatenation(
            [ t.work.main[i][1].rows[1] ],
            List( dispvalue, x -> Concatenation( "    ", x ) ),
            [ "" ] );
        Unbind( t.work.heightRow[ 2*i ] );
      else
        t.work.main[i][1].rows[2]:= Concatenation( "    ", dispvalue );
      fi;
    fi;

    # Recompute the hide conditions further down,
    # and remove components in the result that correspond to hidden entries.
    hide:= t.dynamic.isRejectedRow;
    next:= Length( steps ) + 1;
    while i < Length( steps ) do
      i:= i + 1;
      if IsBound( steps[i].isVisible ) then
        if steps[i].isVisible( steps, result ) = false then
          hide[ 2*i ]:= true;
          hide[ 2*i + 1 ]:= true;
          Unbind( result.( steps[i].key ) );
        else
          hide[ 2*i ]:= false;
          hide[ 2*i + 1 ]:= false;
        fi;
      fi;
      if not hide[ 2*i ] then
        next:= i;
      fi;
    od;

    i:= t.dynamic.selectedEntry[1] / 2;
    i:= First( [ i+1 .. Minimum( Length( steps ), next-1 ) ], 
               x -> steps[x].type in
                             [ "ok", "okcancel", "submitcancelcontinue" ] );
    if i <> fail then
      # There is a hidden step that shall be executed next.
      # Update the window and then execute this step.
      BrowseData.CurrentMode( t ).ShowTables( t );
      NCurses.update_panels();
      NCurses.doupdate();
      t.dynamic.selectedEntry[1]:= 2 * i;
      return BrowseData.EditCurrentStep( t );
    elif next <= Length( steps ) then
      # Move on to the next visible step if there is one.
      return BrowseData.actions.ScrollSelectedCellDown.action( t );
    else
      # This was the last step, and we have not met a question whether we
      # want to continue editing.
      # Thus we exit the browse table.
      return BrowseData.actions.QuitTable.action( t );
    fi;
end;


#############################################################################
##
#F  BrowseData.ValidateStep( <steps>, <record>, <i>, <value> )
##
##  This function returns either 'true' or a string that describes why the
##  validation failed.
##
BrowseData.ValidateStep:= function( steps, record, i, value )
    local curr, keys;

    curr:= steps[i];

    if curr.type = "key" or curr.type = "keys" then
      # Check that only admissible keys are involved.  (This can fail if the
      # defaults record does not fit to the current configuration.)
      if IsFunction( curr.keys ) then
        keys:= curr.keys( steps, record );
      else
        keys:= curr.keys;
      fi;
      keys:= List( keys, x -> x[2] );
      if curr.type = "key" and not value in keys then
        return "The chosen key is not admissible.";
      elif curr.type = "keys" and not ForAll( value, x -> x in keys ) then
        return "Not all chosen keys are admissible.";
      fi;
    fi;
    if IsBound( curr.validation ) then
      # Apply the dedicated function.
      return curr.validation( steps, record, value );
    fi;

    return true;
end;


#############################################################################
##
#F  BrowseData.ShowValidationMessage( <t>, <msg> )
##
BrowseData.ShowValidationMessage:= function( t, msg )
    msg:= SplitString( BrowseData.ReallyFormatParagraph( msg,
                           NCurses.getmaxyx( 0 )[2] - 4, "left" ), "\n" );
    if IsBound( t.dynamic.statuspanel ) then
      NCurses.hide_panel( t.dynamic.statuspanel );
    fi;
    BrowseData.AlertWithReplay( t,
        Concatenation( [ "validation failed: " ], msg ),
        NCurses.attrs.BOLD );
    if IsBound( t.dynamic.statuspanel ) then
      NCurses.show_panel( t.dynamic.statuspanel );
    fi;
end;


#############################################################################
##
#V  BrowseData.WizardMode
##
##  This mode is used by the function 'BrowseWizard'.
##  It admits only vertical scrolling and clicking the selected entry.
##
BrowseData.WizardMode:= BrowseData.CreateMode( "wizard", "select_row", [
    # standard actions
    [ [ "E" ], BrowseData.actions.Error ],
    [ [ "q", [ [ 27 ], "<Esc>" ] ], BrowseData.actions.QuitMode ],
    [ [ "Q" ], BrowseData.actions.QuitTable ],
    [ [ "?", [ [ NCurses.keys.F1 ], "<F1>" ] ],
      BrowseData.actions.ShowHelp ],
    [ [ [ [ NCurses.keys.F2 ], "<F2>" ] ], BrowseData.actions.SaveWindow ],
    [ [ [ [ 14 ], "<Ctrl-N>" ] ], BrowseData.actions.DoNothing ],
    # move down if possible, otherwise edit the current step
    [ [ "d", [ [ NCurses.keys.DOWN ], "<Down>" ] ],
      rec(
           helplines:= [ "validate the current step,",
                         "proceed to the next step in the case of success" ],
           action:= function( t )
             local steps, result, i, curr, key, isvalid;

             # If the value is already stored then first validate it,
             # otherwise open the current step.
             steps:= t.context.steps;
             result:= t.dynamic.Return;
             i:= t.dynamic.selectedEntry[1] / 2;
             curr:= steps[i];
             key:= curr.key;
             if IsBound( result.( key ) ) then
               isvalid:= BrowseData.ValidateStep( steps, result, i,
                                                  result.( key ) );
               if isvalid = true then
                 if BrowseData.actions.ScrollSelectedCellDown.action( t ) then
                   # Go to the next step, as required.
                   return true;
                 elif i < Length( steps ) and
                      steps[ i+1 ].type in [ "ok", "okcancel",
                                             "submitcancelcontinue" ] then
                   # The next step is not visible,
                   # update the window and then execute this step.
                   BrowseData.CurrentMode( t ).ShowTables( t );
                   NCurses.update_panels();
                   NCurses.doupdate();
                   t.dynamic.selectedEntry[1]:= t.dynamic.selectedEntry[1] + 2;
                   return BrowseData.EditCurrentStep( t );
                 else
                   # We are at the end of the table.
                   return false;
                 fi;
               fi;

               # Show the validation text.
               BrowseData.ShowValidationMessage( t, isvalid );
             fi;

             # Open the current step.
             return BrowseData.EditCurrentStep( t );
           end,
         ) ],
    # move up (no additional action)
    [ [ "u", [ [ NCurses.keys.UP ], "<Up>" ] ],
      BrowseData.actions.ScrollSelectedCellUp ],
    # open a step
    [ [ [ [ 13 ], "<Return>" ], [ [ NCurses.keys.ENTER ], "<Enter>" ] ],
      BrowseData.actions.ClickOrToggle ],
    ] );


#############################################################################
##
#F  BrowseWizard( <data> )
##
##  <#GAPDoc Label="BrowseWizard_section">
##  <Section Label="sec:browsewizard">
##  <Heading>Managing simple Workflows</Heading>
##
##  The idea behind the function <Ref Func="BrowseWizard"/> is
##  that one wants to collect interactively information from a user,
##  by asking a series of questions.
##  Default answers for these questions can be provided,
##  perhaps depending on the answers to earlier questions.
##  The questions and answers are shown in a browse table,
##  the current question is highlighted, and this selection is automatically
##  moved to the next question after a valid answer has been entered.
##  One may move up in the table, in order to change previous answers,
##  but one can move down only to the first unanswered question.
##  When the browse table gets closed (by submitting or canceling),
##  a record with the collected information is returned.
##
##  <ManSection>
##  <Heading>BrowseWizard</Heading>
##  <Func Name="BrowseWizard" Arg='data'/>
##
##  <Returns>
##  a record.
##  </Returns>
##
##  <Description>
##  The argument <A>data</A> must be a record with the components
##  <C>steps</C> (a list of records, each representing one step in the
##  questionnaire) and <C>defaults</C> (a record).
##  The component <C>header</C>, if present, must be a string that is used
##  as a header line; the default for it is <C>"BrowseWizard"</C>.
##  <P/>
##  <Ref Func="BrowseWizard"/> opens a browse table whose rows correspond to
##  the entries of <A>data</A><C>.steps</C>.
##  The components of <A>data</A><C>.defaults</C> are used as
##  default values if they are present.
##  <P/>
##  Beginning with the first entry, the user is asked to enter information,
##  one record component per entry; this may be done by entering some text,
##  by choosing keys from a given list of choices, or by editing a list of
##  tabular data.
##  Then one can go to the next step by hitting the <B>ArrowDown</B> key
##  (or by entering <B>d</B>), and edit this step by hitting the <B>Enter</B>
##  key.
##  One can also go back to previous steps and edit them again.
##  <P/>
##  Some steps may be hidden from the user, depending on the information that
##  has been entered for the previous steps.
##  The hide conditions are evaluated after each step.
##  <P/>
##  An implementation of a questionnaire is given by
##  <C>BrowseData.ChooseSimpleGroupQuestions</C>,
##  which is used in the following example.
##  The idea is to choose the description of a finite simple group by
##  entering first the type (cyclic, alternating, classical, exceptional, or
##  sporadic) and then the relevant parameter values.
##  The information is then evaluated by
##  <C>BrowseData.InterpretSimpleGroupDescription</C>, which returns a
##  description that fits to the return values of
##  <Ref Func="IsomorphismTypeInfoFiniteSimpleGroup" BookName="ref"/>.
##  For example, this function identifies the group <C>PSL</C><M>(4,2)</M>
##  as <M>A_8</M>.)
##  <P/>
##  <Example><![CDATA[
##  gap> d:= [ NCurses.keys.DOWN ];;  r:= [ NCurses.keys.RIGHT ];;
##  gap> c:= [ NCurses.keys.ENTER ];;
##  gap> BrowseData.SetReplay( Concatenation(
##  >        c,             # confirm the initial message
##  >        d,             # enter the first step
##  >        d, d,          # go to the choice of classical groups
##  >        c,             # confirm this choice
##  >        c,             # enter the next step
##  >        d, d,          # go to the choice of unitary groups
##  >        c,             # confirm this choice
##  >        c,             # enter the next step
##  >        "5", c,        # enter the dimension and confirm
##  >        c,             # enter the next step
##  >        "3", c,        # enter the field size and confirm
##  >        c ) );         # confirm all choices (closes the table)
##  gap> res:= BrowseWizard( rec(
##  >      steps:= BrowseData.ChooseSimpleGroupQuestions,
##  >      defaults:= rec(),
##  >      header:= "Choose a finite simple group" ) );;
##  gap> BrowseData.SetReplay( false );
##  gap> BrowseData.InterpretSimpleGroupDescription( res );
##  rec( parameter := [ 4, 3 ], requestedname := "U5(3)", series := "2A", 
##    shortname := "U5(3)" )
##  ]]></Example>
##  <P/>
##  The supported components of each entry in <A>data</A><C>.steps</C> are
##  as follows.
##  <List>
##  <Mark><C>key</C></Mark>
##  <Item>
##    a string, the name of the component of the result record that gets
##    bound for this entry.
##  </Item>
##  <Mark><C>description</C></Mark>
##  <Item>
##    a string describing what information shall be entered.
##  </Item>
##  <Mark><C>type</C></Mark>
##  <Item>
##    one of <C>"editstring"</C>, <C>"edittable"</C>, <C>"key"</C>,
##    <C>"keys"</C>, <C>"ok"</C>, <C>"okcancel"</C>,
##    <C>"submitcancelcontinue"</C>.
##  </Item>
##  <Mark><C>keys</C>
##        (only if <C>type</C> is <C>"key"</C> or <C>"keys"</C>)</Mark>
##  <Item>
##    either the list of pairs <C>[ key, alias ]</C> such that the user shall
##    choose from the list of <C>key</C> values (strings),
##    and the <C>alias</C> values (any &GAP; object) corresponding to the
##    chosen values are entered into the result record,
##    or a function that takes <A>steps</A> and the current result record as
##    its arguments and returns the desired list of pairs.
##  </Item>
##  <Mark><C>validation</C> (optional)</Mark>
##  <Item>
##    a function that takes <A>steps</A>, the current result record,
##    and a result candidate for the current step as its arguments;
##    it returns <K>true</K> if the result candidate is valid,
##    and a string describing the reason for the failure otherwise.
##  </Item>
##  <Mark><C>default</C> (optional)</Mark>
##  <Item>
##    depending on the <C>type</C> value, the alias part(s) of the chosen
##    key(s) or the string or the list of data records,
##    or alternatively a function that takes <A>steps</A> and the current
##    result record as its arguments and returns the desired value.
##    If the <C>key</C> component of <A>data</A><C>.defaults</C> is bound
##    and valid (according to the <C>validation</C> function) then this value
##    is taken as the default;
##    otherwise, the <C>default</C> component of the entry is taken as the
##    default.
##  </Item>
##  <Mark><C>isVisible</C> (optional)</Mark>
##  <Item>
##    a function that takes <A>steps</A> and the current result record as
##    its arguments and returns <K>true</K> if the step shall be visible,
##    and <K>false</K> otherwise,
##  </Item>
##  </List>
##  <P/>
##  If the <C>type</C> value of a step is <C>"edittable"</C> then also the
##  following components are mandatory.
##  <P/>
##  <List>
##  <Mark><C>list</C></Mark>
##  <Item>
##    the current list of records to be edited;
##    only strings are supported as the values of the record components.
##  </Item>
##  <Mark><C>mapping</C></Mark>
##  <Item>
##    a list of pairs <C>[ component, label ]</C> such that <C>component</C>
##    is the name of a component in the entries in <C>list</C>,
##    and <C>label</C> is the label shown in the dialog box for editing the
##    record.
##  </Item>
##  <Mark><C>choices</C> (optional)</Mark>
##  <Item>
##    a list of records which can be added to <C>list</C>.
##  </Item>
##  <Mark><C>rectodisp</C></Mark>
##  <Item>
##    a function that takes a record from <C>list</C> and returns a string
##    that is shown in the browse table.
##  </Item>
##  <Mark><C>title</C></Mark>
##  <Item>
##    a string, the header line of the dialog box for editing an entry.
##  </Item>
##  </List>
##  <P/>
##  The code of <Ref Func="BrowseWizard"/>,
##  <C>BrowseData.ChooseSimpleGroupQuestions</C>, and
##  <C>BrowseData.InterpretSimpleGroupDescription</C>
##  can be found in the file <F>app/wizard.g</F> of the package.
##  </Description>
##  </ManSection>
##  </Section>
##  <#/GAPDoc>
##
BindGlobal( "BrowseWizard", function( data )
    local steps, defaults, header, result, main, i, entry, key, keys, value,
          table, hide;

    if not ( IsRecord( data ) and IsBound( data.steps )
                              and IsBound( data.defaults ) ) then
      Error( "<data> must be a record with the components ",
             "'steps' and 'defaults'" );
    fi;

    steps:= data.steps;
    defaults:= data.defaults;

    if not BrowseData.IsQuestionnaire( steps ) then
      Error( "<steps> is not a questionnaire" );
    elif not steps[ Length( steps ) ].type in
         [ "ok", "okcancel", "submitcancelcontinue" ] then
      # Add a default step at the end that asks for confirmation.
      steps:= ShallowCopy( steps );
      Add( steps, rec( key:= "final",
                       description:= "The information is complete.",
                       type:= "submitcancelcontinue",
                       default:= "Submit",
                     ) );
    fi;

    if IsBound( data.header ) then
      header:= data.header;
    else
      header:= "BrowseWizard";
    fi;

    # Set the defaults, and create the main matrix.
    result:= rec();
    main:= [];
    for i in [ 1 .. Length( steps ) ] do

      entry:= [ Concatenation( "- ", steps[i].description ) ];
      key:= steps[i].key;
      if ( not steps[i].type in
           [ "ok", "okcancel", "submitcancelcontinue" ] ) and
         IsBound( defaults.( key ) ) and
         BrowseData.ValidateStep( steps, result, i,
                                  defaults.( key ) ) = true then
        result.( key ):= defaults.( key );
        if steps[i].type in [ "key", "keys" ] then
          if IsFunction( steps[i].keys ) then
            keys:= steps[i].keys( steps, result );
          else
            keys:= steps[i].keys;
          fi;
          value:= First( keys, x -> x[2] = defaults.( key ) );
          if value <> fail then
            Add( entry, Concatenation( "    ", value[1] ) );
          else
            Add( entry, "" );
          fi;
        elif steps[i].type = "edittable" then
          Append( entry, List( defaults.( key ),
                               r -> Concatenation( "    ",
                                        steps[i].rectodisp( r ) ) ) );
        else
          Add( entry, Concatenation( "    ", String( defaults.( key ) ) ) );
        fi;
      else
        Add( entry, "" );
      fi;
      Add( entry, "" );
      main[i]:= [ rec( rows:= entry, align:= "tl" ) ];
    od;

    # Construct the browse table.
    table:= rec(
      work:= rec(
        align:= "tl",
        header:= [ "",
                   [ NCurses.attrs.UNDERLINE, true, header ],
                   "" ],
        availableModes:= [ BrowseData.WizardMode,
                           First( BrowseData.defaults.work.availableModes,
                                  x -> x.name = "help" ) ],
        main:= main,
        sepCol:= [ "", "" ],
        widthCol:= [ , NCurses.getmaxyx( 0 )[2] ],
        Click:= rec(
          wizard:= rec(
            helplines:= [ "edit the current step" ],
            action:= BrowseData.EditCurrentStep,
          ),
        ),
      ),
      dynamic:= rec(
        activeModes:= [ BrowseData.WizardMode ],
        selectedEntry:= [ 2, 2 ],  # gets adjusted by replay if hidden
#T TODO: replay? no longer available, or?
        isRejectedRow:= ListWithIdenticalEntries( 2 * Length( steps ) + 1,
                                                  false ),
        Return:= result,
      ),
      context:= rec(
        steps:= steps,
        defaults:= defaults,
      ),
    );

    # Hide rows according to the initial status.
    hide:= table.dynamic.isRejectedRow;
    for i in [ 1 .. Length( steps ) ] do
      if steps[i].type in [ "ok", "okcancel", "submitcancelcontinue" ] or
         ( IsBound( steps[i].isVisible ) and
           steps[i].isVisible( steps, rec() ) = false ) then
        hide[ 2*i ]:= true;
        hide[ 2*i + 1 ]:= true;
      fi;
    od;

    # If a hidden step comes first then trigger its action,
    # via 'table.dynamic.initialSteps'.
    if hide[2] then
      table.dynamic.initialSteps:= [ 258 ];
    fi;

    # Show the browse table.
    return NCurses.BrowseGeneric( table );
end );


#############################################################################
##
#V  BrowseData.LieTypesClas
##
##  three descriptions of the types of classical groups of Lie type:
##  textual, Chevalley notation, ATLAS notation
##
##  This is used in 'BrowseData.ChooseSimpleGroupQuestions' and in
##  'BrowseData.InterpretSimpleGroupDescription'.
##
BrowseData.LieTypesClas:= [
  [ "linear", "symplectic", "unitary", "orthogonal in odd dimension",
    "orthogonal of plus type", "orthogonal of minus type" ],
  [ "A", "C", "2A", "B", "D", "2D" ],
  [ "L", "S", "U", "O", "O+", "O-" ] ];


#############################################################################
##
#V  BrowseData.ChooseSimpleGroupQuestions
##
##  This is a questionnaire for choosing a finite simple group via
##  'BrowseWiziard', by entering first the type (cyclic, alternating,
##  classical, exceptional, or sporadic)
##  and then the relevant parameter values (the order of a cyclic group;
##  the degree of an alternating group; series, dimension and field size of a
##  classical group of Lie type; series and field size of an exceptional
##  group of Lie type; name of a sporadic simple group).
##
##  It is used in the 'BrowseWizard' example in the documentation.
##
BrowseData.ChooseSimpleGroupQuestions:= [
  rec( key:= "Welcome",
       description:= [
         "Welcome to the choice of a simple group",
         "by series and parameters.",
         "",
         "(Hit any key to continue.)",
       ],
       type:= "ok",
     ),
  rec( key:= "Type",
       description:= "Please choose a type of simple groups.",
       type:= "key",
       keys:= [
         [ "cyclic", "cyc" ],
         [ "alternating", "alt" ],
         [ "classical", "clas" ],
         [ "exceptional", "exc" ],
         [ "sporadic", "spor" ],
       ],
       default:= "",
     ),
  rec( key:= "Order",
       description:= "Please choose the order of the cyclic group.",
       type:= "editstring",
       validation:= function( steps, result, value )
         local n;
         n:= Int( value );
         if n = fail or not IsPrimeInt( n ) then
           return "The order must be a prime integer";
         fi;
         return true;
       end,
       isVisible:= function( steps, result )
         return IsBound( result.Type ) and result.Type = "cyc";
       end,
     ),
  rec( key:= "Degree",
       description:= "Please choose the degree of the alternating group.",
       type:= "editstring",
       validation:= function( steps, result, value )
         local n;
         n:= Int( value );
         if n = fail or n < 5 then
           return "The degree must be an integer >= 5";
         fi;
         return true;
       end,
       isVisible:= function( steps, result )
         return IsBound( result.Type ) and result.Type = "alt";
       end,
     ),
  rec( key:= "ClassicalType",
       description:= "Please choose the classical type.",
       type:= "key",
       keys:= List( TransposedMat( BrowseData.LieTypesClas ),
                    x -> [ Concatenation( x[1], " (type ", x[2], ")" ),
                           x[3] ] ),
       default:= "",
       isVisible:= function( steps, result )
         return IsBound( result.Type ) and result.Type = "clas";
       end,
     ),
  rec( key:= "ExceptionalType",
       description:= "Please choose the exceptional type.",
       type:= "key",
       keys:= [
         [ "2B2 (Suzuki)", "2B2" ],
         [ "2E6", "2E6" ],
         [ "2F4 (Ree in char. 2)", "2F4" ],
         [ "2G2 (Ree in char. 3)", "2G2" ],
         [ "3D4", "3D4" ],
         [ "E6", "E6" ],
         [ "E7", "E7" ],
         [ "E8", "E8" ],
         [ "F4", "F4" ],
         [ "G2", "G2" ],
       ],
       default:= "",
       isVisible:= function( steps, result )
         return IsBound( result.Type ) and result.Type = "exc";
       end,
     ),
  rec( key:= "Name",
       description:= "Please choose the sporadic simple group.",
       type:= "key",
       keys:= List( [ "M11", "M12", "J1", "M22", "J2", "M23", "2F4(2)'",
                      "HS", "J3", "M24", "McL", "He", "Ru", "Suz", "ON",
                      "Co3", "Co2", "Fi22", "HN", "Ly", "Th", "Fi23", "Co1",
                      "J4", "F3+", "B", "M" ],
                    x -> [ x, x ] ),
       default:= "",
       isVisible:= function( steps, result )
         return IsBound( result.Type ) and result.Type = "spor";
       end,
     ),
  rec( key:= "Dimension",
       description:= "Please choose the classical dimension.",
       type:= "editstring",
       validation:= function( steps, result, value )
         local n;
         n:= Int( value );
         if n = fail or n < 2 then
           return "The dimension must be an integer >= 2";
         elif n = 2 and result.ClassicalType[1] = 'O' then
           return "The group in question is not simple";
         elif n = 4 and result.ClassicalType = "O+" then
           return "The group in question is not simple";
         elif result.ClassicalType = "O" and IsEvenInt( n ) then
           return "The dimension for type O must be odd";
         elif result.ClassicalType[1] = 'O' and IsOddInt( n ) then
           return "The dimension for type O+ or O- must be even";
         elif result.ClassicalType = "S" and IsOddInt( n ) then
           return "The dimension for type S must be even";
         fi;
         return true;
       end,
       isVisible:= function( steps, result )
         return IsBound( result.Type ) and result.Type = "clas";
       end,
     ),
  rec( key:= "Q",
       description:= "Please choose the size of the field of definition.",
       type:= "editstring",
       validation:= function( steps, result, value )
         local q;
         q:= Int( value );
         if q = fail or not IsPrimePowerInt( q ) then
           return "The size of the field of definition must be a prime power";
         elif IsBound( result.ClassicalType ) and
              [ result.ClassicalType, result.Dimension, q ] in
              [ [ "L", "2", 2 ], [ "L", "2", 3 ],
                [ "U", "2", 2 ], [ "U", "2", 3 ], [ "U", "3", 2 ],
                [ "S", "2", 2 ], [ "S", "2", 3 ], [ "S", "4", 2 ],
                [ "O", "3", 2 ], [ "O", "3", 3 ], [ "O", "5", 2 ],
              ] then
           return "The group in question is not simple";
         elif IsBound( result.ExceptionalType ) and
              ( ( result.ExceptionalType = "2G" and
                  ( q mod 3 <> 0 or q = 3 or not IsSquareInt( q/3 ) ) ) or
                ( result.ExceptionalType in [ "2B", "2F" ] and
                  ( q mod 2 <> 0 or q = 2 or not IsSquareInt( q/3 ) ) ) ) then
           return "The group in question does not exist or is not simple";
         fi;
         return true;
       end,
       isVisible:= function( steps, result )
         return IsBound( result.Type ) and
                result.Type in [ "clas", "exc" ];
       end,
     ),
];;


#############################################################################
##
#V  BrowseData.InterpretSimpleGroupDescription( <record> )
##
##  Take the output <record> of 'BrowseWizard' when this is called with the
##  questionnaire 'BrowseData.ChooseSimpleGroupQuestions',
##  and return a record with components 'series', 'parameter', 'shortname',
##  and 'requestedname',
##  where the first three components correspond to the component with these
##  names in records returned by 'IsomorphismTypeInfoFiniteSimpleGroup',
##  and the last component describes what was chosen in the 'BrowseWizard'
##  call;
##  note that one may choose the group L4(2) as a classical group,
##  but the record returned by 'IsomorphismTypeInfoFiniteSimpleGroup' regards
##  the group as A8.
##
BrowseData.InterpretSimpleGroupDescription:= function( result )
    local type, series, n, Q, q, m;

    if result.final = "Cancel" then
      result:= fail;
    elif result.Type = "cyc" then
      result:= rec( series:= "Z",
                    parameter:= Int( result.Order ),
                    shortname:= Concatenation( "C", result.Order ) );
    elif result.Type = "alt" then
      result:= rec( series:= "A",
                    parameter:= Int( result.Degree ),
                    shortname:= Concatenation( "A", result.Degree ) );
    elif result.Type = "clas" then
      type:= result.ClassicalType;
      series:= BrowseData.LieTypesClas[2][ Position(
          BrowseData.LieTypesClas[3], type ) ];
      if series = "A" then
        series:= "L";
      fi;
      n:= result.Dimension;
      Q:= result.Q;
      q:= Int( Q );
      m:= Int( n );
      result:= rec( series:= series,
                    parameter:= [ m, q ],
                    shortname:= Concatenation( type{[1]}, n,
                                    type{[2..Length(type)]}, "(", Q, ")" ) );
      result.requestedname:= result.shortname;

      # Adjust the values.
      if type = "L" then
        if m = 2 and q in [ 4, 5 ] then
          # Replace L2(4) and L2(5) by A5.
          result.series:= "A";
          result.parameter:= 5;
          result.shortname:= "A5";
        elif m = 2 and q = 9 then
          # Replace L2(9) by A6.
          result.series:= "A";
          result.parameter:= 6;
          result.shortname:= "A6";
        elif m = 3 and q = 2 then
          # Replace L3(2) by L2(7).
          result.parameter:= [ 2, 7 ];
          result.shortname:= "L3(2)";
        elif m = 4 and q = 2 then
          # Replace L4(2) by A8.
          result.series:= "A";
          result.parameter:= 8;
          result.shortname:= "A8";
        fi;
      elif type = "U" then
        if m = 2 then
          # Replace U2(q) by L2(q).
          result.series:= "L";
          result.shortname:= Concatenation( "L2(", Q, ")" );
        else
          result.parameter[1]:= m-1;
        fi;
      elif type = "S" then
        if m = 2 then
          # Replace S2(q) by L2(q).
          result.series:= "L";
          result.shortname:= Concatenation( "L2(", Q, ")" );
        elif m = 4 and q = 3 then
          # Replace S4(3) by U4(2).
          result.series:= "2A";
          result.parameter:= [ 2, 3 ];
          result.shortname:= "U4(2)";
        else
          result.parameter[1]:= m/2;
        fi;
      elif type[1] = 'O' then
        if m = 3 then
          # Replace O3(q) by L2(q).
          result.series:= "L";
          result.parameter[1]:= 2;
          result.shortname:= Concatenation( "L2(", Q, ")" );
        elif m = 4 and type = "O-" then
          # Replace O4-(q) by L2(q^2).
          result.series:= "L";
          result.parameter:= [ 2, q^2 ];
          result.shortname:= Concatenation( "L2(", String( q^2 ), ")" );
        elif m = 5 then
          # Replace O5(q) by S4(q).
          result.series:= "C";
          result.parameter[1]:= 4;
          result.shortname:= Concatenation( "S4(", Q, ")" );
        elif m = 6 and type = "O+" then
          # Replace O6+(q) by L4(q).
          result.series:= "L";
          result.parameter[1]:= 4;
          result.shortname:= Concatenation( "L4(", Q, ")" );
        elif m = 6 and type = "O-" then
          # Replace O6-(q) by U4(q).
          result.series:= "2A";
          result.parameter[1]:= 4;
          result.shortname:= Concatenation( "2A3(", Q, ")" );
        else
          result.parameter[1]:= Int( m/2 );
        fi;
      fi;
    elif result.Type = "exc" then
      type:= result.ExceptionalType;
      series:= type{ [ 1 .. Length( type )-1 ] };
      Q:= result.Q;
      q:= Int( Q );

      result:= rec( series:= series,
                    parameter:= q,
                    shortname:= Concatenation( type, "(", Q, ")" ) );

      # Adjust the values.
      if series = "E" then
        result.parameter:= [ Int( type{ [ 2 ] } ), q ];
      elif series = "2B" then
        result.shortname:= Concatenation( "Sz(", Q, ")" );
      elif series = "2G" then
        result.shortname:= Concatenation( "R(", Q, ")" );
      fi;
    elif result.Type = "spor" then
      if result.Name = "2F4(2)'" then
        # 'IsomorphismTypeInfoFiniteSimpleGroup' puts this group into '2F'
        result:= rec( series:= "2F",
                      parameter:= 2,
                      shortname:= result.Name );
      else
        result:= rec( series:= "Spor",
                      shortname:= result.Name );
      fi;
    else
      Error( "this should not happen" );
    fi;

    if not IsBound( result.requestedname ) then
      result.requestedname:= result.shortname;
    fi;

    return result;
end;


#############################################################################
##
#E

