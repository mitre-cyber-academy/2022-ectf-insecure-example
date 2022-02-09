# Instructions for Getting the Debugger Flag

This tutorial will show you how to use the GDB debugger to walk through and
interract with a running SAFFIRe bootloader.

## 0. Pull the GDB Challenge Bootloader Image

**Note: You only need to do this once on your server**

You will need the bootloader Docker image from Dockerhub to complete these
instructions. Pull the image and create a new tag for it to be compatible with
`tools/run_saffire.py`:

```bash
docker pull ectf/bootloader:gdb
docker docker image tag ectf/bootloader:gdb gdb-challenge/bootloader
```


## 1. Launch Device in Debug Mode

Instead of the typical `launch-bootloader` command, we will use
`launch-bootloader-gdb`, which attaches a GDB debugger to the SAFFIRe
bootloader.

For this tutorial, you may simply run the following command from the root
directory of this repository (it will pull from pre-built containers we have
pushed to Docker Hub). We recommend you use the same `uart-sock` value you have
been using for your personal development:

```bash
python3 tools/run_saffire.py launch-bootloader-gdb --emulated \
    --sysname gdb-challenge \
    --sock-root socks/ \
    --uart-sock 1337
```

Once the bootloader container launches, connect GDB to the emulator with:

```bash
gdb-multiarch gdb-challenge-bootloader.elf.deleteme \
    -ex 'target remote socks/gdb.sock'
```

Finally, the GDB challenge bootloader will print a flag to the UART socket if
you succeed, so you'll need a way to read from the socket to get the flag. Open
a second terminal session on the server and run:

```bash
telnet localhost 1337
```

**Note: The `1337` should match the `uart-sock` argument you used above!**.


## 2. Getting Your Bearings

When the device finishes starting up, you should see output along the lines of:

```
0x00000448 in ?? ()
(gdb)
```

You are now using GDB. QEMU has started emulating the avionic device, but
stopped in the MITRE bootstrapper at address 0x448.

