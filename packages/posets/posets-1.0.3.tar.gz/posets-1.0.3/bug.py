import posets
P=posets.Poset(
	relations={0:["a","c"],"a":["b"],"b":[1],"c":[1]},
	elements=[0,"a","b","c",1]
	)

print('Original triangular array')
print(P.zeta)
print('1 2 3 subarray')
print(P.zeta.subarray((1,2,3)))
print('1 3 2 subarray')
print(P.zeta.subarray((1,3,2)))
