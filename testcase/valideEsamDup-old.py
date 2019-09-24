#encoding:utf-8
'''
Created on 2014-12-10
检查ESAM重复的脚本
@author: user
'''

POOL_FILE = "existedPool.txt"
TO_VALIDATE_FILE = "toValidate.txt"
OUTPUT_FILE = "output.txt"

def writeToOutput(esam):
    print 'find duplidated:',esam
    f = open(OUTPUT_FILE,'a')
    f.write("%s\n"%esam)
    f.close()

print 'reading local pool...'

esamPool = set()

localPoolFile = open(POOL_FILE)
for line in localPoolFile.readlines():
    esamPool.add(line.strip())
localPoolFile.close()

print 'begin to compare...'

toValidateFile = open(TO_VALIDATE_FILE)

for line in toValidateFile.readlines():
    ls = line.strip()
    if ls in esamPool:
        writeToOutput(ls)
print 'finish'
raw_input()


    
    
    
    
    
