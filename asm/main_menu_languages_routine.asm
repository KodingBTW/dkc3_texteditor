;--------------------------------------------
; Change default language at startup
; A = 00 default language English
;--------------------------------------------
org $407FC0
change_default_language:
	REP #$20
	LDA #$0001				; Force french startup default language
	STA $06D6				; Write in memory
	LDA #$0000
	TCD
	LDX #$01FF
	TXS
	JML continue			; Return

org $8082E7
default_language:
	JML change_default_language	; Change bank
continue:
	NOP
	NOP
	NOP
	NOP
	NOP
	NOP
	NOP
	NOP
	NOP
	JSL $BB8564
	JSR $81C5
	JSL $808C77

;--------------------------------------------
; WRAM $06D6 = language flag (00=English, 01=Francais)
; Input UP
;--------------------------------------------
org $809BA2

check_menu_state_up_input:
    LDA #$00D7                 	; Load menu ID / wheel base index
    STA $1A                    	; Store into WRAM $1A (wheel wrap value)
    LDA $1C83                  	; Read input debounce counter
    BNE scroll_up_wheel        	; If still counting down, skip SFX and reload
    LDA #$0666                 	; Sound effect ID for menu navigation
    JSL $B28012                	; Play the navigation SFX
    LDA #$0008                 	; Reload debounce timer (prevents rapid scrolling)
    STA $1C83                  	; Store debounce

scroll_up_wheel:
    LDA $1CB0                  	; Load raw controller input
    AND #$003F                 	; Keep only D-pad/action bits
    STA $1C                    	; Save filtered input
    LDA $1CB0                  	; Reload complete buffer
    AND #$0FC0                 	; Clear lower 6 bits (consumed by previous AND)
    STA $1CB0                  	; Update buffer

    LDX #$1C51                 	; Pointer to the language wheel tile entries
    JSR move_wheel_up          	; Scroll wheel entry 1 upward
    JSR move_wheel_up          	; Scroll wheel entry 2 upward
    JSR move_wheel_up          	; Scroll wheel entry 3 upward
    JSR move_wheel_up          	; Scroll wheel entry 4 upward

    LSR $1C                    	; Shift input bits; UP becomes carry-out
    BCC change_language_up     	; If carry clear → no UP press detected
    LDA #$0020                 	; If UP detected, set the appropriate flag
    STA $1C

change_language_up:
    LDA $1C                    	; Load interpreted input state
    TSB $1CB0                  	; Acknowledge button press (merge bits)
    DEC $1C83                  	; Decrement debounce timer
    BNE return_up              	; If still nonzero, do NOT toggle language yet

    LDA #$0006                 	; Sound effect ID for language toggle
    JSR $A3E9                  	; Play toggle SFX

    TYX                        	; Move cursor index Y → X
    STZ $38,X                  	; Clear menu entry at index X

    LDA $06D6                  	; Load current language flag
    LDA #$0001                 	; Force french language (FRENCH NOW)
    STA $06D6                  	; Store new language flag
	
    SEP #$20                   	; A = 8-bit mode
    STA $B06008                	; Send new language flag to hardware
    REP #$20                   	; Back to 16-bit accumulator

    JSR $9E09                  	; Refresh menu text with new language

return_up:
    RTS							; Return		

;--------------------------------------------
; WRAM $06D6 = language flag (00=English, 01=Francais)
; Input Down
;--------------------------------------------
org $809C0A
check_menu_state_down_input:
    LDA #$00D7                 	; Load menu ID / wheel base index
    STA $1A                    	; Store in WRAM $1A (wheel wrap value)
    LDA $1C83                  	; Read debounce counter
    BNE scroll_down_wheel      	; If active, skip SFX and reload logic
    LDA #$0666                 	; Menu navigation SFX ID
    JSL $B28012                	; Play the SFX
    LDA #$0008                 	; Reload debounce delay
    STA $1C83                  	; Store debounce timer

scroll_down_wheel:
    LDA $1CB0                  	; Load raw controller input
    AND #$003F                 	; Keep only D-pad/action bits
    STA $1C                    	; Save filtered input
    LDA $1CB0                  	; Reload full input buffer
    AND #$0FC0                 	; Clear lower bits (already processed)
    STA $1CB0                  	; Update buffer

    LDX #$1C51                 	; Base address of wheel tile entries
    JSR move_wheel_down        	; Scroll wheel entry 1 downward
    JSR move_wheel_down        	; Scroll wheel entry 2 downward
    JSR move_wheel_down        	; Scroll wheel entry 3 downward
    JSR move_wheel_down        	; Scroll wheel entry 4 downward

    ASL $1C                    	; Shift input left; DOWN ends up in bit 6
    LDA $1C                    	; Reload shifted input
    BIT #$0040                 	; Test bit 6 (DOWN press)
    BEQ change_language_down   	; If DOWN is pressed → go toggle language
    LDA #$0001                 	; Otherwise fallback (rare path)
    STA $1C                    	; Store fallback action

change_language_down:
    LDA $1C                    	; Load processed input flags
    TSB $1CB0                  	; Merge into the acknowledged input
    DEC $1C83                  	; Decrement debounce counter
    BNE return_down            	; If still active → exit

    LDA #$0006                 	; SFX for language confirmation toggle
    JSR $A3E9                  	; Play the SFX

    TYX                        	; Move cursor index Y → X
    STZ $38,X                  	; Clear menu entry at index X

    LDA $06D6                  	; Load current language flag
    LDA #$0001                 	; Force french language (FRENCH NOW)
    STA $06D6                  	; Store language flag

    SEP #$20                   	; A = 8-bit mode
    STA $B06008                	; Write new language to hardware
    REP #$20                   	; A = 16-bit mode

    JSR $9E09                  	; Refresh menu to apply new language

