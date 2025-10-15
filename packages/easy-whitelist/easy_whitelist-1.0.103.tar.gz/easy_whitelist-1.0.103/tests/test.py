
for i in range(10):
    with open("/tmp/aa", "a+") as f:
        print(f"hello", file=f)
