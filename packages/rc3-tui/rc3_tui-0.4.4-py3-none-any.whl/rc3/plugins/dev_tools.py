"""
Vim Hotkey Reference Guide - Quick reference for vim keybindings
"""

from textual.widgets import Static
from rc3.plugins.base import BasePlugin


class Plugin(BasePlugin):
    """Vim hotkey reference guide plugin"""
    
    name = "Vim Hotkeys"
    description = "Vim keybinding reference guide"
    
    def render(self):
        """Render the vim hotkey reference guide"""
        guide = """VIM HOTKEY REFERENCE GUIDE

═══════════════════════════════════════════════════════════════════
BASIC ESSENTIALS
═══════════════════════════════════════════════════════════════════

MODE SWITCHING
  i            Insert mode (before cursor)
  a            Insert mode (after cursor)
  o            Insert mode (new line below)
  O            Insert mode (new line above)
  ESC          Return to Normal mode
  v            Visual mode (character selection)
  V            Visual mode (line selection)
  Ctrl+v       Visual block mode
  :            Command mode

NAVIGATION
  h j k l      Left, Down, Up, Right
  w            Next word start
  b            Previous word start
  e            Next word end
  0            Start of line
  ^            First non-blank character
  $            End of line
  gg           Top of file
  G            Bottom of file
  {number}G    Go to line number
  Ctrl+d       Page down
  Ctrl+u       Page up

SAVE & QUIT
  :w           Save file
  :q           Quit (fails if unsaved)
  :wq          Save and quit
  :q!          Quit without saving
  :x           Save and quit (only if changes)
  ZZ           Save and quit
  ZQ           Quit without saving

BASIC EDITING
  x            Delete character under cursor
  dd           Delete line
  yy           Copy (yank) line
  p            Paste after cursor/line
  P            Paste before cursor/line
  u            Undo
  Ctrl+r       Redo
  .            Repeat last command
  >>           Indent line
  <<           Unindent line

═══════════════════════════════════════════════════════════════════
INTERMEDIATE
═══════════════════════════════════════════════════════════════════

TEXT OBJECTS (combine with d, c, y, v)
  iw           Inner word
  aw           A word (includes surrounding whitespace)
  is           Inner sentence
  as           A sentence
  ip           Inner paragraph
  ap           A paragraph
  i" i' i`     Inside quotes
  a" a' a`     Around quotes (includes quotes)
  i( i[ i{     Inside brackets
  a( a[ a{     Around brackets (includes brackets)
  it           Inner tag (HTML/XML)
  at           Around tag

REGISTERS
  "ay          Yank into register a
  "ap          Paste from register a
  :reg         Show all registers
  "+y          Copy to system clipboard
  "+p          Paste from system clipboard

MARKS
  ma           Set mark 'a' at cursor
  'a           Jump to mark 'a'
  `a           Jump to mark 'a' exact position
  '.           Jump to last edit position
  ''           Jump back to previous position

SEARCH & REPLACE
  /pattern     Search forward
  ?pattern     Search backward
  n            Next match
  N            Previous match
  *            Search word under cursor (forward)
  #            Search word under cursor (backward)
  :s/old/new   Replace first on line
  :s/old/new/g Replace all on line
  :%s/old/new/g Replace in entire file
  :%s/old/new/gc Replace with confirmation

VISUAL MODE OPERATIONS
  v + motion   Select text
  V + motion   Select lines
  Ctrl+v       Block select
  >            Indent selection
  <            Unindent selection
  y            Yank selection
  d            Delete selection
  c            Change selection
  ~            Toggle case
  U            Uppercase
  u            Lowercase

ADVANCED MOVEMENTS
  f{char}      Find next {char} on line
  F{char}      Find previous {char} on line
  t{char}      Till next {char} on line
  T{char}      Till previous {char} on line
  ;            Repeat last f/F/t/T
  ,            Repeat last f/F/t/T reverse
  %            Jump to matching bracket

MULTIPLE FILES
  :e file      Edit file
  :bn          Next buffer
  :bp          Previous buffer
  :bd          Delete buffer (close file)
  :ls          List buffers

═══════════════════════════════════════════════════════════════════
"""
        
        return Static(guide, classes="info")
