def func1(x):
    if x == 0:
        def func2():
            print("1")
    else:
        def func2():
            print("2")
    func2()
func1(1)