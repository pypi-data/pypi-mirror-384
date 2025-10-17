import os
import stat

def auto_create(var):
    if not os.path.exists(var):
        os.makedirs(var)
    
def lock_file(file):
    if os.path.exists(file):
        os.chmod(file, stat.S_IRUSR)


def is_int(number):
    try:
        int(number)
        return True
    except:
        return False

def is_num(number):
    if is_int(number) == True:
        return True
    try:
        float(number)
        return True
    except:
        return False

def change_to_correct_data_type(data=str):
    if data == 'True':
        return True
    elif data == 'False':
        return False
    elif data == 'None':
        return None
    if is_num(data) == False:
        return data
    if '.' in str(data):
        return float(data)
    return int(data)

def stringify_list(list_to_save=list, splice_sign=str):
    string_to_retrun = ''
    if not len(splice_sign) == 1:
        raise ValueError('splice sign must be one character')
    for i in list_to_save:
        stri = str(i)
        if not i == list_to_save[0]:
            string_to_retrun += splice_sign

        if splice_sign in stri:
            string_to_retrun += stri.replace(splice_sign, f'{splice_sign * 2}')
        else:
            string_to_retrun += str(stri)
    return string_to_retrun

#ai doesn't fucking understand de_stringify_list works what the fuck is wrong with them
#actually, i don't fucking know how this works either
def de_stringify_list(fileList=list, splice_sign=str):
    strippedList = []
    stripVar = ''
    if not len(splice_sign) == 1:
        raise ValueError('splice sign must be one character')
    splice_sign_num = 0

    for i in fileList:
        if i == splice_sign:
            splice_sign_num += 1

        if splice_sign_num == 2:
            stripVar += splice_sign
            splice_sign_num = 0
        #if splice_sign is 1 and i isn't a splice sign, that means it needs to be parced
        elif splice_sign_num == 1 and not i == splice_sign:
            strippedList.append(stripVar)
            stripVar = ''
            stripVar += str(i)
            splice_sign_num = 0
        #if splice_sign_num is 1(past string) and the next string(i) is a splice sign, this means the splice sign was just an escape sequence
        elif i == splice_sign:
            pass
        else:
            stripVar += str(i)

    strippedList.append(stripVar)

    correctList = []
    for i in strippedList:
        correct_data = change_to_correct_data_type(i)
        correctList.append(correct_data)     
    return correctList

class content:
    def __init__(self, folderPath, *fileName, encode='utf-8', lock=False):
        if not folderPath == None and not folderPath == '':
            auto_create(folderPath)
            folderPath += '/'
        else:
            folderPath = ''
        self.fpath = folderPath
        self.encoder = encode
        self.lock = lock
        if not len(fileName) == 0:
            self.file = f'{folderPath}{fileName[0]}'
        if len(fileName) == 0:
            pass
        elif os.path.exists(self.file):
            os.chmod(self.file, stat.S_IWUSR)
        #else:
        #    with open(self.file, 'a') as o:
        #        pass
        self.fileContent = []

    def fetch(self, no_strip=False):
        iList = []
        if not os.path.exists(self.file):
            return []
        with open(self.file, 'r', encoding=self.encoder) as o:
            file_lines = (o.readlines())
        if no_strip == True:
            iList = file_lines
        else:
            for i in file_lines:
                iStrip = i.strip()
                iList.append(iStrip)
        self.fileContent = file_lines
        return iList



    def save(self, save, overwrite=False, sameLN=False, lock=False):
        if len(save) == 0:
            saveString = ''
        else:
            saveString = save

        if overwrite == True:
            how_to_open = 'w'
        elif overwrite == False:
            how_to_open = 'a'
        else:
            raise AttributeError("'overwrite' can only handle boolian")
        
        if self.lock != lock:
            self.lock = lock

        if os.path.exists(self.file):
            os.chmod(self.file, stat.S_IWUSR)
        with open(self.file, how_to_open, encoding=self.encoder, errors='replace') as o:
            if self.fileContent == []:
                pass
            elif sameLN == True:
                pass
            elif not '\n' in self.fileContent[len(self.fileContent)-1]:
                o.write('\n')
            o.write(str(saveString))
            if sameLN == False:
                o.write('\n')
        if lock == True:
            lock_file(self.file)
        elif lock == False:
            os.chmod(self.file, stat.S_IWUSR)

    def change(self, thingToChangeIndex, changedThing, lock=False):
        self.fileContent[thingToChangeIndex] = f'{changedThing}\n'
        if self.lock != lock:
            self.lock = lock
        saveFileContent = ''
        for i in self.fileContent:
            saveFileContent += i
        self.save(saveFileContent, overwrite=True, lock=lock, sameLN=True)

    def delete(self, thingToDeleteIndex, lock=False):
        if self.lock != lock:
            self.lock = lock
        del self.fileContent[thingToDeleteIndex]
        for i in self.fileContent:
            saveFileContent += i
        self.save(saveFileContent, overwrite=True, lock=lock, sameLN=True)

    def delete_bulk(self, thingToDeleteIndexList, lock=False):
        if self.lock != lock:
            self.lock = lock
        for index in thingToDeleteIndexList:
            del self.fileContent[index]
        os.chmod(self.file, stat.S_IWUSR)
        for i in self.fileContent:
            saveFileContent += i
        self.save(saveFileContent, overwrite=True, lock=lock, sameLN=True)
            
    def delete_file(self):
        if os.path.exists(self.file):
            os.chmod(self.file, stat.S_IWUSR)
            os.remove(self.file)


if __name__ == '__main__':
    #string = stringify_list(['list', 'to:save', 'to:list'], ':')
    #input(string)
    #input(de_stringify_list('list:to::save:to::list', ':'))

    ftest = content('test','whyNotWorking.txt')
    ftest.fetch()
    #ftest.save('涙')
    #print(ftest.fetch())
    ftest.change(0, 'one')
    print(ftest.fetch())

    #ftest.change(0, 'true')