return_down:
    RTS							; Return

;--------------------------------------------
; Scroll wheel secuence
;--------------------------------------------
org $809C77

move_wheel_up:
    SEP #$20                  	; 8-bit mode
    LDA $01,X                 	; Load wheel tile index
    DEC                       	; Move upward (index - 1)
    CMP #$B8                  	; If passed minimum
    BCS continue_moving_up      ; 
    LDA $1A                   	; Otherwise wrap using $1A
continue_moving_up:
    STA $01,X                 	; Store updated tile index
    INX                       	; Advance to next wheel entry
    INX
    INX
    INX
    REP #$20                  	; 16-bit mode
    RTS

move_wheel_down:
    SEP #$20                  	; 8-bit mode
    LDA $01,X                 	; Load wheel tile index
    INC                       	; Move downward (index + 1)
    CMP $1A                   	; If passed maximun
    BCC continue_moving_down    ; 
    LDA #$B7                  	; Otherwise wrap using $B7  
continue_moving_down:
    STA $01,X                 	; Store updated tile index
    INX                       	; Advance to next entry
    INX
    INX
    INX
    REP #$20                  	; 16-bit mode
    RTS

;--------------------------------------------
; This section updates the menu strings
; Options Need to be duplicated because wheel 
; have 3 string at the front (visual reason)
;--------------------------------------------
org $80A113
load_main_menu_options:
	LDA $0432					; Load current sound config
	STA $1A						; Write to WRAM $1A
	JSR read_sound_options		; Read menu sound option ptr(STEREO)
	LDA #$BC70					; Load sound option position Y,X
	JSR write_to_cpu			; Write ptr and pos to $1C3F + Y
	JSR read_sound_options		; Read menu sound option ptr(MONO)
	LDA #$C470					; Load sound option position Y,X
	JSR write_to_cpu			; Write ptr and pos to $1C3F + Y
	JSR read_sound_options		; Read menu sound option ptr(STEREO)
	LDA #$CC70					; Load sound option position Y,X
	JSR write_to_cpu			; Write ptr and pos to $1C3F + Y
	JSR read_sound_options		; Read menu sound option ptr(MONO)
	LDA #$D470					; Load sound option position Y,X
	JSR write_to_cpu			; Write ptr and pos to $1C3F + Y
	
	LDA $06D6					; Load current language
	STA $1A						; Write to WRAM $1A
	JSR read_language_options	; Read menu language option ptr(FRANCAIS)
	LDA #$BCB0					; Load language option position Y,X
	JSR write_to_cpu			; Write ptr and pos to $1C3F + Y
	JSR read_language_options	; Read menu language option ptr(ENGLISH)
	LDA #$C4B0					; Load language option position Y,X
	JSR write_to_cpu			; Write ptr and pos to $1C3F + Y
	JSR read_language_options	; Read menu language option ptr(FRANCAIS)
	LDA #$CCB0					; Load language option position Y,X
	JSR write_to_cpu			; Write ptr and pos to $1C3F + Y
	JSR read_language_options	; Read menu language option ptr(ENGLISH)
	LDA #$D4B0					; Load language option position Y,X
	JSR write_to_cpu			; Write ptr and pos to $1C3F + Y
	RTS							; Return to routine
	
read_sound_options:
	LDA $1A						; Load sound config into A
	INC $1A						; Increment sound config for the next read
	AND #$0001					; Mask 00=STEREO, 01=MONO
	ASL							; Multiply by 2
	TAY							; Y = index
	LDX ptr_sound_options,Y		; Load pointer from table
	RTS
	
ptr_sound_options:
	db $65,$C3,$5F,$C3

read_language_options:
	LDA $1A						; Load language setting into A
	INC $1A						; Increment for the next read
	LDA #$0000					; Mask 00=FRANCAIS, 01=ENGLISH ---> FORCE FRENCH NOW
	ASL							; Multiply by 2
	TAY							; Y = index
	LDX ptr_language_options,Y	; Load pointer from table
	RTS

ptr_language_options:
	db $49,$C3,$58,$C3

;--------------------------------------------------
; For some reason at select players language wheel 
; update with this routine so need to be fixed too.
;--------------------------------------------------
org $80A324
reload_language_wheel:
	PHX
	PHY
	LDA ptr_language_options_at_select,X
	TAX
	JSR $A41D
	PLA
	CLC
	ADC #$0040
	TAY
	PLX
	INX
	INX
	RTS
ptr_language_options_at_select:
	db $49,$C3,$49,$C3,$49,$C3,$49,$C3

;------------------------------------------------
; This section writes menu configuration data  
; into a buffer that the CPU reads
;------------------------------------------------
org $80A453

write_to_cpu:
	LDY $1C3F					; Load current CPU write offset
	STA $0000,Y					; Write position Y,X to CPU
	INY							; Advance offset by 2 bytes
	INY
	TXA							; Transfer pointer value from X to A
	STA $0000,Y					; Write pointer to CPU
	INY							; Advance offset by 2 bytes
	INY
	STY $1C3F					; Store updated offset
	RTS							; Return


