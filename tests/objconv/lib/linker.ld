SECTIONS {
    . = 0x0;
    .start : {
      *(.start);
    }
    .text : {
      *(.text);
    }
}