To get to the start of the SAFFIRe bootloader, set a breakpoint at the
`Bootloader_Startup` function and run to it (we'll explain this more later!):

```
(gdb) b Bootloader_Startup
Breakpoint 1 at 0x5812
```

```
(gdb) c
Continuing.

Breakpoint 1, 0x00005812 in Bootloader_Startup ()
```

Now you are stopped at the beginning of the SAFFIRe bootloader.

Let's view the current register values with `info registers`:
```
(gdb) info registers
r0             0x1                 1
r1             0x40005528          1073763624
r2             0x4000d030          1073795120
r3             0x20000000          536870912
r4             0x0                 0
r5             0x0                 0
r6             0x0                 0
r7             0x20000fd0          536874960
r8             0x0                 0
r9             0x0                 0
r10            0x0                 0
r11            0x0                 0
r12            0x0                 0
sp             0x20000000          0x20000000 <pui32Stack>
lr             0x43b               1083
pc             0x5812              0x5812 <Bootloader_Startup+18>
xpsr           0x21000000          553648128
fpscr          0x0                 0
fpsid          0x0                 0
fpexc          0x0                 0
```

We can also view values in memory with `x` specified by address or symbol:
```
(gdb) x 0x5800
0x5800 <Bootloader_Startup>:    0xb082b580
(gdb) x Bootloader_Startup
0x5800 <Bootloader_Startup>:    0xb082b580
```

**Write down the raw value of the instruction in memory at uart_init for later
as value1**


## Setting a Breakpoint
Now that we have control of the system, let's continue to main. To do that,
we must first set a breakpoint at main using `break` or `b` for shorthand:

```
(gdb) b main
Breakpoint 2 at 0x5c5e
```

Let's also set up GDB so it prints out the current instruction when it hits a
breakpoint:

```
(gdb) set disassemble-next-line on
```

Now continue running the process with `continue` or `c` for shorthand:

```
(gdb) c
Continuing.

Breakpoint 2, 0x00005c5e in main ()
=> 0x00005c5e <main+6>: ff f7 05 fe     bl      0x586c <uart_init>
```

Note, GDB did not actually break at main, but rather at an adddress 88 bytes
into main (seen by `<main+6>`. This can be confirmed by printing the address
of `main` with `print` or `p` for shorthand:

```
(gdb) p main
$1 = {<text variable, no debug info>} 0x5c58 <main>
```

Why is that? It turns out GDB is trying to be smart under the hood. It skips
over the function prologue that mainly handles cleaning up the stack before the
main body of the function. If you did not want that and instead want to break at
the exact start of a function, we can manually break at an address by calling
`break` with a number preceded by `*`. Or, we can dereference (`print`) the
function address and use the resulting GDB variable to break. Let's try this
second technique with `uart_init`:

```
(gdb) p uart_init
$2 = {<text variable, no debug info>} 0x586c <uart_init>
(gdb) b *$2
Breakpoint 3 at 0x586c
(gdb) c
Continuing.

Breakpoint 3, 0x0000586c in uart_init ()
=> 0x0000586c <uart_init+0>:    80 b5   push    {r7, lr}
```

**Inspect the registers and write down the value in `sp` as value2**


## 3. Stepping Through Code
Let's skip ahead to a function called `do_dumb_math` (without skipping the
function prologue):

```
(gdb) p do_dumb_math
$3 = {<text variable, no debug info>} 0x5910 <do_dumb_math>
(gdb) b *$3
Breakpoint 4 at 0x5910
(gdb) c
Continuing.

Breakpoint 4, 0x00005910 in do_dumb_math ()
=> 0x00005910 <do_dumb_math+0>: 80 b4   push    {r7}
```

Now, let's inspect the disassembly of this function with `disas`:

```
(gdb) disas do_dumb_math
Dump of assembler code for function do_dumb_math:
=> 0x00005910 <+0>:     push    {r7}
   0x00005912 <+2>:     sub     sp, #20
   0x00005914 <+4>:     add     r7, sp, #0
   0x00005916 <+6>:     str     r0, [r7, #12]
   0x00005918 <+8>:     str     r1, [r7, #8]
   0x0000591a <+10>:    str     r2, [r7, #4]
   0x0000591c <+12>:    str     r3, [r7, #0]
   0x0000591e <+14>:    ldr     r2, [r7, #12]
   0x00005920 <+16>:    ldr     r3, [r7, #8]
   0x00005922 <+18>:    add     r3, r2
   0x00005924 <+20>:    ldr     r1, [r7, #8]
   0x00005926 <+22>:    ldr     r2, [r7, #4]
   0x00005928 <+24>:    sdiv    r2, r1, r2
   0x0000592c <+28>:    mul.w   r2, r2, r3
   0x00005930 <+32>:    ldr     r3, [r7, #0]
   0x00005932 <+34>:    ldr     r1, [r7, #12]
   0x00005934 <+36>:    sdiv    r1, r3, r1
   0x00005938 <+40>:    ldr     r0, [r7, #12]
   0x0000593a <+42>:    mul.w   r1, r0, r1
   0x0000593e <+46>:    subs    r3, r3, r1
   0x00005940 <+48>:    mul.w   r3, r3, r2
   0x00005944 <+52>:    ldr     r1, [r7, #12]
   0x00005946 <+54>:    ldr     r2, [r7, #8]
   0x00005948 <+56>:    eors    r1, r2
   0x0000594a <+58>:    ldr     r2, [r7, #0]
   0x0000594c <+60>:    add     r2, r1
   0x0000594e <+62>:    sdiv    r1, r3, r2
   0x00005952 <+66>:    mul.w   r2, r2, r1
   0x00005956 <+70>:    subs    r3, r3, r2
   0x00005958 <+72>:    mov     r0, r3
   0x0000595a <+74>:    adds    r7, #20
   0x0000595c <+76>:    mov     sp, r7
   0x0000595e <+78>:    pop     {r7}
   0x00005960 <+80>:    bx      lr
End of assembler dump.
```

Instead of using breakpoints, we can instead step through this function
instruction by instruction using `si` for step instruction:

```
(gdb) si
0x00005912 in do_dumb_math ()
=> 0x00005912 <do_dumb_math+2>: 85 b0   sub     sp, #20
(gdb) si
0x00005914 in do_dumb_math ()
=> 0x00005914 <do_dumb_math+4>: 00 af   add     r7, sp, #0
(gdb) si
0x00005916 in do_dumb_math ()
=> 0x00005916 <do_dumb_math+6>: f8 60   str     r0, [r7, #12]
```

You can see that we are stepping through the instructions of the function.
If you run `disas` again, you will see our position has changed:

```
(gdb) disas
Dump of assembler code for function do_dumb_math:
   0x00005910 <+0>:     push    {r7}
   0x00005912 <+2>:     sub     sp, #20
   0x00005914 <+4>:     add     r7, sp, #0
=> 0x00005916 <+6>:     str     r0, [r7, #12]
   0x00005918 <+8>:     str     r1, [r7, #8]
   0x0000591a <+10>:    str     r2, [r7, #4]
   0x0000591c <+12>:    str     r3, [r7, #0]
   0x0000591e <+14>:    ldr     r2, [r7, #12]
   0x00005920 <+16>:    ldr     r3, [r7, #8]
   0x00005922 <+18>:    add     r3, r2
   0x00005924 <+20>:    ldr     r1, [r7, #8]
   0x00005926 <+22>:    ldr     r2, [r7, #4]
   0x00005928 <+24>:    sdiv    r2, r1, r2
   0x0000592c <+28>:    mul.w   r2, r2, r3
   0x00005930 <+32>:    ldr     r3, [r7, #0]
   0x00005932 <+34>:    ldr     r1, [r7, #12]
   0x00005934 <+36>:    sdiv    r1, r3, r1
   0x00005938 <+40>:    ldr     r0, [r7, #12]
   0x0000593a <+42>:    mul.w   r1, r0, r1
   0x0000593e <+46>:    subs    r3, r3, r1
   0x00005940 <+48>:    mul.w   r3, r3, r2
   0x00005944 <+52>:    ldr     r1, [r7, #12]
   0x00005946 <+54>:    ldr     r2, [r7, #8]
   0x00005948 <+56>:    eors    r1, r2
   0x0000594a <+58>:    ldr     r2, [r7, #0]
   0x0000594c <+60>:    add     r2, r1
   0x0000594e <+62>:    sdiv    r1, r3, r2
   0x00005952 <+66>:    mul.w   r2, r2, r1
   0x00005956 <+70>:    subs    r3, r3, r2
   0x00005958 <+72>:    mov     r0, r3
   0x0000595a <+74>:    adds    r7, #20
   0x0000595c <+76>:    mov     sp, r7
   0x0000595e <+78>:    pop     {r7}
   0x00005960 <+80>:    bx      lr
End of assembler dump.
```

### Setting a Watchpoint

Instead of manually stepping through individual instructions, we can also
automatically run through code and break when a variable, register, or value in
memory changes by setting a watchpoint. Let's set a watchpoint on register `r3`
and continue running:

```
(gdb) watch $r3
Watchpoint 5: $r3
```

By default, GDB will just print the old and new value in signed integer format,
so let's tell GDB to inspect register `r3` when it breaks on the
watchpoint in order to automatically see the hexadecimal representation:

```
(gdb) commands
Type commands for breakpoint(s) 5, one per line.
End with a line saying just "end".
>info registers r3
>end
```

Now, we can continue running until `r3` changes:

```
(gdb) c
Continuing.

Watchpoint 5: $r3

Old value = -1057017071
New value = -17958194
0x00005922 in do_dumb_math ()
=> 0x00005922 <do_dumb_math+18>:        13 44   add     r3, r2
r3             0xfeedface          -17958194
```

Notice that GDB prints out the old and new values (in signed integer format),
the current break location and instruction, and then the `info registers`
printout of `r3`.

**Continue running through the `do_dumb_math` function until the value of r3
starts with 0xe and record that value as value3**

When we're done watching `r3`, we can delete the watchpoint. First, view the
existing breakpoints and watchpoints with `info break` or `i b` for shorthand:

```
(gdb) info break
Num     Type           Disp Enb Address    What
1       breakpoint     keep y   0x00005812 <Bootloader_Startup+18>
        breakpoint already hit 1 time
2       breakpoint     keep y   0x00005c5e <main+6>
        breakpoint already hit 1 time
3       breakpoint     keep y   0x0000586c <uart_init>
        breakpoint already hit 1 time
4       breakpoint     keep y   0x00005910 <do_dumb_math>
        breakpoint already hit 1 time
5       watchpoint     keep y              $r3
```

The break number of the `r3` watchpoint is `5`, so we will delete that break
number, and check the break numbers again to make sure we successfully removed
the watchpoint:

```
(gdb) delete 5
(gdb) i b
Num     Type           Disp Enb Address    What
1       breakpoint     keep y   0x00005812 <Bootloader_Startup+18>
        breakpoint already hit 1 time
2       breakpoint     keep y   0x00005c5e <main+6>
        breakpoint already hit 1 time
3       breakpoint     keep y   0x0000586c <uart_init>
        breakpoint already hit 1 time
4       breakpoint     keep y   0x00005910 <do_dumb_math>
        breakpoint already hit 1 time
```

### Writing to Registers and Memory
Set a breakpoint at 0x5960 (the end of `do_dumb_math` and continue there:

```
(gdb) b *0x5960
Breakpoint 6 at 0x5960
(gdb) c
Continuing.

Breakpoint 6, 0x00005960 in do_dumb_math ()
=> 0x00005960 <do_dumb_math+80>:        70 47   bx      lr
```

With the `set` command we can now modify registers (make sure to reset them):

```
(gdb) info registers r0
r0             0x0                 0
(gdb) set $r0=111
(gdb) info registers r0
r0             0x6f                111
(gdb) set $r0=0
```

And memory:

```
(gdb) x 0x20000000
0x20000000 <pui32Stack>:        0x00000000
(gdb) set *0x20000000=0x111
(gdb) x 0x20000000
0x20000000 <pui32Stack>:        0x00000111
(gdb) set *0x20000000=0
```

## Capturing the flag
With what you've learned, set a breakpoint at the first instruction of the
`check_flag` function and continue up to there.

`check_flag` has five arguments; let's check them out. The ARM calling
convention
is to place the first four arguments in registers and further arguments are
pushed to the stack.

Print the registers and then the top value on the stack to view the arguments:

```
(gdb) info registers
r0             0x11111111          286331153
r1             0x22222222          572662306
r2             0x33333333          858993459
r3             0x44444444          1145324612
r4             0x0                 0
r5             0x0                 0
r6             0x0                 0
r7             0x20001cf8          536878328
r8             0x0                 0
r9             0x0                 0
r10            0x0                 0
r11            0x0                 0
r12            0x0                 0
sp             0x20001cf0          0x20001cf0
lr             0x5c93              23699
pc             0x5b38              0x5b38 <check_flag>
xpsr           0x1000000           16777216
fpscr          0x0                 0
fpsid          0x0                 0
fpexc          0x0                 0
(gdb) x $sp
0x20001cf0:     0x55555555
```

We can see that arguments 1-4 (0x11111111, 0x22222222, 0x33333333, and
0x44444444) are in registers r0 through r3, and the top value of the stack
hold the fifth argument (0x55555555).
Now, using what you have learned, change the values of the function arguments so
that the first argument is set to `value1`, the third argument is set to
`value2`, and the fifth argument is set to `value3`.

Next, set a breakpoint at 0x5c92, which is just after the return of the flag-
dispensing function, and continue to it. Type `q` to quit GDB; **don't hit
<ctrl+c> or else it will kill the emulator**:
```
(gdb) q
A debugging session is active.

   Inferior 1 [process 1] will be detached.

Quit anyway? (y or n) y
Detaching from program: /home/ubuntu/jgrycel/2022-ectf-insecure-example/gdb-challenge-bootloader.elf.deleteme, process 1
Ending remote debugging.
```

Now, look at your terminal running the `telnet` command. If you did everything
correctly, you should see a flag, and if not, you should see an explanation of
which argument was incorrect.

Once you're done with the challenge, kill the system by running:

```bash
python3 tools/run_saffire.py kill-system --sysname gdb-challenge
````

This will also automatically end the `telnet` connection.

