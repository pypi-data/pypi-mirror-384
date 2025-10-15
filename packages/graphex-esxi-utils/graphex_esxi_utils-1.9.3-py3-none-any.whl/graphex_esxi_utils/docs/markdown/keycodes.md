# USB Key Code Reference

This page describes how to provide keyboard input to a VM object using this plugin. First, the available nodes for providing keyboard input of any kind is shown. Second, the table of available keys and hexidecimal codes is shown [at the bottom of this page](#conversion-table). 

## Available Keyboard Emulation Nodes

Keyboard functionality can be found under the category tree: 'ESXi' -> 'Virtual Machine' -> 'Keyboard':
![the keyboard category](images/keyboard_category.png)

If you just want to write text to the screen and have GraphEx automatically handle all of the key conversions for you, use the 'ESXi VM Keyboard Write' node. Simply type the text (String) into the node in the case that you want it to be written to the VM in. Check the 'Enter?' boolean checkbox (set it to True) if you want the node to press the enter key for you after writing the string:
![the keyboard write node](images/keyboard_write.png)

In the table [below](#conversion-table), the column for 'Corresponding Key Name' represents the valid strings that you can provide to the 'ESXi VM Press Key' node:
![the keyboard press key node](images/keyboard_press_key.png)

Likewise, the column for 'Hexidecimal' code in the table [below](#conversion-table) represents the valid strings that you can provide to the 'ESXi VM Send USB Code' node:
![the keyboard send usb code node](images/keyboard_send_code.png)

When you send individual keys via hexidecimal code, you can also send 'modifier' keys alongside the desired key in order to change the default behavior of the key. A good example of this is sending the code for the letter 'a' alongside the code for the key 'shift': which produces the output 'A' on the VM. Keep in mind that their are modifiers for both shift keys on a standard keyboard:
![keyboard modifiers](images/keyboard_send_code_mod.png)

If you would like to convert a value in a row between the code and key name, you can use either of the two convience nodes provided. The 'ESXi VM Get USB Scan Code' will throw an error if the 'Key Name' doesn't exist in the table below. This is a way of quickly 'brute force' checking if you have the proper name of a key that you are trying to press.
![nodes to convert between scan codes and keyboard presses](images/keyboard_conversion.png)

## Conversion Table

This table shows the available keys that you can use via the 'ESXi VM Press Key' node and the available hexidecimal codes you can provide to the 'ESXi VM Send USB Code' node. The names and numbers of the keys are standardized, I do not know what all of them represent on an actual physical keyboard. I have omitted some of the ones I have tested that do not work or do not make sense for a user to provide as input.

Remember that these represent *IDENTIFIERS* (IDs) for each individual key on the keyboard (**NOT THE CHARACTERS**). For example, if you wanted to produce the character: '#', you would have to provide the modifier 'LeftShift' and the hex code: '0x20'. Remember that you could also use the conversion node to get the hex code (you don't have to look it up if you know you need the key named: '3').

| Hexidecimal Code | Corresponding Key Name |
| :-----: | :-----: |
| 0x04 | A | 
| 0x05 | B | 
| 0x06 | C | 
| 0x07 | D | 
| 0x08 | E | 
| 0x09 | F | 
| 0x0a | G | 
| 0x0b | H | 
| 0x0c | I | 
| 0x0d | J | 
| 0x0e | K | 
| 0x0f | L | 
| 0x10 | M | 
| 0x11 | N | 
| 0x12 | O | 
| 0x13 | P | 
| 0x14 | Q | 
| 0x15 | R | 
| 0x16 | S | 
| 0x17 | T | 
| 0x18 | U | 
| 0x19 | V | 
| 0x1a | W | 
| 0x1b | X | 
| 0x1c | Y | 
| 0x1d | Z |
| 0x1e | 1 | 
| 0x1f | 2 | 
| 0x20 | 3 | 
| 0x21 | 4 | 
| 0x22 | 5 | 
| 0x23 | 6 | 
| 0x24 | 7 | 
| 0x25 | 8 | 
| 0x26 | 9 | 
| 0x27 | 0 |
| 0x28 | ENTER | 
| 0x29 | ESC | 
| 0x2a | BACKSPACE | 
| 0x2b | TAB | 
| 0x2c | SPACE | 
| 0x2d | - | 
| 0x2e | = | 
| 0x2f | [ | 
| 0x30 | ] | 
| 0x31 | \ | 
| 0x33 | ; | 
| 0x34 | ' | 
| 0x35 | ` | 
| 0x36 | , | 
| 0x37 | . | 
| 0x38 | / | 
| 0x39 | CAPSLOCK |
| 0x3a | F1 | 
| 0x3b | F2 | 
| 0x3c | F3 | 
| 0x3d | F4 | 
| 0x3e | F5 | 
| 0x3f | F6 | 
| 0x40 | F7 | 
| 0x41 | F8 | 
| 0x42 | F9 | 
| 0x43 | F10 | 
| 0x44 | F11 | 
| 0x45 | F12 |
| 0x46 | SYSRQ | 
| 0x47 | SCROLLLOCK | 
| 0x48 | PAUSE | 
| 0x49 | INSERT | 
| 0x4a | HOME | 
| 0x4b | PAGEUP | 
| 0x4c | DELETE | 
| 0x4d | END | 
| 0x4e | PAGEDOWN | 
| 0x4f | RIGHT | 
| 0x50 | LEFT | 
| 0x51 | DOWN | 
| 0x52 | UP |
| 0x53 | NUMLOCK | 
| 0x54 | KPSLASH | 
| 0x55 | KPASTERISK | 
| 0x56 | KPMINUS | 
| 0x57 | KPPLUS | 
| 0x58 | KPENTER | 
| 0x59 | KP1 | 
| 0x5a | KP2 | 
| 0x5b | KP3 | 
| 0x5c | KP4 | 
| 0x5d | KP5 | 
| 0x5e | KP6 | 
| 0x5f | KP7 | 
| 0x60 | KP8 | 
| 0x61 | KP9 | 
| 0x62 | KP0 | 
| 0x63 | KPDOT | 
| 0x64 | 102ND | 
| 0x65 | COMPOSE | 
| 0x66 | POWER | 
| 0x67 | KPEQUAL |
| 0x68 | F13 | 
| 0x69 | F14 | 
| 0x6a | F15 | 
| 0x6b | F16 | 
| 0x6c | F17 | 
| 0x6d | F18 | 
| 0x6e | F19 | 
| 0x6f | F20 | 
| 0x70 | F21 | 
| 0x71 | F22 | 
| 0x72 | F23 | 
| 0x73 | F24 |
| 0x74 | OPEN | 
| 0x75 | HELP | 
| 0x76 | PROPS | 
| 0x77 | FRONT | 
| 0x78 | STOP | 
| 0x79 | AGAIN | 
| 0x7a | UNDO | 
| 0x7b | CUT | 
| 0x7c | COPY | 
| 0x7d | PASTE | 
| 0x7e | FIND | 
| 0x7f | MUTE | 
| 0x80 | VOLUMEUP | 
| 0x81 | VOLUMEDOWN |
| 0x85 | KPCOMMA |
| 0x87 | RO | 
| 0x88 | KATAKANAHIRAGANA | 
| 0x89 | YEN | 
| 0x8a | HENKAN | 
| 0x8b | MUHENKAN | 
| 0x8c | KPJPCOMMA |
| 0x90 | HANGEUL | 
| 0x91 | HANJA | 
| 0x92 | KATAKANA | 
| 0x93 | HIRAGANA | 
| 0x94 | ZENKAKUHANKAKU |
| 0xb6 | KPLEFTPAREN | 
| 0xb7 | KPRIGHTPAREN |
| 0xe0 | LEFTCTRL | 
| 0xe1 | LEFTSHIFT | 
| 0xe2 | LEFTALT | 
| 0xe3 | LEFTMETA | 
| 0xe4 | RIGHTCTRL | 
| 0xe5 | RIGHTSHIFT | 
| 0xe6 | RIGHTALT | 
| 0xe7 | RIGHTMETA |
| 0xe8 | MEDIA_PLAYPAUSE |
| 0xe9 | MEDIA_STOPCD |
| 0xea | MEDIA_PREVIOUSSONG |
| 0xeb | MEDIA_NEXTSONG |
| 0xec | MEDIA_EJECTCD |
| 0xed | MEDIA_VOLUMEUP |
| 0xee | MEDIA_VOLUMEDOWN |
| 0xef | MEDIA_MUTE |
| 0xf0 | MEDIA_WWW |
| 0xf1 | MEDIA_BACK |
| 0xf2 | MEDIA_FORWARD |
| 0xf3 | MEDIA_STOP |
| 0xf4 | MEDIA_FIND |
| 0xf5 | MEDIA_SCROLLUP |
| 0xf6 | MEDIA_SCROLLDOWN |
| 0xf7 | MEDIA_EDIT |
| 0xf8 | MEDIA_SLEEP |
| 0xf9 | MEDIA_COFFEE |
| 0xfa | MEDIA_REFRESH |
| 0xfb | MEDIA_CALC |
