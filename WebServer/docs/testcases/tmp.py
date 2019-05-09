f=open('dir')
ans=''
for l in f.readlines():
    ans+=l[9:12]
    ans+=' '
print(ans)
