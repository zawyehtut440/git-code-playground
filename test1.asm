. comment
  . indexed addressing
.. free format coding
. empty line detection
. . comand line user filenames input

COPY START 2000	. program start here
FIRST STL RETADR
CLOOP JSUB RDREC
LDA LENGTH
COMP ZERO
JEQ ENDFIL
JSUB 	WRREC
J CLOOP
ENDFIL LDA EOF
STA BUFFER
LDA THREE
STA LENGTH
JSUB WRREC
LDL RETADR
	RSUB
EOF BYTE C'EOF'
THREE WORD 3
ZERO WORD 0
RETADR RESW 1
LENGTH RESW 1
BUFFER RESB 4096
.
.
.
RDREC LDX ZERO    .. subroutine
LDA ZERO
RLOOP TD INPUT
JEQ RLOOP
RD INPUT
COMP ZERO
JEQ EXIT
STCH BUFFER ,X
TIX MAXLEN
JLT RLOOP
EXIT STX LENGTH
RSUB
INPUT BYTE X'F1'
MAXLEN WORD 4096
.
.
.

WRREC LDX 		. . subroutine
WLOOP TD OUTPUT
WLOOP TD OUTPUT
JEQ 
LDCHS BUFFER, X
WD OUTPU
TIX LENGTH
JLT WLOOP
TEST RSUB
OUTPUT BYTE X'05'
END WRREC

.. . end of this program