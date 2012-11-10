l = [1,2,3,4,5]
l2 = [1,2,3,4,5,6]

# i want [1,3,5]
l3 = filter(lambda x: x%2 == 1, l2)


b = [n1*n2 for n1 in l for n2 in l2 if n1 != 3]

b = []
for n1 in l:
	for n2 in l2:
		if n1 != 3:
			b.append(n1*n2)


options = {
			'one' : func1, #@UndefinedVariable
			'two' : func2 #@UndefinedVariable
			}

options['one']('hi')
# --> hi

options['two']('hi')
# --> hi hi

def func1(arg):
	print arg


def func2(arg):
	print arg+' '+arg


