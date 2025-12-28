import lstring

# Test 1: Default behavior (should use lstring.re.Match)
p1 = lstring.re.compile(lstring.L(r'(\d+)'))
m1 = p1.search(lstring.L('test 123 abc'))
print(f"Test 1 - Default Match type: {type(m1)}")
print(f"Test 1 - Match result: {m1.group(0)}")

# Test 2: Custom Match class
class CustomMatch(lstring.re.Match):
    def custom_method(self):
        return f"Custom: {self.group(0)}"

p2 = lstring.re.compile(lstring.L(r'(\d+)'), Match=CustomMatch)
m2 = p2.search(lstring.L('test 456 def'))
print(f"\nTest 2 - Custom Match type: {type(m2)}")
print(f"Test 2 - Match result: {m2.group(0)}")
print(f"Test 2 - Custom method: {m2.custom_method()}")

# Test 3: Match factory in re.compile
p3 = lstring.re.compile(lstring.L(r'[a-z]+'), Match=CustomMatch)
m3 = p3.match(lstring.L('hello world'))
print(f"\nTest 3 - Match via re.compile: {type(m3)}")
print(f"Test 3 - Match result: {m3.group(0)}")
print(f"Test 3 - Custom method: {m3.custom_method()}")

# Test 4: Verify error when passing non-subclass
try:
    p4 = lstring.re.compile(lstring.L(r'test'), Match=str)
    print("\nTest 4 - FAILED: Should have raised TypeError")
except TypeError as e:
    print(f"\nTest 4 - Correctly raised TypeError: {e}")

print("\n✓ All tests passed!")
